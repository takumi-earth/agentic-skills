#!/usr/bin/env python3
"""Regression tests for resource ownership, publication, and guard compatibility."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('mover', SCRIPTS / 'move_pending_resources.py')
mover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mover)
REPO = next(p for p in SCRIPTS.parents if (p / 'auto-skill-creator/scripts/skill_change_guard.py').is_file())


def fixture(repo, count=1):
    owner = repo / 'review-pending-skills/pending-review/candidate/variant-001'
    package = owner / 'package/candidate'
    (package / 'agents').mkdir(parents=True)
    (package / 'scripts').mkdir()
    (owner / 'intent.md').write_text('resource owner')
    (owner / 'review.json').write_text(json.dumps(dict(candidate_name='candidate', variant_id='variant-001')))
    (package / 'SKILL.md').write_text('fixture skill')
    (package / 'agents/openai.yaml').write_text('interface: {}')
    (repo / '.scratchpad').mkdir()
    moves = []
    for index in range(count):
        source = repo / f'.scratchpad/resource-{index}.py'
        source.write_bytes(b'original\x00bytes\n')
        moves.append(dict(source=str(source), destination=str(package / f'scripts/resource-{index}.py'),
                          candidate_name='candidate', variant_id='variant-001', classification='reusable-resource', sha256=mover.sha256(source)))
    return dict(schema_version=1, moves=moves)


class ResourceMoveTests(unittest.TestCase):
    def test_real_multi_resource_transfer(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory); manifest = fixture(repo, 2)
            checked = mover.validate(repo, manifest)
            moved = mover.execute(checked)
            self.assertEqual(len(moved), 2)
            for record in manifest['moves']:
                self.assertFalse(Path(record['source']).exists())
                self.assertEqual(Path(record['destination']).read_bytes(), b'original\x00bytes\n')

    def test_destination_owner_and_source_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory); manifest = fixture(repo)
            record = manifest['moves'][0]; destination = record['destination']
            record['destination'] = str(repo / 'review-pending-skills/pending-review/unowned.json')
            with self.assertRaisesRegex(ValueError, 'declared candidate'):
                mover.validate(repo, manifest)
            record['destination'] = destination
            source = Path(record['source']); referent = source.with_name('referent.py')
            source.rename(referent); source.symlink_to(referent)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                mover.validate(repo, manifest)
            self.assertTrue(source.is_symlink())
            self.assertEqual(referent.read_bytes(), b'original\x00bytes\n')

    def test_late_destination_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory); manifest = fixture(repo); checked = mover.validate(repo, manifest)
            destination = Path(manifest['moves'][0]['destination']); original_link = os.link
            def competing_link(source, target):
                destination.write_bytes(b'late destination')
                return original_link(source, target)
            with patch.object(mover.os, 'link', competing_link), self.assertRaises(mover.MoveFailure) as raised:
                mover.execute(checked)
            self.assertEqual(destination.read_bytes(), b'late destination')
            self.assertTrue(Path(manifest['moves'][0]['source']).exists())
            self.assertEqual(raised.exception.moved, [])
            self.assertEqual(raised.exception.partial, [])
            self.assertEqual(list(destination.parent.glob('.*.move.*')), [])

    def test_partial_effects_preserve_completed_and_remaining_moves(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory); manifest = fixture(repo, 2); checked = mover.validate(repo, manifest)
            original = mover.publish_resource
            def fail_second(record, progress):
                if record['source'] == checked[1]['source']:
                    raise OSError('second move unavailable')
                original(record, progress)
            with patch.object(mover, 'publish_resource', fail_second), self.assertRaises(mover.MoveFailure) as raised:
                mover.execute(checked)
            self.assertEqual(raised.exception.moved, checked[:1])
            self.assertEqual(raised.exception.remaining, checked[1:])
            self.assertFalse(Path(manifest['moves'][0]['source']).exists())
            self.assertTrue(Path(manifest['moves'][1]['source']).exists())

    def test_failure_after_publication_reports_retained_source(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory); manifest = fixture(repo); checked = mover.validate(repo, manifest)
            source = Path(manifest['moves'][0]['source']); original = Path.unlink
            def refuse_source(path, *args, **kwargs):
                if path == source:
                    raise PermissionError('source removal unavailable')
                return original(path, *args, **kwargs)
            with patch.object(Path, 'unlink', refuse_source), self.assertRaises(mover.MoveFailure) as raised:
                mover.execute(checked)
            self.assertEqual(raised.exception.partial[0]['phase'], 'destination-published-source-retained')
            self.assertTrue(source.exists())
            self.assertEqual(Path(manifest['moves'][0]['destination']).read_bytes(), source.read_bytes())

    def test_malformed_manifest_has_structured_cli_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory); manifest = fixture(repo); manifest['moves'][0]['source'] = None
            path = repo / '.scratchpad/manifest.json'; path.write_text(json.dumps(manifest))
            result = subprocess.run([sys.executable, str(SCRIPTS / 'move_pending_resources.py'), '--repo', str(repo), '--manifest', str(path), '--execute'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)['moved'], [])
            self.assertEqual(result.stderr, '')


class GuardAdapterTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / 'run_home_normalized_skill_guard.py'), '--guard', str(REPO / 'auto-skill-creator/scripts/skill_change_guard.py'), '--', *map(str, args)], capture_output=True, text=True)

    def test_supported_output_forms_and_native_status(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory); (repo / 'demo').mkdir(); target = repo / 'demo/SKILL.md'; target.write_text('before')
            for index, inline in enumerate([False, True]):
                output = repo / f'.scratchpad/snapshot-{index}.json'
                output_args = ['--output=' + str(output)] if inline else ['--output', str(output)]
                result = self.invoke('snapshot', '--skills-root', repo, '--existing', 'demo', *output_args)
                self.assertEqual(result.returncode, 0, result.stderr)
                original = output.read_bytes()
                self.assertEqual(self.invoke('unchanged', '--snapshot', output).returncode, 0)
                conflict = self.invoke('snapshot', '--skills-root', repo, '--existing', 'demo', *output_args)
                self.assertEqual(conflict.returncode, 2)
                self.assertEqual(json.loads(conflict.stdout)['code'], 'snapshot-conflict')
                self.assertEqual(output.read_bytes(), original)
            target.write_text('after')
            self.assertEqual(self.invoke('unchanged', '--snapshot', output).returncode, 1)
            self.assertEqual(self.invoke('verify', '--snapshot', output, '--allow', 'demo/SKILL.md').returncode, 0)
            self.assertEqual(self.invoke('verify', '--snapshot', output).returncode, 1)

    def test_outside_snapshot_does_not_create_output_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory); output = repo / 'outside/new/snapshot.json'
            result = self.invoke('snapshot', '--skills-root', repo, '--new', 'demo', '--output=' + str(output))
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.parent.exists())


if __name__ == '__main__':
    unittest.main()
