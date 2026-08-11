#!/usr/bin/env python3
"""Run the generic damage renderer twice and require byte-identical outputs."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from damage_common import atomic_write_text, canonical_json, display_path, sha256_file


def parse_args() -> argparse.Namespace:
    """Parse the manifest, absent run root, and summary path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--renderer", type=Path, default=Path(__file__).with_name("render_damage_assessment.py"))
    return parser.parse_args()


def run_renderer(renderer: Path, manifest: Path, output_root: Path, run_name: str) -> dict[str, object]:
    """Execute one isolated render and retain its complete diagnostics."""
    run_root = output_root / run_name
    run_root.mkdir(parents=True)
    markdown = run_root / "detailed-damage-assessment.md"
    derived = run_root / "detailed-damage-assessment.json"
    command = [
        sys.executable,
        str(renderer),
        "--manifest",
        str(manifest),
        "--output-markdown",
        str(markdown),
        "--output-json",
        str(derived),
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    return {
        "name": run_name,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "markdown": display_path(markdown),
        "json": display_path(derived),
        "markdown_sha256": sha256_file(markdown) if markdown.is_file() else None,
        "json_sha256": sha256_file(derived) if derived.is_file() else None,
    }


def main() -> int:
    """Require successful byte-identical output from two absent-directory runs."""
    arguments = parse_args()
    manifest = arguments.manifest.expanduser().resolve(strict=True)
    renderer = arguments.renderer.expanduser().resolve(strict=True)
    output_root = arguments.output_root.expanduser()
    if output_root.exists():
        raise SystemExit(f"output root already exists: {display_path(output_root)}")
    output_root.mkdir(parents=True)
    runs = [run_renderer(renderer, manifest, output_root, name) for name in ("run-a", "run-b")]
    exits_ok = all(run["exit_code"] == 0 for run in runs)
    markdown_identical = exits_ok and runs[0]["markdown_sha256"] == runs[1]["markdown_sha256"]
    json_identical = exits_ok and runs[0]["json_sha256"] == runs[1]["json_sha256"]
    result = {
        "schema_version": 1,
        "manifest": {"path": display_path(manifest), "sha256": sha256_file(manifest)},
        "renderer": {"path": display_path(renderer), "sha256": sha256_file(renderer)},
        "runs": runs,
        "outputs_byte_identical": bool(markdown_identical and json_identical),
        "markdown_byte_identical": bool(markdown_identical),
        "json_byte_identical": bool(json_identical),
    }
    atomic_write_text(arguments.output.expanduser(), canonical_json(result))
    return 0 if result["outputs_byte_identical"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
