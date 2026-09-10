#!/usr/bin/env python3
"""Validate declarations using the packaged schema and explicit cross-field checks."""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

SCHEMA = Path(__file__).resolve().parents[1] / 'references/transformation-contract.schema.json'
KEYWORDS = {'$schema', '$id', 'title', 'description', 'type', 'required', 'properties', 'additionalProperties',
            'items', 'minItems', 'uniqueItems', 'const', 'enum', 'minLength', 'pattern', 'minimum',
            'allOf', 'if', 'then', 'contains', 'minProperties', 'propertyNames'}


def equal(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equal(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(equal(a, b) for a, b in zip(left, right))
    return left == right


def matches_type(value, kind):
    types = {'object': dict, 'array': list, 'string': str, 'boolean': bool}
    if kind == 'integer':
        return type(value) is int or (type(value) is float and math.isfinite(value) and value.is_integer())
    return isinstance(value, types[kind])


def defect(path, condition, expected, received):
    return dict(condition=f'{path}: {condition}', expected=expected, received=received)


def object_errors(value, schema, path):
    errors = []
    for key in schema.get('required', []):
        if key not in value:
            errors.append(defect(f'{path}.{key}', 'required field', 'present', {'present': False}))
    if len(value) < schema.get('minProperties', 0):
        errors.append(defect(path, 'minimum property count', schema['minProperties'], len(value)))
    properties = schema.get('properties', {})
    for key, item in value.items():
        if 'propertyNames' in schema:
            errors += check(key, schema['propertyNames'], f'{path}.{key}')
        if key in properties:
            errors += check(item, properties[key], f'{path}.{key}')
        elif isinstance(schema.get('additionalProperties'), dict):
            errors += check(item, schema['additionalProperties'], f'{path}.{key}')
        elif schema.get('additionalProperties') is False:
            errors.append(defect(f'{path}.{key}', 'unknown field', sorted(properties), key))
    return errors


def array_errors(value, schema, path):
    errors = []
    if len(value) < schema.get('minItems', 0):
        errors.append(defect(path, 'minimum item count', schema['minItems'], len(value)))
    if schema.get('uniqueItems') and any(any(equal(item, prior) for prior in value[:i]) for i, item in enumerate(value)):
        errors.append(defect(path, 'unique items', True, value))
    if 'contains' in schema and not any(not check(item, schema['contains'], path) for item in value):
        errors.append(defect(path, 'required member', schema['contains'], value))
    for i, item in enumerate(value):
        errors += check(item, schema.get('items', {}), f'{path}[{i}]')
    return errors


def scalar_errors(value, schema, path):
    errors = []
    if 'const' in schema and not equal(value, schema['const']):
        errors.append(defect(path, 'constant', schema['const'], value))
    if 'enum' in schema and not any(equal(value, allowed) for allowed in schema['enum']):
        errors.append(defect(path, 'allowed value', schema['enum'], value))
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            errors.append(defect(path, 'minimum length', schema['minLength'], len(value)))
        if 'pattern' in schema and re.search(schema['pattern'], value) is None:
            errors.append(defect(path, 'pattern', schema['pattern'], value))
    if type(value) in (int, float) and 'minimum' in schema and value < schema['minimum']:
        errors.append(defect(path, 'minimum', schema['minimum'], value))
    return errors


def check(value, schema, path='$'):
    unsupported = set(schema) - KEYWORDS
    if unsupported:
        raise ValueError(f'unsupported packaged schema keywords: {sorted(unsupported)}')
    if 'type' in schema and not matches_type(value, schema['type']):
        return [defect(path, 'type', schema['type'], value)]
    errors = scalar_errors(value, schema, path)
    if isinstance(value, dict):
        errors += object_errors(value, schema, path)
    if isinstance(value, list):
        errors += array_errors(value, schema, path)
    for condition in schema.get('allOf', []):
        errors += check(value, condition, path)
    if 'if' in schema and not check(value, schema['if'], path):
        errors += check(value, schema.get('then', {}), path)
    return errors


def validate_contract(document):
    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    errors = check(document, schema)
    if errors:
        return errors
    cardinality = document['cardinality']
    if cardinality['minimum'] > cardinality['maximum']:
        errors.append(defect('$.cardinality', 'ordered bounds', 'minimum <= maximum', cardinality))
    return errors


def display(value):
    if isinstance(value, str):
        return re.sub(re.escape(str(Path.home())) + r'(?=$|[/\s\x27\x22:,)])', '~', value)
    if isinstance(value, dict):
        return {display(k): display(v) for k, v in value.items()}
    if isinstance(value, list):
        return [display(item) for item in value]
    return value


def invalid_constant(value):
    raise ValueError(f'nonfinite JSON value: {value}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract', type=Path)
    args = parser.parse_args(argv)
    try:
        document = json.loads(args.contract.expanduser().read_text(encoding='utf-8'), parse_constant=invalid_constant)
        errors = validate_contract(document)
        output = display(dict(status='invalid' if errors else 'valid', errors=errors))
        rendered = json.dumps(output, sort_keys=True, allow_nan=False)
    except (OSError, UnicodeError, ValueError, RecursionError, OverflowError) as error:
        print(json.dumps(dict(status='invalid-input', errors=[defect('input', 'readable declaration and schema', 'valid JSON input', display(str(error)))])))
        return 2
    print(rendered)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
