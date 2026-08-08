#!/usr/bin/env python3
"""Reconcile relative skill-package symlinks across local agent harnesses."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = 1
CONFIG_FILENAME = "agentic-skills.toml"
NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
CONFIG_TOP_LEVEL_KEYS = {"schema_version", "harness"}
HARNESS_KEYS = {
    "mode",
    "new_skills",
    "skills",
    "exclude_skills",
    "detect_dir",
    "skills_dir",
}


class InputError(Exception):
    """An invalid command, source root, or configuration input."""


class JsonArgumentParser(argparse.ArgumentParser):
    """Convert command-line syntax failures into structured input errors."""

    def error(self, message: str) -> None:
        """Raise instead of printing argparse's unstructured usage error."""

        raise InputError(f"command line: {message}")


@dataclass(frozen=True)
class UserDirectories:
    """Resolved user-owned directories used by discovery and configuration."""

    home: Path
    xdg_config_home: Path
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BuiltinHarness:
    """One built-in harness location relative to user directories."""

    name: str
    detect_dir: Path | None
    skills_dir: Path
    mode: str


@dataclass
class HarnessRoute:
    """One configured or default harness route."""

    name: str
    mode: str
    new_skills: str
    skills: set[str]
    exclude_skills: set[str]
    detect_dir: Path | None
    skills_dir: Path
    detect_value: str | None = None
    skills_value: str | None = None


@dataclass(frozen=True)
class ConfigLocation:
    """The active and preferred configuration paths for one invocation."""

    active: Path | None
    preferred: Path
    warnings: tuple[str, ...] = ()


@dataclass
class LoadedConfig:
    """A parsed authoritative config."""

    path: Path
    routes: dict[str, HarnessRoute]


@dataclass
class HarnessPlan:
    """A read-only plan for one harness destination."""

    route: HarnessRoute
    target_status: str
    physical_dir: Path | None
    actions: list[dict[str, Any]]
    had_failure: bool


def path_exists(path: Path) -> bool:
    """Return whether a path exists without following its final symlink."""

    return os.path.lexists(path)


def normalized_absolute(path: Path) -> Path:
    """Normalize an absolute path lexically without requiring it to exist."""

    return Path(os.path.abspath(os.path.normpath(os.fspath(path))))


def expand_user_path(value: str | Path, home: Path, label: str) -> Path:
    """Expand a portable `~` path against the selected user home."""

    raw = os.fspath(value)
    if raw == "~":
        path = home
    elif raw.startswith("~/") or raw.startswith("~\\"):
        path = home / raw[2:]
    elif raw.startswith("~"):
        raise InputError(f"{label} does not support another user's home: {raw!r}")
    else:
        path = Path(raw)
    if not path.is_absolute():
        raise InputError(f"{label} must be absolute or start with '~': {raw!r}")
    return normalized_absolute(path)


def resolve_cli_path(value: str | Path, home: Path, label: str) -> Path:
    """Resolve a CLI path, accepting `~`, absolute, and current-relative forms."""

    raw = os.fspath(value)
    if raw.startswith("~"):
        return expand_user_path(raw, home, label)
    path = Path(raw)
    if not path.is_absolute():
        path = Path.cwd() / path
    return normalized_absolute(path)


def resolve_user_directories(
    raw_home: str | Path | None, environ: Mapping[str, str] = os.environ
) -> UserDirectories:
    """Resolve the selected home and XDG config root deterministically."""

    try:
        if raw_home is None:
            home = Path.home().resolve()
        else:
            home = Path(raw_home).expanduser().resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise InputError(f"cannot resolve user home: {error}") from error
    if not home.is_dir():
        raise InputError(f"user home is not a directory: {home}")

    warnings: list[str] = []
    raw_xdg = environ.get("XDG_CONFIG_HOME")
    if raw_xdg:
        try:
            candidate = Path(raw_xdg).expanduser()
        except (OSError, RuntimeError) as error:
            raise InputError(
                f"cannot expand XDG_CONFIG_HOME {raw_xdg!r}: {error}"
            ) from error
        if candidate.is_absolute():
            xdg_config_home = normalized_absolute(candidate)
        else:
            warnings.append(
                f"ignoring non-absolute XDG_CONFIG_HOME {raw_xdg!r}; using {home / '.config'}"
            )
            xdg_config_home = home / ".config"
    else:
        xdg_config_home = home / ".config"
    return UserDirectories(
        home=normalized_absolute(home),
        xdg_config_home=normalized_absolute(xdg_config_home),
        warnings=tuple(warnings),
    )


