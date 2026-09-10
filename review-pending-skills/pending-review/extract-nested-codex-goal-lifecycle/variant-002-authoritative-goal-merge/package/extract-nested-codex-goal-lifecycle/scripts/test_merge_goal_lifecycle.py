#!/usr/bin/env python3
"""Exercise identity, observation, and timestamp boundaries without a live goal store."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('merge_goal_lifecycle.py')
spec = importlib.util.spec_from_file_location('goal_merge', SCRIPT)
merge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(merge)


def authority(status='complete', at='2026-08-12T08:00:00Z'):
    return dict(goal_id='goal-a', thread_id='thread-a', status=status, observed_at=at)


def event(**updates):
    value = dict(goal_id='goal-a', thread_id='thread-a', call_id='call-1', line=1,
                 status='blocked', output_confirms=True, timestamp='2026-08-12T07:00:00Z')
    value.update(updates)
    return value


class GoalMergeTests(unittest.TestCase):
    def test_actual_instants_select_latest_and_detect_ambiguity(self):
        records = [authority('blocked', '2026-08-12T09:30:00+02:00'), authority()]
        self.assertEqual(merge.select_authority(dict(records=records), 'goal-a', 'thread-a')['status'], 'complete')
        records.append(authority('blocked', '2026-08-12T10:00:00+02:00'))
        with self.assertRaisesRegex(merge.MergeError, 'ambiguous'):
            merge.select_authority(dict(records=records), 'goal-a', 'thread-a')

    def test_history_is_not_current_contradiction(self):
        events = merge.normalize_events(dict(events=[event(), event(state_at='2026-08-12T10:00:00+02:00')]))
        report = merge.merge(authority(), events)
        self.assertEqual(len(report['historical_transcript_events']), 1)
        self.assertEqual(len(report['disagreements']), 1)
        self.assertEqual(report['current_status'], 'complete')

    def test_goal_and_thread_identity_do_not_leak(self):
        unknown = event(); del unknown['goal_id']
        events = merge.normalize_events(dict(events=[event(goal_id='goal-b'), event(thread_id='thread-b'), unknown]))
        report = merge.merge(authority(), events)
        self.assertEqual(len(report['other_goal_or_thread_events']), 2)
        self.assertEqual(len(report['unattributed_transcript_events']), 1)
        self.assertEqual(report['confirmed_transcript_events'], [])
        self.assertEqual(report['other_goal_or_thread_events'][0]['goal_id'], 'goal-b')

    def test_official_nested_confirmation_and_identity(self):
        raw = dict(kind='nested_goal_call_site', tool='update_goal', call_id='outer-1', line=4,
                   arguments=dict(status='complete'), timestamp=None, input_offset=8, input_line=1,
                   output_confirmation='unattributed-output', output_lines=[5], output=None)
        row = merge.normalize_event(raw)
        self.assertEqual(row['attribution'], 'unresolved')
        self.assertEqual(row['output_confirmation'], 'unattributed-output')
        raw.update(output_confirmation='confirmed', output=dict(goal=dict(status='complete', goal_id='goal-a', thread_id='thread-a')))
        row = merge.normalize_event(raw)
        self.assertEqual(row['goal_id'], 'goal-a')
        raw['goal_id'] = 'goal-b'
        row = merge.normalize_event(raw)
        self.assertEqual(row['attribution'], 'conflicting')
        self.assertEqual(len(merge.merge(authority(), [row])['unattributed_transcript_events']), 1)
        raw['output'] = None
        with self.assertRaises(merge.MergeError):
            merge.normalize_event(raw)

    def test_malformed_shapes_are_controlled(self):
        for field, value in [('status', []), ('line', True), ('line', -1), ('call_id', ''), ('timestamp', 'tomorrow')]:
            with self.subTest(field=field), self.assertRaises(merge.MergeError):
                merge.normalize_event(event(**{field: value}))
        for record in [dict(authority(), extra=True), authority(at='tomorrow'), dict(authority(), status=[])]:
            with self.assertRaises(merge.MergeError):
                merge.select_authority(dict(records=[record]), 'goal-a', 'thread-a')
        with self.assertRaisesRegex(merge.MergeError, 'no authoritative'):
            merge.select_authority(dict(records=[authority()]), 'goal-b', 'thread-a')

    def test_cli_hashes_consumed_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); events = root / 'events.json'; records = root / 'records.json'
            events.write_text(json.dumps(dict(events=[event()])))
            records.write_text(json.dumps(dict(records=[authority()])))
            args = [sys.executable, str(SCRIPT), '--goal-id', 'goal-a', '--thread-id', 'thread-a',
                    '--transcript-events', str(events), '--authoritative', str(records)]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['input_hashes']['transcript_events'], hashlib.sha256(events.read_bytes()).hexdigest())
            records.write_text(json.dumps(dict(records=[dict(authority(), status=[])])))
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, '')
            self.assertNotIn('Traceback', result.stderr)

    def test_diagnostic_paths_preserve_home_neighbors(self):
        home = str(Path.home())
        self.assertEqual(merge.display(home + '/missing.json'), '~/missing.json')
        self.assertEqual(merge.display(home + '-neighbor/missing.json'), home + '-neighbor/missing.json')


if __name__ == '__main__':
    unittest.main()
