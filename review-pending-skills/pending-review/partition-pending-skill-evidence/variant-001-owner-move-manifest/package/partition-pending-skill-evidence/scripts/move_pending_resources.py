#!/usr/bin/env python3
"""Validate and execute an ownership-preserving pending-resource move manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import os
import re
import shutil
import stat
import tempfile
from typing import Any


USER_HOME = Path.home().resolve()


def display(path: Path) -> str:
    absolute = path.expanduser().absolute()
    try:
        relative = absolute.relative_to(USER_HOME)
    except ValueError:
        return str(absolute)
    return "~" if relative == Path(".") else f"~/{relative.as_posix()}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contained(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.expanduser().read_text(encoding="utf-8"))


def validate_shape(manifest):
    if not isinstance(manifest, dict) or set(manifest) != {'schema_version', 'moves'} or type(manifest['schema_version']) not in (int, float) or manifest['schema_version'] != 1:
        raise ValueError('manifest must contain schema_version integer 1 and moves')
    if not isinstance(manifest['moves'], list) or not manifest['moves']:
        raise ValueError('manifest requires a nonempty moves array')
    required = {'source', 'destination', 'sha256', 'classification', 'candidate_name', 'variant_id'}
    for record in manifest['moves']:
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError('move fields must match the manifest schema')
        if not all(isinstance(v, str) and v.strip() for v in record.values()):
            raise ValueError('move fields must be nonempty strings')
        if record['classification'] != 'reusable-resource' or re.fullmatch(r'[0-9a-f]{64}', record['sha256']) is None:
            raise ValueError('move classification or sha256 is invalid')
        if any(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', record[k]) is None for k in ('candidate_name', 'variant_id')):
            raise ValueError('candidate and variant names must be lowercase hyphen-case')


def selected_path(raw, repository):
    path = Path(os.path.abspath(repository / Path(raw).expanduser()))
    if not contained(path, repository):
        raise ValueError('selected path escapes repository')
    current = repository
    for part in path.relative_to(repository).parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f'selected path crosses a symlink: {display(current)}')
    return path


def validate_owner(repository, record, destination):
    owner = repository / 'review-pending-skills/pending-review' / record['candidate_name'] / record['variant_id']
    if destination == owner or not contained(destination, owner):
        raise ValueError('destination is outside the declared candidate and variant')
    for relative in ('intent.md', 'review.json', f"package/{record['candidate_name']}/SKILL.md", f"package/{record['candidate_name']}/agents/openai.yaml"):
        path = selected_path(str(owner / relative), repository)
        if not path.is_file():
            raise ValueError(f'owning variant is incomplete: {display(path)}')
    metadata = json.loads((owner / 'review.json').read_text(encoding='utf-8'))
    if not isinstance(metadata, dict) or any(metadata.get(k) != record[k] for k in ('candidate_name', 'variant_id')):
        raise ValueError('destination owner metadata disagrees with manifest')
    return owner


def identity(path):
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError('selected source is not a regular file')
    return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns]


def validate(repo: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    validate_shape(manifest)
    repository = repo.expanduser().resolve(strict=True)
    checked, sources, destinations = [], set(), set()
    for record in manifest['moves']:
        source = selected_path(record['source'], repository)
        destination = selected_path(record['destination'], repository)
        if not contained(source, repository / '.scratchpad'):
            raise ValueError('source must be beneath repository scratchpad')
        validate_owner(repository, record, destination)
        if source in sources or destination in destinations:
            raise ValueError('move ownership uniqueness check failed')
        sources.add(source); destinations.add(destination)
        source_identity = identity(source)
        if os.path.lexists(destination):
            raise FileExistsError(f'destination already exists: {display(destination)}')
        if not destination.parent.is_dir():
            raise ValueError('destination parent must already exist')
        if sha256(source) != record['sha256']:
            raise ValueError('source hash differs from manifest')
        checked.append(dict(record, source=display(source), destination=display(destination),
                            source_identity=source_identity, repository=display(repository)))
    return checked


class MoveFailure(RuntimeError):
    def __init__(self, cause, moved, remaining, partial):
        super().__init__(str(cause))
        self.moved, self.remaining, self.partial = moved, remaining, partial


def publish_resource(record, progress):
    source = Path(record['source']).expanduser()
    destination = Path(record['destination']).expanduser()
    repository = Path(record['repository']).expanduser()
    selected_path(str(source), repository)
    selected_path(str(destination), repository)
    validate_owner(repository, record, destination)
    if identity(source) != record['source_identity']:
        raise ValueError('source identity changed after validation')
    descriptor, temporary_name = tempfile.mkstemp(prefix=f'.{destination.name}.move.', dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            source_descriptor = os.open(source, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
            with os.fdopen(source_descriptor, 'rb') as input_file:
                info = os.fstat(input_file.fileno())
                if [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns] != record['source_identity']:
                    raise ValueError('opened source differs from selected source')
                shutil.copyfileobj(input_file, output)
            output.flush(); os.fsync(output.fileno())
            os.fchmod(output.fileno(), stat.S_IMODE(info.st_mode))
        if sha256(temporary) != record['sha256']:
            raise ValueError('copied resource hash differs from manifest')
        os.utime(temporary, ns=(info.st_atime_ns, info.st_mtime_ns))
        os.link(temporary, destination)  # Exclusive publication; never replace a late destination.
        progress.append(dict(record, phase='destination-published-source-retained'))
        selected_path(str(source), repository)
        if identity(source) != record['source_identity'] or sha256(source) != record['sha256']:
            raise ValueError('source changed before removal; published destination retained')
        source.unlink()
        progress[-1]['phase'] = 'source-removed'
        if os.path.lexists(source) or sha256(destination) != record['sha256']:
            raise ValueError('post-move source absence or destination integrity failed')
    finally:
        temporary.unlink(missing_ok=True)


def execute(checked: list[dict[str, Any]]) -> list[dict[str, Any]]:
    moved = []
    for index, record in enumerate(checked):
        progress = []
        try:
            publish_resource(record, progress)
        except (OSError, ValueError, RuntimeError) as error:
            raise MoveFailure(error, moved, checked[index + 1:] if progress else checked[index:], progress) from error
        moved.append(record)
    return moved


def diagnostic(value):
    return re.sub(re.escape(str(USER_HOME)) + r"(?=$|[/\s\x27\x22:,)])", '~', str(value))


def self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary) / "repo"
        source = repo / ".scratchpad" / "run" / "resource.py"
        destination = (
            repo
            / "review-pending-skills"
            / "pending-review"
            / "candidate"
            / "variant-001"
            / "package"
            / "candidate"
            / "scripts"
            / "resource.py"
        )
        source.parent.mkdir(parents=True)
        destination.parent.mkdir(parents=True)
        source.write_text("resource\n", encoding="utf-8")
        owner = destination.parents[3]
        (owner / 'intent.md').write_text('fixture owner')
        (owner / 'review.json').write_text(json.dumps(dict(candidate_name='candidate', variant_id='variant-001')))
        (owner / 'package/candidate/SKILL.md').write_text('fixture skill')
        (owner / 'package/candidate/agents').mkdir()
        (owner / 'package/candidate/agents/openai.yaml').write_text('interface: {}')
        manifest = {
            "schema_version": 1,
            "moves": [
                {
                    "source": str(source),
                    "destination": str(destination),
                    "sha256": sha256(source),
                    "classification": "reusable-resource",
                    "candidate_name": "candidate", "variant_id": "variant-001",
                }
            ],
        }
        checked = validate(repo, manifest)
        moved = execute(checked)
        assert len(moved) == 1
        assert not source.exists()
        assert destination.read_text(encoding="utf-8") == "resource\n"
        assert sha256(destination) == moved[0]["sha256"]
    return {"status": "passed", "assertions": 4, "operation": "exclusive-resource-transfer"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--manifest", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and (arguments.repo is None or arguments.manifest is None):
        parser.error("--repo and --manifest are required unless --self-test is used")
    return arguments


def main() -> int:
    arguments = parse_args()
    if arguments.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return 0
    try:
        checked = validate(arguments.repo, load_manifest(arguments.manifest))
    except (OSError, ValueError, RuntimeError, RecursionError) as error:
        print(json.dumps(dict(status='failure', code='invalid-manifest', error=diagnostic(error), moved=[], partial=[], remaining=[])))
        return 2
    try:
        moved = execute(checked) if arguments.execute else []
    except MoveFailure as error:
        print(json.dumps(dict(status='failure', code='move-failed', error=diagnostic(error), moved=error.moved, remaining=error.remaining, partial=error.partial)))
        return 3
    print(
        json.dumps(
            {
                "status": "moved" if arguments.execute else "validated",
                "checked": checked,
                "moved": moved,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
