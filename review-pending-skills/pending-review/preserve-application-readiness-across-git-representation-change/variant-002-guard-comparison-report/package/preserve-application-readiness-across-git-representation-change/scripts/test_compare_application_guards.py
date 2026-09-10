#!/usr/bin/env python3
"""Check readiness evidence without claiming live repository validation."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import compare_application_guards as guards


def snapshot():
    return {
        'content_guards': {'target.rs': 'a'*64},
        'restore_objects': {'blob': {'available': True, 'sha256':'b'*64}},
        'effect_paths': ['target.rs'],
        'operations': {'target.rs': {'id':'replace-target', 'kind':'restore', 'restore_object':'blob'}},
        'index_preservation_capability': True,
        'recovery_requirements': {'method':'preserve-current-index', 'exact_head':False, 'exact_index':False},
        'head':'before', 'index_sha256':'c'*64,
    }


class GuardComparisonTests(unittest.TestCase):
    def test_representation_change_and_exact_recovery_requirements(self):
        before = snapshot()
        after = copy.deepcopy(before)
        after.update(head='after', index_sha256='d'*64)
        result = guards.compare(before, after)
        self.assertTrue(result['application_ready'])
        self.assertFalse(result['independently_verified'])
        self.assertFalse(result['authorization_checked'])
        for field, blocker in (('exact_head','required_head_matches'), ('exact_index','required_index_matches')):
            left, right = copy.deepcopy(before), copy.deepcopy(after)
            left['recovery_requirements'][field] = right['recovery_requirements'][field] = True
            self.assertIn(blocker, guards.compare(left, right)['blockers'])

    def test_unavailable_replacement_never_becomes_ready_by_equality(self):
        before = snapshot()
        before['restore_objects']['blob']['available'] = False
        self.assertIn('current_replacements_available', guards.compare(before, before)['blockers'])
        self.assertTrue(guards.compare(before, snapshot())['application_ready'])

    def test_malformed_nested_values_and_missing_coverage_are_rejected(self):
        changes = [
            {'content_guards':{}}, {'content_guards':{'target.rs':{}}},
            {'restore_objects':{'blob':{'available':'yes','sha256':'b'*64}}},
            {'restore_objects':{'blob':{'available':True,'sha256':'invalid'}}},
            {'operations':{}}, {'effect_paths':['target.rs', []]},
            {'recovery_requirements':{'method':'index','exact_head':True,'exact_index':1}},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(guards.GuardError):
                malformed = {**snapshot(), **change}
                guards.compare(malformed, malformed)

    def test_deletion_only_and_changed_operation_identity(self):
        deletion = snapshot()
        deletion['restore_objects'] = {}
        deletion['operations']['target.rs'] = {'id':'delete-target','kind':'delete','restore_object':None}
        self.assertTrue(guards.compare(deletion, deletion)['application_ready'])
        changed = copy.deepcopy(deletion)
        changed['operations']['target.rs']['id'] = 'different-selection'
        self.assertIn('operations_match', guards.compare(deletion, changed)['blockers'])

    def test_target_bytes_and_current_index_capability_block_independently(self):
        before, after = snapshot(), snapshot()
        after['content_guards']['target.rs'] = 'd'*64
        after['index_preservation_capability'] = False
        self.assertEqual(guards.compare(before, after)['blockers'], ['content_guards_match', 'current_index_preservable'])

    def test_cli_only_reads_supplied_snapshots_and_normalizes_failure_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'snapshot.json'
            path.write_text(json.dumps(snapshot()))
            original = path.read_bytes()
            command = [sys.executable, guards.__file__, '--before', str(path), '--after', str(path)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertTrue(json.loads(result.stdout)['application_ready'])
            self.assertEqual(path.read_bytes(), original)
            command[-1] = str(Path.home()/Path(temporary).name/'missing.json')
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('~/', result.stderr)
            self.assertNotIn(str(Path.home())+'/', result.stderr)


if __name__ == '__main__':
    unittest.main()
