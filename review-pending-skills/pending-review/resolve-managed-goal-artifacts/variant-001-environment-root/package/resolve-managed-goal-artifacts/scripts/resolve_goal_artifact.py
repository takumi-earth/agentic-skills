#!/usr/bin/env python3
"""Resolve one exact managed goal artifact without package-topology inference."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import Any, Mapping


APPROACH = "environment-root"
STAGE_RUNTIME = "resolve-runtime-root"
STAGE_OBJECTIVE = "parse-goal-objective"
STAGE_ARTIFACT = "resolve-managed-goal-artifact"
UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z"
)
QUOTED_PATH_RE = re.compile(r"(?P<quote>[`\"'])(?P<path>(?:~|/).*?)(?P=quote)")
UNQUOTED_PATH_RE = re.compile(r"(?P<path>(?:~|/)[^\s`\"'<>]+)")
TRAILING_DELIMITERS = ".,;:!?)]}"


@dataclass(frozen=True)
class GoalArtifactResolution:
    """Typed, serializable result shared by every prospective consumer."""

    status: str
    stage: str
    code: str
    condition: str
    expected: Any
    received: Any
    candidate_count: int
    artifact: str | None = None
    approach: str = APPROACH

    def to_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-compatible representation."""

        return asdict(self)


def display_path(path: Path) -> str:
    """Render paths beneath the current home directory as `~/...`."""

    absolute = path.expanduser().absolute()
    home = Path.home().resolve(strict=False)
    try:
        relative = absolute.relative_to(home)
    except ValueError:
        return str(absolute)
    return "~" if relative == Path(".") else f"~/{relative.as_posix()}"


def failure(
    *,
    code: str,
    stage: str,
    condition: str,
    expected: Any,
    received: Any,
    candidate_count: int,
) -> GoalArtifactResolution:
    """Build one complete typed failure."""

    if not code or not stage or not condition:
        raise ValueError("resolution diagnostics require nonempty code, stage, and condition")
    return GoalArtifactResolution(
        status="failure",
        stage=stage,
        code=code,
        condition=condition,
        expected=expected,
        received=received,
        candidate_count=candidate_count,
    )


def invalid_runtime_root(reason: str, source: str) -> GoalArtifactResolution:
    """Return the stable failure for an unusable runtime authority."""

    return failure(
        code="invalid-runtime-root",
        stage=STAGE_RUNTIME,
        condition="the inherited runtime root is an existing usable directory with attachments",
        expected={"source": source, "state": "usable-directory-with-attachments"},
        received={"source": source, "state": reason},
        candidate_count=0,
    )


def resolve_runtime_root(
    environ: Mapping[str, str],
    *,
    fallback_home: Path | None = None,
) -> tuple[Path, Path] | GoalArtifactResolution:
    """Resolve `CODEX_HOME`, falling back only when the variable is absent."""

    if "CODEX_HOME" in environ:
        source = "CODEX_HOME"
        raw = environ["CODEX_HOME"]
        if not isinstance(raw, str) or not raw.strip():
            return invalid_runtime_root("empty", source)
        configured = Path(raw).expanduser()
    else:
        source = "fallback"
        base = Path.home() if fallback_home is None else fallback_home
        configured = base / ".codex"

    if not configured.is_absolute():
        return invalid_runtime_root("not-absolute", source)
    try:
        root = configured.resolve(strict=True)
    except (OSError, RuntimeError):
        return invalid_runtime_root("missing-or-unresolvable", source)
    if not root.is_dir():
        return invalid_runtime_root("not-directory", source)

    attachments_lexical = root / "attachments"
    if attachments_lexical.is_symlink():
        return invalid_runtime_root("attachments-symlink", source)
    try:
        attachments = attachments_lexical.resolve(strict=True)
    except (OSError, RuntimeError):
        return invalid_runtime_root("attachments-missing-or-unresolvable", source)
    if not attachments.is_dir():
        return invalid_runtime_root("attachments-not-directory", source)
    return root, attachments