def builtin_registry(user: UserDirectories) -> dict[str, BuiltinHarness]:
    """Return the built-in, user-level harness registry."""

    home = user.home
    xdg = user.xdg_config_home
    entries = (
        BuiltinHarness("agents", None, home / ".agents" / "skills", "always"),
        BuiltinHarness(
            "codex", home / ".codex", home / ".codex" / "skills", "detected"
        ),
        BuiltinHarness(
            "claude", home / ".claude", home / ".claude" / "skills", "detected"
        ),
        BuiltinHarness(
            "gemini", home / ".gemini", home / ".gemini" / "skills", "detected"
        ),
        BuiltinHarness("kiro", home / ".kiro", home / ".kiro" / "skills", "detected"),
        BuiltinHarness(
            "copilot", home / ".copilot", home / ".copilot" / "skills", "detected"
        ),
        BuiltinHarness(
            "cursor", home / ".cursor", home / ".cursor" / "skills", "detected"
        ),
        BuiltinHarness(
            "cline", home / ".cline", home / ".cline" / "skills", "detected"
        ),
        BuiltinHarness(
            "windsurf",
            home / ".codeium" / "windsurf",
            home / ".codeium" / "windsurf" / "skills",
            "detected",
        ),
        BuiltinHarness(
            "opencode",
            xdg / "opencode",
            xdg / "opencode" / "skills",
            "detected",
        ),
    )
    return {entry.name: entry for entry in entries}


def resolve_skills_root(raw: str | Path | None, home: Path) -> Path:
    """Resolve the flat directory whose immediate children are skill packages."""

    if raw is None:
        root = Path(__file__).resolve().parents[2]
    else:
        root = resolve_cli_path(raw, home, "skills root")
    try:
        resolved = root.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise InputError(f"cannot resolve skills root {root}: {error}") from error
    if not resolved.is_dir():
        raise InputError(f"skills root is not a directory: {resolved}")
    return resolved


def discover_skills(root: Path) -> dict[str, Path]:
    """Select deployable immediate children containing a root `SKILL.md`."""

    discovered: dict[str, Path] = {}
    try:
        children = sorted(root.iterdir(), key=lambda path: path.name)
    except OSError as error:
        raise InputError(f"cannot enumerate skills root {root}: {error}") from error
    for child in children:
        if child.name.startswith(".") or not child.is_dir():
            continue
        if not (child / "SKILL.md").is_file():
            continue
        if NAME_RE.fullmatch(child.name) is None:
            raise InputError(
                f"deployable skill directory is not lowercase hyphen-case: {child.name!r}"
            )
        discovered[child.name] = root / child.name
    return discovered


def locate_config(
    explicit: str | Path | None, user: UserDirectories, require_explicit: bool = False
) -> ConfigLocation:
    """Resolve an explicit config or apply XDG-over-home lookup precedence."""

    if explicit is not None:
        selected = resolve_cli_path(explicit, user.home, "config path")
        if require_explicit and not path_exists(selected):
            raise InputError(f"explicit config does not exist: {selected}")
        return ConfigLocation(
            active=selected if path_exists(selected) else None, preferred=selected
        )

    xdg_path = user.xdg_config_home / CONFIG_FILENAME
    home_path = user.home / CONFIG_FILENAME
    xdg_exists = path_exists(xdg_path)
    home_exists = path_exists(home_path)
    warnings: list[str] = []
    if xdg_exists:
        if home_exists and normalized_absolute(home_path) != normalized_absolute(
            xdg_path
        ):
            warnings.append(
                f"using XDG config {xdg_path}; ignoring fallback config {home_path}"
            )
        return ConfigLocation(
            active=xdg_path, preferred=xdg_path, warnings=tuple(warnings)
        )
    if home_exists:
        return ConfigLocation(active=home_path, preferred=xdg_path)
    return ConfigLocation(active=None, preferred=xdg_path)


def validate_name_list(value: Any, label: str) -> set[str]:
    """Validate and deduplicate a TOML array of skill names."""

    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise InputError(f"{label} must be an array of skill-name strings")
    invalid = sorted({item for item in value if NAME_RE.fullmatch(item) is None})
    if invalid:
        raise InputError(f"{label} contains invalid skill names: {', '.join(invalid)}")
    return set(value)


def optional_path_value(
    table: dict[str, Any], key: str, home: Path, label: str
) -> tuple[str | None, Path | None]:
    """Read one optional portable absolute path from a harness table."""

    if key not in table:
        return None, None
    raw = table[key]
    if not isinstance(raw, str) or not raw:
        raise InputError(f"{label}.{key} must be a non-empty path string")
    return raw, expand_user_path(raw, home, f"{label}.{key}")


