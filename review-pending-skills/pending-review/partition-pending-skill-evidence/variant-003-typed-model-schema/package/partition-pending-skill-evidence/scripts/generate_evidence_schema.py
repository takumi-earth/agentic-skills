#!/usr/bin/env python3
"""Generate and validate evidence contracts from one authoritative typed model."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Annotated, Any, Literal, Required, TypedDict, get_args, get_origin, get_type_hints

Nonempty = Annotated[str, 'nonempty']
EvidencePath = Annotated[str, 'path']


class EvidenceRecord(TypedDict, total=False):
    schema_version: Required[Literal[1]]
    event_id: Required[Nonempty]
    event_type: Required[Nonempty]
    status: Required[Nonempty]
    condition: str
    expected: Any
    received: Any
    evidence: list[EvidencePath]


def presented_path(value: str) -> str:
    home = str(Path.home())
    return '~' + value[len(home):] if value == home or value.startswith(home + '/') else value


def field_schema(hint):
    origin, args = get_origin(hint), get_args(hint)
    if origin is Required:
        return field_schema(args[0])
    if origin is Annotated:
        result = field_schema(args[0])
        for constraint in args[1:]:
            if constraint == 'nonempty':
                result.update(minLength=1, pattern=r'\S')
            elif constraint == 'path':
                result.update(minLength=1, format='home-presented-path')
            else:
                raise ValueError(f'unsupported model constraint: {constraint}')
        return result
    if origin is Literal and len(args) == 1 and type(args[0]) is int:
        return dict(type='integer', const=args[0])
    if origin is list:
        return dict(type='array', items=field_schema(args[0]))
    if hint is Any:
        return {}
    if hint is str:
        return dict(type='string')
    raise ValueError(f'unsupported evidence field type: {hint}')


def model_contract(model=EvidenceRecord):
    hints = get_type_hints(model, include_extras=True)
    return dict(type='object', properties={key: field_schema(hint) for key, hint in hints.items()},
                required=[key for key, hint in hints.items() if get_origin(hint) is Required],
                additionalProperties=True)


def schema(model=EvidenceRecord):
    contract = model_contract(model)
    digest = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return dict(contract, **{'$schema': 'https://json-schema.org/draft/2020-12/schema',
                '$id': 'skill://partition-pending-skill-evidence/evidence-record.schema.json',
                'title': 'Automatic skill evidence record', 'x-model-sha256': digest})


def encoded():
    return json.dumps(schema(), indent=2, sort_keys=True) + '\n'


def value_errors(value, contract, path):
    kind = contract.get('type')
    valid_type = {'string': isinstance(value, str), 'array': isinstance(value, list),
                  'integer': type(value) is int or (type(value) is float and math.isfinite(value) and value.is_integer())}
    if kind and not valid_type[kind]:
        return [dict(condition=path + ': type', expected=kind, received=type(value).__name__)]
    errors = []
    if 'const' in contract and value != contract['const']:
        errors.append(dict(condition=path + ': constant', expected=contract['const'], received=value))
    if isinstance(value, str):
        if len(value) < contract.get('minLength', 0) or ('pattern' in contract and re.search(contract['pattern'], value) is None):
            errors.append(dict(condition=path + ': nonempty value', expected='nonempty', received=value))
        if contract.get('format') == 'home-presented-path' and presented_path(value) != value:
            errors.append(dict(condition=path + ': path presentation', expected='home-relative path', received='expanded-home path'))
    if kind == 'array':
        for index, item in enumerate(value):
            errors += value_errors(item, contract['items'], f'{path}[{index}]')
    return errors


def validate_instance(value, model=EvidenceRecord):
    if not isinstance(value, dict):
        return [dict(condition='evidence object', expected='object', received=type(value).__name__)]
    contract = model_contract(model)
    errors = [dict(condition=key + ': required field', expected='present', received='missing') for key in contract['required'] if key not in value]
    for key, field in contract['properties'].items():
        if key in value:
            errors += value_errors(value[key], field, key)
    return errors


def normalize_field(value, field):
    if field.get('format') == 'home-presented-path' and isinstance(value, str):
        return presented_path(value)
    if field.get('type') == 'array' and isinstance(value, list):
        return [normalize_field(item, field['items']) for item in value]
    return value


def normalize_instance(value):
    if not isinstance(value, dict):
        return value
    fields = model_contract()['properties']
    return {key: normalize_field(item, fields.get(key, {})) for key, item in value.items()}


def diagnostic(value):
    return re.sub(re.escape(str(Path.home())) + r'(?=$|[/\s\x27\x22:,)])', '~', str(value))


def self_test():
    good = dict(schema_version=1, event_id='one', event_type='check', status='passed')
    assert not validate_instance(good)
    assert validate_instance(dict(good, schema_version=True))
    assert encoded() == encoded()
    assert schema()['x-model-sha256'] == hashlib.sha256(json.dumps(model_contract(), sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return dict(status='passed', assertions=4)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--check', action='store_true')
    modes.add_argument('--self-test', action='store_true')
    modes.add_argument('--validate', type=Path, metavar='EVIDENCE_JSON')
    args = parser.parse_args()
    if not args.self_test and not args.validate and args.output is None:
        parser.error('--output is required for schema generation or checking')
    if args.validate and args.output:
        parser.error('--validate emits a report; it does not write the input or a schema')
    return args


def reject_nonfinite(value):
    raise ValueError(f'nonfinite JSON value: {value}')


def validate_file(path):
    raw = path.expanduser().read_bytes()
    value = json.loads(raw, parse_constant=reject_nonfinite)
    normalized = normalize_instance(value)
    errors = validate_instance(normalized)
    return dict(status='invalid' if errors else 'valid', errors=errors,
                input=diagnostic(path), input_sha256=hashlib.sha256(raw).hexdigest(),
                model_sha256=schema()['x-model-sha256'], validated_representation='normalized-projection',
                normalization_applied=normalized != value, input_unchanged=True), bool(errors)


def main():
    args = parse_args()
    try:
        if args.self_test:
            result, failed = self_test(), False
        elif args.validate:
            result, failed = validate_file(args.validate)
        else:
            output = args.output.expanduser()
            expected = encoded()
            if args.check:
                received = output.read_text(encoding='utf-8') if output.is_file() else None
                failed = received != expected
                result = dict(status='failure' if failed else 'valid', output=diagnostic(output),
                              condition='generated schema equals typed-model projection', model_sha256=schema()['x-model-sha256'])
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(expected, encoding='utf-8')
                result, failed = dict(status='written', output=diagnostic(output), model_sha256=schema()['x-model-sha256']), False
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 1 if failed else 0
    except (OSError, ValueError, TypeError, RecursionError) as error:
        print(json.dumps(dict(status='failure', code='invalid-input-or-io', error=diagnostic(error)), sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