def path_parts(reference: str) -> tuple[str, ...]:
    """Return lexical path parts without treating prose as authority."""

    normalized = reference.replace("~", "/home", 1) if reference.startswith("~/") else reference
    return PurePosixPath(normalized).parts


def looks_managed(reference: str) -> bool:
    """Return whether one path-shaped token names an attachments subtree."""

    return "attachments" in path_parts(reference)


def extract_managed_references(objective: str) -> list[str]:
    """Extract unique managed path spellings without assuming a filename or extension."""

    references: list[str] = []
    quoted_spans: list[tuple[int, int]] = []
    for match in QUOTED_PATH_RE.finditer(objective):
        quoted_spans.append(match.span())
        reference = match.group("path")
        if looks_managed(reference) and reference not in references:
            references.append(reference)

    for match in UNQUOTED_PATH_RE.finditer(objective):
        if any(start <= match.start() and match.end() <= end for start, end in quoted_spans):
            continue
        reference = match.group("path").rstrip(TRAILING_DELIMITERS)
        if looks_managed(reference) and reference not in references:
            references.append(reference)
    return references


def objective_path(reference: str) -> Path:
    """Expand one objective reference while retaining lexical traversal for validation."""

    return Path(reference).expanduser()


def lexical_traversal(reference: str) -> bool:
    """Return whether a reference contains a traversal segment."""

    return ".." in path_parts(reference)


def resolve_artifact(
    objective: Any,
    *,
    environ: Mapping[str, str] | None = None,
    fallback_home: Path | None = None,
) -> GoalArtifactResolution:
    """Resolve one exact regular managed artifact as a side-effect-free operation."""

    if not isinstance(objective, str):
        return failure(
            code="objective-not-text",
            stage=STAGE_OBJECTIVE,
            condition="the goal objective is text",
            expected="text",
            received=type(objective).__name__,
            candidate_count=0,
        )

    environment = os.environ if environ is None else environ
    runtime = resolve_runtime_root(environment, fallback_home=fallback_home)
    if isinstance(runtime, GoalArtifactResolution):
        return runtime
    _, attachments = runtime

    references = extract_managed_references(objective)
    if not references:
        return failure(
            code="no-managed-artifact-reference",
            stage=STAGE_OBJECTIVE,
            condition="the objective names one managed attachments artifact",
            expected=1,
            received=0,
            candidate_count=0,
        )
    if len(references) != 1:
        return failure(
            code="ambiguous-managed-artifacts",
            stage=STAGE_OBJECTIVE,
            condition="the objective names exactly one managed attachments artifact",
            expected=1,
            received=len(references),
            candidate_count=len(references),
        )

    reference = references[0]
    candidate_count = 1
    if lexical_traversal(reference):
        return failure(
            code="managed-path-shape",
            stage=STAGE_ARTIFACT,
            condition="the managed reference has no traversal segments",
            expected="attachments/<uuid>/<filename>",
            received="traversal-segment",
            candidate_count=candidate_count,
        )

    candidate = objective_path(reference)
    if not candidate.is_absolute():
        return failure(
            code="attachments-root-mismatch",
            stage=STAGE_ARTIFACT,
            condition="the managed reference resolves beneath the trusted attachments root",
            expected=display_path(attachments),
            received="non-absolute-reference",
            candidate_count=candidate_count,
        )

    try:
        resolved = candidate.resolve(strict=False)
        relative = resolved.relative_to(attachments)
    except (OSError, RuntimeError, ValueError):
        return failure(
            code="attachments-root-mismatch",
            stage=STAGE_ARTIFACT,
            condition="the managed reference resolves beneath the trusted attachments root",
            expected=display_path(attachments),
            received=display_path(candidate),
            candidate_count=candidate_count,
        )

    if (
        len(relative.parts) != 2
        or UUID_RE.fullmatch(relative.parts[0]) is None
        or relative.parts[1] in {"", ".", ".."}
    ):
        return failure(
            code="managed-path-shape",
            stage=STAGE_ARTIFACT,
            condition="the managed reference has attachments/<uuid>/<filename> shape",
            expected="<uuid>/<filename>",
            received=relative.as_posix(),
            candidate_count=candidate_count,
        )

    try:
        metadata = candidate.lstat()
    except OSError:
        return failure(
            code="artifact-not-file",
            stage=STAGE_ARTIFACT,
            condition="the managed artifact exists as a regular non-symlink file",
            expected="regular-file",
            received="missing-or-unreadable",
            candidate_count=candidate_count,
        )
    if not stat.S_ISREG(metadata.st_mode):
        received = "symlink" if stat.S_ISLNK(metadata.st_mode) else "not-regular-file"
        return failure(
            code="artifact-not-file",
            stage=STAGE_ARTIFACT,
            condition="the managed artifact exists as a regular non-symlink file",
            expected="regular-file",
            received=received,
            candidate_count=candidate_count,
        )

    return GoalArtifactResolution(
        status="success",
        stage=STAGE_ARTIFACT,
        code="resolved-exact-artifact",
        condition="one exact regular managed artifact is named by the objective",
        expected={"attachments_root": display_path(attachments), "candidate_count": 1},
        received={"attachments_root": display_path(attachments), "candidate_count": 1},
        candidate_count=1,
        artifact=display_path(resolved),
    )