def load_config(
    path: Path, user: UserDirectories, builtins: Mapping[str, BuiltinHarness]
) -> LoadedConfig:
    """Parse and strictly validate one authoritative TOML config."""

    if not path_exists(path):
        raise InputError(f"config does not exist: {path}")
    try:
        source_text = path.read_text(encoding="utf-8")
        document = tomllib.loads(source_text)
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise InputError(f"cannot read config {path}: {error}") from error
    if not isinstance(document, dict):
        raise InputError(f"config root must be a TOML table: {path}")
    unknown_top = sorted(set(document) - CONFIG_TOP_LEVEL_KEYS)
    if unknown_top:
        raise InputError(f"config has unknown top-level keys: {', '.join(unknown_top)}")
    version = document.get("schema_version")
    if isinstance(version, bool) or version != SCHEMA_VERSION:
        raise InputError(
            f"config schema_version must be integer {SCHEMA_VERSION}: {path}"
        )
    harness_tables = document.get("harness", {})
    if not isinstance(harness_tables, dict):
        raise InputError("config harness value must be a table")

    routes: dict[str, HarnessRoute] = {}
    for name in sorted(harness_tables):
        if NAME_RE.fullmatch(name) is None:
            raise InputError(f"invalid harness name: {name!r}")
        table = harness_tables[name]
        label = f"harness.{name}"
        if not isinstance(table, dict):
            raise InputError(f"{label} must be a table")
        unknown = sorted(set(table) - HARNESS_KEYS)
        if unknown:
            raise InputError(f"{label} has unknown keys: {', '.join(unknown)}")
        missing = sorted({"mode", "new_skills", "skills"} - set(table))
        if missing:
            raise InputError(f"{label} is missing required keys: {', '.join(missing)}")

        mode = table["mode"]
        if not isinstance(mode, str) or mode not in {"always", "detected"}:
            raise InputError(f"{label}.mode must be 'always' or 'detected'")
        new_skills = table["new_skills"]
        if not isinstance(new_skills, str) or new_skills not in {"link", "ignore"}:
            raise InputError(f"{label}.new_skills must be 'link' or 'ignore'")
        skills = validate_name_list(table["skills"], f"{label}.skills")
        exclusions = validate_name_list(
            table.get("exclude_skills", []), f"{label}.exclude_skills"
        )
        detect_value, configured_detect = optional_path_value(
            table, "detect_dir", user.home, label
        )
        skills_value, configured_skills = optional_path_value(
            table, "skills_dir", user.home, label
        )

        builtin = builtins.get(name)
        if builtin is None and configured_skills is None:
            raise InputError(f"custom {label} requires skills_dir")
        skills_dir = configured_skills or builtin.skills_dir  # type: ignore[union-attr]
        detect_dir = configured_detect or (builtin.detect_dir if builtin else None)
        if mode == "detected" and detect_dir is None:
            raise InputError(f"{label} in detected mode requires detect_dir")
        route = HarnessRoute(
            name=name,
            mode=mode,
            new_skills=new_skills,
            skills=skills,
            exclude_skills=exclusions,
            detect_dir=detect_dir,
            skills_dir=skills_dir,
            detect_value=detect_value,
            skills_value=skills_value,
        )
        routes[name] = route

    validate_unique_destinations(routes)
    return LoadedConfig(path=path, routes=routes)


def validate_unique_destinations(routes: Mapping[str, HarnessRoute]) -> None:
    """Reject harness routes that normalize to one destination directory."""

    owners: dict[Path, str] = {}
    for name, route in sorted(routes.items()):
        try:
            destination = route.skills_dir.resolve(strict=False)
        except (OSError, RuntimeError) as error:
            raise InputError(
                f"cannot normalize harness.{name}.skills_dir {route.skills_dir}: {error}"
            ) from error
        previous = owners.get(destination)
        if previous is not None:
            raise InputError(
                f"harnesses {previous!r} and {name!r} share skills_dir {destination}"
            )
        owners[destination] = name


