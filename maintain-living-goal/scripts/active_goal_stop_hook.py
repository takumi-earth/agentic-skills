#!/usr/bin/env python3
"""Request one anti-punting continuation before an active Codex goal turn ends."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Final


CONTINUATION_REASON: Final = (
    "An active harness goal still governs this thread. Before ending this same "
    "Codex turn, perform one substantive anti-punting audit against the full "
    "objective and current authoritative state. Continue every meaningful "
    "causally independent in-scope lane that the user has authorized; a pending "
    "review, decision, or stopped slice is not a whole-goal blocker while such "
    "work remains. Do not invent work, manufacture goal turns, or count this "
    "same-turn Stop retry as another turn in the three-turn blocked audit: it "
    "retains the same `turn_id`. If the objective appears satisfied, produce or "
    "strengthen a self-contained requirement-by-requirement candidate completion "
    "audit and leave the goal active for explicit user review. The user alone "
    "decides achievement; never call `update_goal(status: \"complete\")` from "
    "your own assessment."
)


def default_goals_database() -> Path:
    """Resolve the Codex goals database without binding the package to one home."""

    configured_home = os.environ.get("CODEX_HOME")
    if configured_home:
        return Path(configured_home).expanduser() / "goals_1.sqlite"
    return Path.home() / ".codex" / "goals_1.sqlite"


def read_goal_status(database_path: Path, session_id: str) -> str | None:
    """Read one thread status without creating or mutating the SQLite database."""

    try:
        database_uri = f"{database_path.resolve().as_uri()}?mode=ro"
        connection = sqlite3.connect(database_uri, uri=True, timeout=0.25)
        try:
            row = connection.execute(
                "SELECT status FROM thread_goals WHERE thread_id = ?",
                (session_id,),
            ).fetchone()
        finally:
            connection.close()
    except (OSError, RuntimeError, sqlite3.Error, ValueError):
        return None

    if row is None or not isinstance(row[0], str):
        return None
    return row[0]


def stop_hook_output(
    payload: object,
    database_path: Path | None = None,
) -> dict[str, str]:
    """Return one continuation decision only for an active goal's first Stop pass."""

    if not isinstance(payload, dict):
        return {}
    if payload.get("hook_event_name") != "Stop":
        return {}
    if payload.get("stop_hook_active") is not False:
        return {}

    session_id = payload.get("session_id")
    turn_id = payload.get("turn_id")
    if not isinstance(session_id, str) or not session_id.strip():
        return {}
    if not isinstance(turn_id, str) or not turn_id.strip():
        return {}

    selected_database = database_path or default_goals_database()
    if read_goal_status(selected_database, session_id.strip()) != "active":
        return {}

    return {"decision": "block", "reason": CONTINUATION_REASON}


def main() -> int:
    try:
        payload: Any = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        payload = None

    output = stop_hook_output(payload)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