def make_root(base: Path, name: str = "codex") -> tuple[Path, Path]:
    """Create one disposable runtime root and attachments directory."""

    root = base / name
    attachments = root / "attachments"
    attachments.mkdir(parents=True)
    return root, attachments


def make_artifact(attachments: Path, filename: str = "goal") -> Path:
    """Create one filename- and extension-agnostic managed artifact."""

    artifact = attachments / "12345678-1234-1234-1234-123456789abc" / filename
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("objective", encoding="utf-8")
    return artifact


def self_test() -> dict[str, Any]:
    """Exercise every stable code and the trusted-root boundary."""

    assertions = 0
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        custom_root, custom_attachments = make_root(base, "custom")
        artifact = make_artifact(custom_attachments, "goal-without-extension")
        objective = f"Continue from `{artifact}` after reading it fully."

        success = resolve_artifact(objective, environ={"CODEX_HOME": str(custom_root)})
        assert success.status == "success"
        assert success.code == "resolved-exact-artifact"
        assert success.artifact == str(artifact)
        assert success.candidate_count == 1
        assertions += 4

        repeated = resolve_artifact(objective, environ={"CODEX_HOME": str(custom_root)})
        assert repeated == success
        assertions += 1

        fallback_home = base / "fallback-home"
        fallback_root, fallback_attachments = make_root(fallback_home, ".codex")
        fallback_artifact = make_artifact(fallback_attachments, "artifact.data.bin")
        fallback = resolve_artifact(
            f"Managed artifact: {fallback_artifact}",
            environ={},
            fallback_home=fallback_home,
        )
        assert fallback.status == "success" and fallback.artifact == str(fallback_artifact)
        assert fallback_root == fallback_home / ".codex"
        assertions += 2

        empty = resolve_artifact(objective, environ={"CODEX_HOME": ""})
        assert empty.code == "invalid-runtime-root"
        assert empty.received["state"] == "empty"
        assertions += 2

        relative = resolve_artifact(objective, environ={"CODEX_HOME": "relative-root"})
        assert relative.code == "invalid-runtime-root"
        assert relative.received["state"] == "not-absolute"
        assertions += 2

        missing_root = resolve_artifact(
            objective,
            environ={"CODEX_HOME": str(base / "missing")},
        )
        assert missing_root.code == "invalid-runtime-root"
        assertions += 1

        root_file = base / "root-file"
        root_file.write_text("not a directory", encoding="utf-8")
        root_file_result = resolve_artifact(
            objective,
            environ={"CODEX_HOME": str(root_file)},
        )
        assert root_file_result.code == "invalid-runtime-root"
        assertions += 1

        nontext = resolve_artifact(None, environ={"CODEX_HOME": str(custom_root)})
        assert nontext.code == "objective-not-text"
        assertions += 1

        none = resolve_artifact("No managed path is named.", environ={"CODEX_HOME": str(custom_root)})
        assert none.code == "no-managed-artifact-reference" and none.candidate_count == 0
        assertions += 1

        second = make_artifact(custom_attachments, "second")
        ambiguous = resolve_artifact(
            f"Read {artifact} and {second}.",
            environ={"CODEX_HOME": str(custom_root)},
        )
        assert ambiguous.code == "ambiguous-managed-artifacts"
        assert ambiguous.candidate_count == 2
        assertions += 2

        other_root, other_attachments = make_root(base, "other")
        other_artifact = make_artifact(other_attachments, "other")
        mismatch = resolve_artifact(
            f"Read {other_artifact}.",
            environ={"CODEX_HOME": str(custom_root)},
        )
        assert mismatch.code == "attachments-root-mismatch"
        assert mismatch.expected != mismatch.received
        assertions += 2
        assert other_root != custom_root

        invalid_uuid = custom_attachments / "not-a-uuid" / "goal"
        invalid_uuid.parent.mkdir()
        invalid_uuid.write_text("invalid", encoding="utf-8")
        invalid = resolve_artifact(
            f"Read {invalid_uuid}.",
            environ={"CODEX_HOME": str(custom_root)},
        )
        assert invalid.code == "managed-path-shape"
        assertions += 1

        traversal = (
            f"{custom_attachments}/12345678-1234-1234-1234-123456789abc/../other/goal"
        )
        traversal_result = resolve_artifact(
            f"Read {traversal}.",
            environ={"CODEX_HOME": str(custom_root)},
        )
        assert traversal_result.code == "managed-path-shape"
        assertions += 1

        directory = custom_attachments / "12345678-1234-1234-1234-123456789abc" / "directory"
        directory.mkdir()
        not_file = resolve_artifact(
            f"Read {directory}.",
            environ={"CODEX_HOME": str(custom_root)},
        )
        assert not_file.code == "artifact-not-file"
        assertions += 1

        missing_artifact = (
            custom_attachments
            / "12345678-1234-1234-1234-123456789abc"
            / "missing"
        )
        missing_file = resolve_artifact(
            f"Read {missing_artifact}.",
            environ={"CODEX_HOME": str(custom_root)},
        )
        assert missing_file.code == "artifact-not-file"
        assertions += 1

        escape = (
            custom_attachments
            / "12345678-1234-1234-1234-123456789abc"
            / "escape"
        )
        escape.symlink_to(other_artifact)
        escaped = resolve_artifact(
            f"Read {escape}.",
            environ={"CODEX_HOME": str(custom_root)},
        )
        assert escaped.code == "attachments-root-mismatch"
        assertions += 1

        internal_link = (
            custom_attachments
            / "12345678-1234-1234-1234-123456789abc"
            / "internal-link"
        )
        internal_link.symlink_to(artifact.name)
        linked = resolve_artifact(
            f"Read {internal_link}.",
            environ={"CODEX_HOME": str(custom_root)},
        )
        assert linked.code == "artifact-not-file"
        assertions += 1

    return {"status": "passed", "assertions": assertions, "approach": APPROACH}


def parse_args() -> argparse.Namespace:
    """Parse the objective or packaged self-test request."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--objective")
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if not arguments.self_test and arguments.objective is None:
        parser.error("--objective is required unless --self-test is used")
    return arguments


def main() -> int:
    """Render one typed result without writing state or hook envelopes."""

    arguments = parse_args()
    if arguments.self_test:
        output: dict[str, Any] = self_test()
    else:
        output = resolve_artifact(arguments.objective).to_dict()
    print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if output["status"] in {"success", "passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