def validate_destination_safety(
    routes: Mapping[str, HarnessRoute], skills_root: Path, home: Path
) -> None:
    """Reject broad or source-overlapping destinations before reconciliation."""

    source = skills_root.resolve(strict=True)
    selected_home = home.resolve(strict=True)
    for name, route in sorted(routes.items()):
        try:
            destination = route.skills_dir.resolve(strict=False)
        except (OSError, RuntimeError) as error:
            raise InputError(
                f"cannot normalize harness.{name}.skills_dir {route.skills_dir}: {error}"
            ) from error
        filesystem_root = Path(destination.anchor)
        if destination == filesystem_root:
            raise InputError(
                f"harness.{name}.skills_dir cannot be a filesystem root: {destination}"
            )
        if destination == selected_home:
            raise InputError(
                f"harness.{name}.skills_dir cannot be the selected user home: {destination}"
            )
        if (
            destination == source
            or destination.is_relative_to(source)
            or source.is_relative_to(destination)
        ):
            raise InputError(
                f"harness.{name}.skills_dir overlaps skills root {source}: {destination}"
            )


def default_routes(
    builtins: Mapping[str, BuiltinHarness], skill_names: set[str]
) -> dict[str, HarnessRoute]:
    """Build no-config routes for every built-in harness."""

    return {
        name: HarnessRoute(
            name=name,
            mode=builtin.mode,
            new_skills="link",
            skills=set(skill_names),
            exclude_skills=set(),
            detect_dir=builtin.detect_dir,
            skills_dir=builtin.skills_dir,
        )
        for name, builtin in sorted(builtins.items())
    }


def reconcile_config_routes(
    config: LoadedConfig, current_skills: set[str]
) -> tuple[bool, list[dict[str, Any]]]:
    """Apply per-harness new, excluded, and stale skill policy in memory."""

    changes: list[dict[str, Any]] = []
    semantic_changed = False
    for name, route in sorted(config.routes.items()):
        before_skills = set(route.skills)
        before_exclusions = set(route.exclude_skills)
        route.skills.intersection_update(current_skills)
        route.exclude_skills.intersection_update(current_skills)
        route.skills.difference_update(route.exclude_skills)
        if route.new_skills == "link":
            route.skills.update(current_skills - route.exclude_skills)

        added = sorted(route.skills - before_skills)
        removed = sorted(before_skills - route.skills)
        removed_exclusions = sorted(before_exclusions - route.exclude_skills)
        if added or removed or removed_exclusions:
            semantic_changed = True
            changes.append(
                {
                    "harness": name,
                    "added_skills": added,
                    "removed_skills": removed,
                    "removed_exclusions": removed_exclusions,
                }
            )
    return semantic_changed, changes


def toml_string(value: str) -> str:
    """Encode a string using JSON-compatible TOML basic-string syntax."""

    return json.dumps(value, ensure_ascii=False)


def toml_array(key: str, values: set[str]) -> list[str]:
    """Serialize one deterministic array of skill names."""

    if not values:
        return [f"{key} = []"]
    lines = [f"{key} = ["]
    lines.extend(f"  {toml_string(value)}," for value in sorted(values))
    lines.append("]")
    return lines


def serialize_config(routes: Mapping[str, HarnessRoute]) -> str:
    """Serialize the supported config schema canonically."""

    lines = [f"schema_version = {SCHEMA_VERSION}"]
    for name, route in sorted(routes.items()):
        lines.extend(["", f"[harness.{name}]", f"mode = {toml_string(route.mode)}"])
        if route.detect_value is not None:
            lines.append(f"detect_dir = {toml_string(route.detect_value)}")
        if route.skills_value is not None:
            lines.append(f"skills_dir = {toml_string(route.skills_value)}")
        lines.append(f"new_skills = {toml_string(route.new_skills)}")
        lines.extend(toml_array("skills", route.skills))
        lines.extend(toml_array("exclude_skills", route.exclude_skills))
    return "\n".join(lines) + "\n"


def atomic_write(path: Path, content: str) -> None:
    """Atomically write UTF-8 text while preserving a config symlink and mode."""

    output = path
    if path.is_symlink():
        try:
            output = path.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise OSError(f"cannot resolve config symlink {path}: {error}") from error
    output.parent.mkdir(parents=True, exist_ok=True)
    previous_mode: int | None = None
    if output.exists():
        previous_mode = stat.S_IMODE(output.stat().st_mode)

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if previous_mode is not None:
            os.chmod(temporary_name, previous_mode)
        os.replace(temporary_name, output)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass


def harness_is_detected(route: HarnessRoute) -> bool:
    """Return whether a route is currently installed or explicitly always active."""

    if route.mode == "always":
        return True
    if path_exists(route.skills_dir):
        return True
    return route.detect_dir is not None and route.detect_dir.is_dir()


