#!/usr/bin/env python3
"""Verify model-driven schema generation, validation, and path presentation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Required
import unittest
from jsonschema import Draft202012Validator, FormatChecker

SCRIPT = Path(__file__).with_name('generate_evidence_schema.py')
spec = importlib.util.spec_from_file_location('evidence_model', SCRIPT)
model = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = model
spec.loader.exec_module(model)


def record():
    return dict(schema_version=1, event_id='event-1', event_type='check', status='passed')


class EvidenceModelTests(unittest.TestCase):
    def test_schema_follows_typed_model_changes(self):
        class Extended(model.EvidenceRecord):
            owner: Required[str]
        generated = model.schema(Extended)
        self.assertIn('owner', generated['required'])
        self.assertEqual(generated['properties']['owner']['type'], 'string')
        self.assertNotEqual(generated['x-model-sha256'], model.schema()['x-model-sha256'])
        self.assertTrue(model.validate_instance(record(), Extended))
        self.assertFalse(model.validate_instance(dict(record(), owner='test-owner'), Extended))

    def test_schema_and_runtime_agree_on_input_values(self):
        checker = FormatChecker()
        checker.checks('home-presented-path')(lambda value: not isinstance(value, str) or model.presented_path(value) == value)
        schema = model.schema(); Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=checker)
        cases = [record(), {}, dict(record(), schema_version=True), dict(record(), schema_version=2),
                 dict(record(), schema_version=1.0), dict(record(), event_id=' '),
                 dict(record(), evidence=[None]), dict(record(), evidence=['~/run/report.json']),
                 dict(record(), evidence=[str(Path.home() / 'run/report.json')])]
        for value in cases:
            self.assertEqual(not model.validate_instance(value), validator.is_valid(value), value)

    def test_path_normalization_preserves_nonpath_evidence(self):
        raw = str(Path.home() / 'run/report.json')
        value = dict(record(), evidence=[raw, str(Path.home()) + '-neighbor/report'], expected=raw, note=raw)
        normalized = model.normalize_instance(value)
        self.assertEqual(normalized['evidence'][0], '~/run/report.json')
        self.assertEqual(normalized['evidence'][1], value['evidence'][1])
        self.assertEqual(normalized['expected'], raw)
        self.assertEqual(normalized['note'], raw)
        self.assertEqual(value['evidence'][0], raw)

    def test_cli_validation_preserves_input_bytes_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'evidence.json'
            raw = json.dumps(dict(record(), evidence=[str(Path.home() / 'run/report.json')])).encode()
            source.write_bytes(raw)
            result = subprocess.run([sys.executable, str(SCRIPT), '--validate', str(source)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['validated_representation'], 'normalized-projection')
            self.assertTrue(report['normalization_applied'])
            self.assertEqual(report['input_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(source.read_bytes(), raw)
            source.write_text('{"schema_version":NaN}')
            result = subprocess.run([sys.executable, str(SCRIPT), '--validate', str(source)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stderr, '')

    def test_generation_and_drift_check(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'schema.json'
            command = [sys.executable, str(SCRIPT), '--output', str(output)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(subprocess.run(command + ['--check'], capture_output=True).returncode, 0)
            output.write_text('{}')
            result = subprocess.run(command + ['--check'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['model_sha256'], model.schema()['x-model-sha256'])
        self.assertEqual(model.diagnostic(Path.home() / 'schema.json'), '~/schema.json')


if __name__ == '__main__':
    unittest.main()
