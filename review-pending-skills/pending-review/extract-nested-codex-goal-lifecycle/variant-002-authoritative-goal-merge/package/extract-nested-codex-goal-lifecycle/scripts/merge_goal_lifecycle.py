#!/usr/bin/env python3
"""Merge attributable transcript observations with supplied authoritative goal snapshots."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

VALID_AUTHORITY = {'active', 'blocked', 'complete'}
CONFIRMATIONS = {'confirmed', 'missing-output', 'ambiguous-correlation', 'unattributed-output',
                 'unsupported-output', 'failed-output', 'status-mismatch'}


class MergeError(ValueError):
    """Describe malformed, ambiguous, or missing lifecycle evidence."""


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def instant(value):
    if not isinstance(value, str) or re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value) is None:
        raise MergeError('timestamp must be an RFC3339 date-time with timezone')
    if value[-1] != 'Z' and (int(value[-5:-3]) > 23 or int(value[-2:]) > 59):
        raise MergeError('timestamp timezone is invalid')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)
    except ValueError as error:
        raise MergeError('timestamp calendar or time is invalid') from error


def load_object(path):
    raw = path.expanduser().read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise MergeError('expected a JSON object')
    return payload, hashlib.sha256(raw).hexdigest()


def select_authority(payload, goal_id, thread_id):
    records = payload.get('records')
    if set(payload) != {'records'} or not isinstance(records, list) or not records:
        raise MergeError('authoritative source must contain only a nonempty records array')
    matching = []
    for record in records:
        if not isinstance(record, dict) or set(record) != {'goal_id', 'thread_id', 'status', 'observed_at'}:
            raise MergeError('authoritative record fields are invalid')
        if not all(nonempty(record[k]) for k in ('goal_id', 'thread_id', 'status')) or record['status'] not in VALID_AUTHORITY:
            raise MergeError('authoritative record identity or status is invalid')
        at = instant(record['observed_at'])
        if (record['goal_id'], record['thread_id']) == (goal_id, thread_id):
            matching.append((at, record))
    if not matching:
        raise MergeError('no authoritative record for the selected goal and thread')
    matching.sort(key=lambda pair: pair[0])
    if len(matching) > 1 and matching[-1][0] == matching[-2][0]:
        raise MergeError('ambiguous latest authoritative record at the same instant')
    return matching[-1][1]


def positive_line(value):
    return type(value) is int and value > 0


def event_identity(raw, confirmation):
    identities = {key: raw.get(key) for key in ('goal_id', 'thread_id')}
    for key, value in identities.items():
        if key in raw and not nonempty(value):
            raise MergeError(f'{key} must be nonempty when supplied')
    result = raw.get('output')
    goal = result.get('goal') if isinstance(result, dict) else None
    conflict = False
    if isinstance(goal, dict):
        for key in identities:
            if key not in goal:
                continue
            if not nonempty(goal[key]):
                raise MergeError(f'output goal {key} must be nonempty')
            conflict |= identities[key] is not None and identities[key] != goal[key]
            if confirmation == 'confirmed' and identities[key] is None:
                identities[key] = goal[key]
    attribution = 'conflicting' if conflict else 'resolved-declaration' if all(identities.values()) else 'unresolved'
    return identities, attribution


def nested_confirmation(raw, status):
    confirmation = raw.get('output_confirmation')
    if not isinstance(confirmation, str) or confirmation not in CONFIRMATIONS:
        raise MergeError('nested event output_confirmation is invalid')
    output = raw.get('output')
    if confirmation == 'confirmed' and (not isinstance(output, dict) or not isinstance(output.get('goal'), dict) or output['goal'].get('status') != status):
        raise MergeError('confirmed nested event requires a consistent goal result')
    for field in ('input_line', 'output_lines'):
        value = raw.get(field)
        if field in raw and not (positive_line(value) if field == 'input_line' else isinstance(value, list) and all(positive_line(v) for v in value)):
            raise MergeError(f'{field} must contain positive integer locators')
    if 'input_offset' in raw and (type(raw['input_offset']) is not int or raw['input_offset'] < 0):
        raise MergeError('input_offset must be a nonnegative integer')
    return confirmation


def normalize_event(raw):
    if not isinstance(raw, dict) or not nonempty(raw.get('call_id')) or not positive_line(raw.get('line')):
        raise MergeError('event must have a nonempty call_id and positive integer line')
    nested = raw.get('kind') == 'nested_goal_call_site'
    if nested and not isinstance(raw.get('arguments'), dict):
        raise MergeError('nested event requires an arguments object')
    status = raw['arguments'].get('status') if nested else raw.get('status')
    if not isinstance(status, str) or status not in VALID_AUTHORITY:
        raise MergeError('event status is invalid')
    if nested:
        confirmation = nested_confirmation(raw, status)
    else:
        if type(raw.get('output_confirms')) is not bool:
            raise MergeError('normalized event output_confirms must be Boolean')
        confirmation = 'confirmed' if raw['output_confirms'] else 'unattributed-output'
    identities, attribution = event_identity(raw, confirmation)
    for key in ('timestamp', 'state_at'):
        if raw.get(key) is not None:
            instant(raw[key])
    return dict(raw, status=status, output_confirmation=confirmation,
                attribution=attribution,
                confirmation_source='extractor-result' if nested else 'caller-declared',
                **identities)


def normalize_events(payload):
    events = payload.get('events')
    if not isinstance(events, list):
        raise MergeError('transcript source must contain an events array')
    return [normalize_event(raw) for raw in events]


def merge(authority, events):
    selected, unrelated, unattributed = [], [], []
    for event in events:
        if event['attribution'] != 'resolved-declaration':
            unattributed.append(event)
        elif (event['goal_id'], event['thread_id']) != (authority['goal_id'], authority['thread_id']):
            unrelated.append(event)
        else:
            selected.append(event)
    confirmed = [e for e in selected if e['output_confirmation'] == 'confirmed']
    disagreements, historical = [], []
    for event in confirmed:
        state_at = event.get('state_at')
        observed = instant(state_at) if state_at is not None else None
        if observed == instant(authority['observed_at']) and event['status'] != authority['status']:
            disagreements.append(event)
        elif event.get('timestamp') and instant(event['timestamp']) < instant(authority['observed_at']):
            historical.append(event)
    return dict(schema_version=1, goal_id=authority['goal_id'], thread_id=authority['thread_id'],
                authoritative=authority, current_status=authority['status'],
                authority_source='caller-supplied export; source authenticity not independently verified',
                confirmed_transcript_events=confirmed, historical_transcript_events=historical,
                unconfirmed_transcript_events=[e for e in selected if e['output_confirmation'] != 'confirmed'],
                unattributed_transcript_events=unattributed, other_goal_or_thread_events=unrelated,
                disagreements=disagreements)


def display(value):
    if isinstance(value, str):
        return re.sub(re.escape(str(Path.home())) + r'(?=$|[/\s\x27\x22:,)])', '~', value)
    if isinstance(value, list):
        return [display(item) for item in value]
    if isinstance(value, dict):
        return {display(key): display(item) for key, item in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--goal-id', required=True)
    parser.add_argument('--thread-id', required=True)
    parser.add_argument('--transcript-events', type=Path, required=True)
    parser.add_argument('--authoritative', type=Path, required=True)
    args = parser.parse_args()
    try:
        if not nonempty(args.goal_id) or not nonempty(args.thread_id):
            raise MergeError('selected goal and thread identities must be nonempty')
        authority_data, authority_hash = load_object(args.authoritative)
        transcript_data, transcript_hash = load_object(args.transcript_events)
        authority = select_authority(authority_data, args.goal_id, args.thread_id)
        report = merge(authority, normalize_events(transcript_data))
        report['input_hashes'] = dict(authoritative=authority_hash, transcript_events=transcript_hash)
        rendered = json.dumps(display(report), indent=2, sort_keys=True, allow_nan=False)
    except (OSError, UnicodeError, ValueError, RecursionError, OverflowError) as error:
        print(f'goal lifecycle merge failed: {display(str(error))}', file=sys.stderr)
        return 2
    print(rendered)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