def init_routes(
    builtins: Mapping[str, BuiltinHarness], skill_names: set[str]
) -> dict[str, HarnessRoute]:
    """Seed config routes for `agents` and currently discovered built-ins."""

    routes: dict[str, HarnessRoute] = {}
    for name, builtin in sorted(builtins.items()):
        route = HarnessRoute(
            name=name,
            mode=builtin.mode,
            new_skills="link",
            skills=set(skill_names),
            exclude_skills=set(),
            detect_dir=builtin.detect_dir,
            skills_dir=builtin.skills_dir,
        )
        if harness_is_detected(route):
            routes[name] = route
    return routes


def ensure_target(
    route: HarnessRoute, dry_run: bool
) -> tuple[str, Path | None, str | None]:
    """Resolve, create, skip, or reject one harness skills directory."""

    if path_exists(route.skills_dir):
        if not route.skills_dir.is_dir():
            return "error", None, f"skills_dir is not a directory: {route.skills_dir}"
        try:
            return "active", route.skills_dir.resolve(strict=True), None
        except (OSError, RuntimeError) as error:
            return (
                "error",
                None,
                f"cannot resolve skills_dir {route.skills_dir}: {error}",
            )

    if route.mode == "detected":
        assert route.detect_dir is not None
        if not path_exists(route.detect_dir):
            return "skipped", None, None
        if not route.detect_dir.is_dir():
            return "error", None, f"detect_dir is not a directory: {route.detect_dir}"

    try:
        physical = route.skills_dir.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        return "error", None, f"cannot resolve skills_dir {route.skills_dir}: {error}"
    if dry_run:
        return "would-create", physical, None
    try:
        route.skills_dir.mkdir(parents=True, exist_ok=False)
        return "created", route.skills_dir.resolve(strict=True), None
    except OSError as error:
        return "error", None, f"cannot create skills_dir {route.skills_dir}: {error}"


def relative_link_destination(parent: Path, target: str) -> Path:
    """Resolve a relative link target lexically from its physical parent."""

    return normalized_absolute(parent / target)


def expected_package_path(skills_root: Path, name: str) -> Path:
    """Return the same-named lexical package path owned by this repository."""

    return normalized_absolute(skills_root / name)


def owned_relative_link(link: Path, physical_parent: Path, skills_root: Path) -> bool:
    """Return whether a link lexically targets this root's same-named package."""

    if not link.is_symlink():
        return False
    try:
        target = os.readlink(link)
    except OSError:
        return False
    if os.path.isabs(target):
        return False
    return relative_link_destination(physical_parent, target) == expected_package_path(
        skills_root, link.name
    )


def reconcile_target(
    route: HarnessRoute,
    physical_dir: Path,
    skills_root: Path,
    source_skills: Mapping[str, Path],
    dry_run: bool,
) -> tuple[list[dict[str, Any]], bool]:
    """Prune owned undesired links and converge desired package links."""

    actions: list[dict[str, Any]] = []
    had_failure = False
    desired = set(route.skills)

    if dry_run and not path_exists(route.skills_dir):
        existing: list[Path] = []
    else:
        try:
            existing = sorted(route.skills_dir.iterdir(), key=lambda path: path.name)
        except OSError as error:
            return (
                [
                    {
                        "action": "error",
                        "message": f"cannot scan {route.skills_dir}: {error}",
                    }
                ],
                True,
            )

    for entry in existing:
        if entry.name in desired:
            continue
        if not owned_relative_link(entry, physical_dir, skills_root):
            continue
        action = "would-remove" if dry_run else "removed"
        if not dry_run:
            try:
                entry.unlink()
            except OSError as error:
                actions.append(
                    {"action": "error", "skill": entry.name, "message": str(error)}
                )
                had_failure = True
                continue
        actions.append({"action": action, "skill": entry.name})

    for name in sorted(desired):
        source = source_skills.get(name)
        if source is None:
            actions.append(
                {
                    "action": "error",
                    "skill": name,
                    "message": "source skill is unavailable",
                }
            )
            had_failure = True
            continue
        destination = route.skills_dir / name
        if path_exists(destination):
            if destination.is_symlink():
                try:
                    target = os.readlink(destination)
                except OSError as error:
                    actions.append(
                        {"action": "error", "skill": name, "message": str(error)}
                    )
                    had_failure = True
                    continue
                if not os.path.isabs(target) and relative_link_destination(
                    physical_dir, target
                ) == expected_package_path(skills_root, name):
                    actions.append(
                        {"action": "unchanged", "skill": name, "target": target}
                    )
                else:
                    actions.append(
                        {
                            "action": "conflict",
                            "skill": name,
                            "kind": "absolute-symlink"
                            if os.path.isabs(target)
                            else "wrong-symlink",
                            "target": target,
                        }
                    )
                    had_failure = True
            else:
                actions.append(
                    {
                        "action": "conflict",
                        "skill": name,
                        "kind": "directory"
                        if destination.is_dir()
                        else "file-or-special",
                    }
                )
                had_failure = True
            continue

        try:
            target = os.path.relpath(source, start=physical_dir)
        except ValueError as error:
            actions.append(
                {
                    "action": "error",
                    "skill": name,
                    "message": f"cannot create a cross-volume relative link: {error}",
                }
            )
            had_failure = True
            continue
        action = "would-create" if dry_run else "created"
        if not dry_run:
            try:
                os.symlink(target, destination, target_is_directory=True)
            except OSError as error:
                actions.append(
                    {
                        "action": "error",
                        "skill": name,
                        "message": f"cannot create relative directory symlink: {error}",
                    }
                )
                had_failure = True
                continue
        actions.append({"action": action, "skill": name, "target": target})
    return actions, had_failure


