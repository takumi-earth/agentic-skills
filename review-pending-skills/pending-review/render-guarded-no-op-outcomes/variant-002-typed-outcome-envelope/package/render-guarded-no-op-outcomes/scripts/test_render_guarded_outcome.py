#!/usr/bin/env python3
"""Exercise outcome semantics, schema agreement, and factual rendering."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator
import render_guarded_outcome as renderer


def envelope(kind='no-op'):
    value = {'operation':'restore', 'target':'src/target.rs', 'outcome':kind,
             'guard':{'matched':True,'condition':'current bytes','expected':'','received':''},
             'desired_state':{'description':'selected bytes already present','proven':True},
             'write_count':0, 'verification':{'status':'not-run','description':'user excluded verification'}, 'error':None}
    if kind == 'write':
        value['write_count'] = 2
    elif kind == 'blocked':
        value['guard']['matched'] = False
    elif kind == 'failed':
        value.update(write_count=3, error='second phase failed')
    return value


class GuardedOutcomeTests(unittest.TestCase):
    def test_schema_and_runtime_accept_the_same_outcome_contracts(self):
        schema_path = Path(renderer.__file__).parent.parent/'references/guarded-outcome.schema.json'
        schema = json.loads(schema_path.read_text())
        Draft202012Validator.check_schema(schema)
        oracle = Draft202012Validator(schema)
        cases = [(envelope(kind), True) for kind in ('no-op','write','blocked','failed')]
        for kind in ('no-op','write','blocked','failed'):
            value = envelope(kind)
            value.update(outcome='verified', application_outcome=kind, verification={'status':'passed','description':'post-state check passed'})
            cases.append((value, True))
        for field in envelope():
            value = envelope(); del value[field]
            cases.append((value, False))
        for patch in ({'outcome':[]}, {'extra':1}, {'write_count':True}, {'write_count':-1},
                      {'write_count':1.5}, {'error':'unexpected'}, {'operation':'   '},
                      {'application_outcome':'no-op'}, {'outcome':'verified'}):
            cases.append(({**envelope(), **patch}, False))
        for field, patch in (('guard',{'condition':''}), ('guard',{'condition':'  '}), ('guard',{'expected':None}),
                             ('guard',{'matched':False}), ('guard',{'unknown':0}), ('desired_state',{'proven':False}),
                             ('verification',{'status':[]}), ('verification',{'status':'passed','description':''})):
            value = envelope(); value[field].update(patch); cases.append((value, False))
        fractional_spelling = envelope('write'); fractional_spelling['write_count'] = 1.0
        cases.append((fractional_spelling, True))
        for kind, patch in (('write', {'write_count':0}), ('blocked', {'write_count':2}), ('failed', {'error':''})):
            cases.append(({**envelope(kind), **patch}, False))
        verified_without_pass = envelope()
        verified_without_pass.update(outcome='verified', application_outcome='no-op')
        cases.append((verified_without_pass, False))
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(oracle.is_valid(value), expected)
                try:
                    renderer.validate(value)
                    valid = True
                except renderer.OutcomeError:
                    valid = False
                self.assertEqual(valid, expected)

    def test_failed_and_verified_results_preserve_partial_effects(self):
        failed = envelope('failed')
        text = renderer.render(renderer.validate(failed))
        self.assertIn('application failed', text)
        self.assertIn('completed writes: 3', text)
        self.assertIn('second phase failed', text)
        failed.update(outcome='verified', application_outcome='failed', verification={'status':'passed','description':'failure state verified'})
        text = renderer.render(renderer.validate(failed))
        self.assertIn('application failed', text)
        self.assertIn('completed writes: 3', text)
        self.assertIn('Verification: passed', text)

    def test_noop_includes_desired_state_and_literal_empty_observations(self):
        value = envelope()
        text = renderer.render(renderer.validate(value))
        self.assertIn('expected "", received ""', text)
        self.assertIn(value['desired_state']['description'], text)
        self.assertIn('completed writes: 0', text)
        self.assertNotIn('zero writes were attempted', text)

    def test_cli_normalizes_presentation_and_hashes_original_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'outcome.json'
            value = envelope('failed')
            value.update(target=str(Path.home()/'target.rs'), error=str(Path.home()/'failure.log'))
            source = json.dumps(value).encode(); path.write_bytes(source)
            result = subprocess.run([sys.executable, renderer.__file__, '--input', str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            self.assertEqual(output['input_sha256'], hashlib.sha256(source).hexdigest())
            self.assertEqual(output['outcome']['target'], '~/target.rs')
            self.assertNotIn(str(Path.home())+'/', result.stdout)
            self.assertEqual(path.read_bytes(), source)
            self.assertEqual(result.stderr, '')

    def test_malformed_input_keeps_failure_channel_and_path_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'invalid.json'
            for data in (b'\xff', json.dumps({**envelope(), 'outcome':[]}).encode()):
                path.write_bytes(data)
                result = subprocess.run([sys.executable, renderer.__file__, '--input', str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertNotIn('Traceback', result.stderr)
        sibling = str(Path.home())+'-neighbor/target'
        self.assertEqual(renderer.display_text(sibling), sibling)


if __name__ == '__main__':
    unittest.main()