def build_harness_plans(
    routes: Mapping[str, HarnessRoute],
    skills_root: Path,
    source_skills: Mapping[str, Path],
) -> list[HarnessPlan]:
    """Inspect every route and link action without changing the filesystem."""

    plans: list[HarnessPlan] = []
    for _, route in sorted(routes.items()):
        target_status, physical_dir, error = ensure_target(route, dry_run=True)
        if target_status == "skipped":
            actions: list[dict[str, Any]] = []
            had_failure = False
        elif target_status == "error":
            actions = [{"action": "error", "message": error}]
            had_failure = True
        else:
            assert physical_dir is not None
            actions, had_failure = reconcile_target(
                route,
                physical_dir,
                skills_root,
                source_skills,
                dry_run=True,
            )
        plans.append(
            HarnessPlan(
                route=route,
                target_status=target_status,
                physical_dir=physical_dir,
                actions=actions,
                had_failure=had_failure,
            )
        )
    return plans


def harness_report(
    route: HarnessRoute,
    target_status: str,
    actions: list[dict[str, Any]],
    had_failure: bool,
) -> dict[str, Any]:
    """Build one stable per-harness JSON object."""

    if target_status == "skipped":
        status = "skipped"
    elif target_status == "error":
        status = "error"
    else:
        status = "partial" if had_failure else "converged"
    return {
        "name": route.name,
        "mode": route.mode,
        "detect_dir": str(route.detect_dir) if route.detect_dir else None,
        "skills_dir": str(route.skills_dir),
        "selected_skills": sorted(route.skills),
        "target_status": target_status,
        "status": status,
        "actions": actions,
    }


def planned_harness_report(plan: HarnessPlan) -> dict[str, Any]:
    """Render a read-only harness plan."""

    return harness_report(
        plan.route,
        plan.target_status,
        plan.actions,
        plan.had_failure,
    )


def apply_harness_plan(
    plan: HarnessPlan,
    skills_root: Path,
    source_skills: Mapping[str, Path],
) -> tuple[dict[str, Any], bool]:
    """Apply one prebuilt plan while rechecking its destination state."""

    if plan.target_status in {"skipped", "error"}:
        return planned_harness_report(plan), plan.had_failure

    target_status, physical_dir, error = ensure_target(plan.route, dry_run=False)
    if target_status == "skipped":
        return harness_report(plan.route, target_status, [], False), False
    if target_status == "error":
        actions = [{"action": "error", "message": error}]
        return harness_report(plan.route, target_status, actions, True), True

    assert physical_dir is not None
    actions, had_failure = reconcile_target(
        plan.route,
        physical_dir,
        skills_root,
        source_skills,
        dry_run=False,
    )
    return (
        harness_report(plan.route, target_status, actions, had_failure),
        had_failure,
    )


def summarize(harnesses: Sequence[dict[str, Any]]) -> dict[str, int]:
    """Count harness and action outcomes for one JSON report."""

    summary = {
        "harnesses": len(harnesses),
        "skipped_harnesses": 0,
        "created": 0,
        "would_create": 0,
        "unchanged": 0,
        "removed": 0,
        "would_remove": 0,
        "conflicts": 0,
        "errors": 0,
    }
    for harness in harnesses:
        if harness["status"] == "skipped":
            summary["skipped_harnesses"] += 1
        for action in harness.get("actions", []):
            kind = action["action"]
            if kind == "created":
                summary["created"] += 1
            elif kind == "would-create":
                summary["would_create"] += 1
            elif kind == "unchanged":
                summary["unchanged"] += 1
            elif kind == "removed":
                summary["removed"] += 1
            elif kind == "would-remove":
                summary["would_remove"] += 1
            elif kind == "conflict":
                summary["conflicts"] += 1
            elif kind == "error":
                summary["errors"] += 1
    return summary


def collect_issues(
    harnesses: Sequence[dict[str, Any]],
    extra_errors: Sequence[dict[str, Any]] = (),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Aggregate per-harness conflicts and errors for machine consumers."""

    conflicts: list[dict[str, Any]] = []
    errors = [dict(error) for error in extra_errors]
    for harness in harnesses:
        for action in harness.get("actions", []):
            kind = action.get("action")
            if kind not in {"conflict", "error"}:
                continue
            issue = {
                "harness": harness["name"],
                "skills_dir": harness["skills_dir"],
                **action,
            }
            if kind == "conflict":
                conflicts.append(issue)
            else:
                errors.append(issue)
    return conflicts, errors


def finalize_sync_report(
    report: dict[str, Any],
    harnesses: list[dict[str, Any]],
    extra_errors: Sequence[dict[str, Any]] = (),
) -> None:
    """Attach complete harness, issue, and count results to a sync report."""

    report["harnesses"] = harnesses
    conflicts, errors = collect_issues(harnesses, extra_errors)
    report["conflicts"] = conflicts
    report["errors"] = errors
    report["summary"] = summarize(harnesses)
    report["summary"]["errors"] += len(extra_errors)


def run_sync(
    args: argparse.Namespace, environ: Mapping[str, str]
) -> tuple[dict[str, Any], int]:
    """Execute or preview one complete sync operation."""

    user = resolve_user_directories(args.home, environ)
    skills_root = resolve_skills_root(args.skills_root, user.home)
    source_skills = discover_skills(skills_root)
    skill_names = set(source_skills)
    builtins = builtin_registry(user)
    location = locate_config(
        args.config, user, require_explicit=args.config is not None
    )
    warnings = [*user.warnings, *location.warnings]

    loaded: LoadedConfig | None = None
    config_changes: list[dict[str, Any]] = []
    config_semantic_change = False
    if location.active is None:
        routes = default_routes(builtins, skill_names)
        config_report: dict[str, Any] = {
            "mode": "defaults",
            "path": None,
            "update_required": False,
            "updated": False,
            "write_status": "not-applicable",
        }
    else:
        loaded = load_config(location.active, user, builtins)
        routes = loaded.routes
        config_semantic_change, config_changes = reconcile_config_routes(
            loaded, skill_names
        )
        config_report = {
            "mode": "authoritative",
            "path": str(loaded.path),
            "update_required": config_semantic_change,
            "updated": False,
            "write_status": (
                "would-update"
                if config_semantic_change and args.dry_run
                else "pending"
                if config_semantic_change
                else "unchanged"
            ),
            "changes": config_changes,
        }
    validate_unique_destinations(routes)
    validate_destination_safety(routes, skills_root, user.home)
    canonical_config = serialize_config(routes) if loaded is not None else None
    plans = build_harness_plans(routes, skills_root, source_skills)
    planned_reports = [planned_harness_report(plan) for plan in plans]
    planning_failed = any(plan.had_failure for plan in plans)

    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "operation": "sync",
        "dry_run": bool(args.dry_run),
        "applied": False,
        "source_root": str(skills_root),
        "source_skills": sorted(skill_names),
        "config": config_report,
        "warnings": warnings,
        "harnesses": planned_reports,
        "conflicts": [],
        "errors": [],
    }

    if args.dry_run:
        finalize_sync_report(report, planned_reports)
        return report, 1 if planning_failed else 0

    if loaded is not None and config_semantic_change and not args.dry_run:
        assert canonical_config is not None
        try:
            atomic_write(loaded.path, canonical_config)
        except OSError as error:
            config_report["write_status"] = "error"
            config_report["error"] = str(error)
            config_error = {
                "scope": "config",
                "path": str(loaded.path),
                "message": str(error),
            }
            finalize_sync_report(report, planned_reports, [config_error])
            return report, 1
        config_report["updated"] = True
        config_report["write_status"] = "updated"

    had_failure = False
    harness_reports: list[dict[str, Any]] = []
    for plan in plans:
        applied_report, failed = apply_harness_plan(plan, skills_root, source_skills)
        harness_reports.append(applied_report)
        had_failure = had_failure or failed

    report["applied"] = True
    finalize_sync_report(report, harness_reports)
    return report, 1 if had_failure else 0


def run_init_config(
    args: argparse.Namespace, environ: Mapping[str, str]
) -> tuple[dict[str, Any], int]:
    """Create or preview a canonical config seeded from current discovery."""

    user = resolve_user_directories(args.home, environ)
    skills_root = resolve_skills_root(args.skills_root, user.home)
    source_skills = discover_skills(skills_root)
    builtins = builtin_registry(user)
    location = locate_config(args.config, user)
    warnings = [*user.warnings, *location.warnings]
    output = location.preferred
    if location.active is not None:
        raise InputError(f"refusing to overwrite existing config: {location.active}")
    routes = init_routes(builtins, set(source_skills))
    content = serialize_config(routes)
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "operation": "init-config",
        "dry_run": bool(args.dry_run),
        "applied": False,
        "source_root": str(skills_root),
        "source_skills": sorted(source_skills),
        "config": {
            "path": str(output),
            "status": "would-create" if args.dry_run else "created",
            "harnesses": sorted(routes),
            "content": content if args.dry_run else None,
        },
        "warnings": warnings,
        "conflicts": [],
        "errors": [],
        "summary": {
            "harnesses": len(routes),
            "source_skills": len(source_skills),
            "configs_created": 0,
            "configs_planned": 1 if args.dry_run else 0,
            "errors": 0,
        },
    }
    if not args.dry_run:
        try:
            atomic_write(output, content)
        except OSError as error:
            report["config"]["status"] = "error"
            report["config"]["error"] = str(error)
            report["errors"] = [
                {"scope": "config", "path": str(output), "message": str(error)}
            ]
            report["summary"]["errors"] = 1
            return report, 1
        report["applied"] = True
        report["summary"]["configs_created"] = 1
    return report, 0


def build_parser() -> argparse.ArgumentParser:
    """Build the non-interactive command-line interface."""

    parser = JsonArgumentParser(
        description=(
            "Create and reconcile relative links from a flat Agent Skills repository "
            "into local harness skill directories."
        )
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for name, help_text in (
        (
            "init-config",
            "Create a canonical config for currently discovered harnesses.",
        ),
        ("sync", "Reconcile configured or discovered harness skill links."),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument(
            "--skills-root",
            help="Flat source directory containing immediate skill-package children.",
        )
        command.add_argument(
            "--home",
            help="User home used for harness paths; defaults to Path.home().",
        )
        command.add_argument(
            "--config",
            help=(
                "Explicit agentic-skills.toml path. Sync requires it to exist; "
                "init-config refuses to overwrite it."
            ),
        )
        command.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the complete plan without changing config, directories, or links.",
        )
    return parser


def emit_report(report: dict[str, Any]) -> None:
    """Write one stable JSON document to stdout."""

    json.dump(report, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def emit_diagnostics(report: Mapping[str, Any]) -> None:
    """Write warnings and non-successful operation details to stderr."""

    for warning in report.get("warnings", []):
        print(f"Warning: {warning}", file=sys.stderr)
    config = report.get("config", {})
    if isinstance(config, Mapping) and config.get("error"):
        print(f"Error: config: {config['error']}", file=sys.stderr)
    for harness in report.get("harnesses", []):
        if not isinstance(harness, Mapping):
            continue
        harness_name = harness.get("name", "unknown")
        for action in harness.get("actions", []):
            if not isinstance(action, Mapping):
                continue
            kind = action.get("action")
            if kind not in {"conflict", "error"}:
                continue
            skill = action.get("skill")
            subject = f"{harness_name}/{skill}" if skill else str(harness_name)
            detail = action.get("message") or action.get("kind") or kind
            print(f"Error: {subject}: {detail}", file=sys.stderr)


def main(
    argv: Sequence[str] | None = None, environ: Mapping[str, str] = os.environ
) -> int:
    """Run the selected operation and return a documented process status."""

    parser = build_parser()
    args: argparse.Namespace | None = None
    try:
        args = parser.parse_args(argv)
        if args.operation == "sync":
            report, status = run_sync(args, environ)
        else:
            report, status = run_init_config(args, environ)
    except InputError as error:
        print(f"Error: {error}", file=sys.stderr)
        raw_arguments = list(argv) if argv is not None else sys.argv[1:]
        operation = args.operation if args is not None else None
        if operation is None and raw_arguments:
            operation = (
                raw_arguments[0]
                if raw_arguments[0] in {"sync", "init-config"}
                else None
            )
        emit_report(
            {
                "schema_version": SCHEMA_VERSION,
                "operation": operation,
                "status": "invalid-input",
                "error": str(error),
                "conflicts": [],
                "errors": [{"scope": "input", "message": str(error)}],
                "summary": {"conflicts": 0, "errors": 1},
            }
        )
        return 2
    emit_diagnostics(report)
    emit_report(report)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
