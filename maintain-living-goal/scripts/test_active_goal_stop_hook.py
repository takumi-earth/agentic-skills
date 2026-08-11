#!/usr/bin/env python3
"""Focused tests for the active-goal Codex Stop hook."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import active_goal_stop_hook


HOOK = Path(active_goal_stop_hook.__file__).resolve()
THREAD_ID = "019fe135-c7db-7872-bf57-e26e7c30a4ad"
TURN_ID = "turn-1"


def stop_payload(**changes: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "cwd": "/workspace",
        "hook_event_name": "Stop",
        "last_assistant_message": "candidate response",
        "model": "test-model",
        "permission_mode": "default",
        "session_id": THREAD_ID,
        "stop_hook_active": False,
        "transcript_path": None,
        "turn_id": TURN_ID,
    }
    payload.update(changes)
    return payload


def create_goals_database(root: Path, rows: list[tuple[str, str]]) -> Path:
    database_path = root / "goals_1.sqlite"
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            "CREATE TABLE thread_goals ("
            "thread_id TEXT PRIMARY KEY NOT NULL, "
            "status TEXT NOT NULL"
            ")"
        )
        connection.executemany(
            "INSERT INTO thread_goals(thread_id, status) VALUES (?, ?)",
            rows,
        )
        connection.commit()
    finally:
        connection.close()
    return database_path


class StopDecisionTests(unittest.TestCase):
    def test_active_goal_requests_one_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database_path = create_goals_database(
                Path(temporary),
                [(THREAD_ID, "active")],
            )

            output = active_goal_stop_hook.stop_hook_output(
                stop_payload(),
                database_path,
            )

        self.assertEqual(
            output,
            {
                "decision": "block",
                "reason": active_goal_stop_hook.CONTINUATION_REASON,
            },
        )
        for required_text in (
            "explicitly required",
            "current user-specified explicit objective",
            "literal user instruction",
            "provenance that traces to the actual user instruction",
            "an assistant-authored provenance label is not sufficient",
            "Agent-authored goal objectives",
            "derived work grant no authority",
            "already authorized",
            "grants no authority",
            "Do not create or strengthen evidence",
            "are not independent lanes",
            "make no tool call",
            "state that boundary once",
            "same-turn retry",
            "goal active",
            "The user alone decides achievement",
            '`update_goal(status: "complete")`',
        ):
            self.assertIn(required_text, output["reason"])
        for forbidden_text in (
            "perform one substantive anti-punting audit",
            "Continue every meaningful",
            "produce or strengthen a self-contained",
            "required by the current objective",
        ):
            self.assertNotIn(forbidden_text, output["reason"])

    def test_recursive_stop_pass_is_a_noop(self) -> None:
        output = active_goal_stop_hook.stop_hook_output(
            stop_payload(stop_hook_active=True),
            Path("/database/must-not-be-read"),
        )

        self.assertEqual(output, {})

    def test_every_non_active_status_is_a_noop(self) -> None:
        for status in (
            "paused",
            "blocked",
            "usage_limited",
            "budget_limited",
            "complete",
        ):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temporary:
                database_path = create_goals_database(
                    Path(temporary),
                    [(THREAD_ID, status)],
                )

                output = active_goal_stop_hook.stop_hook_output(
                    stop_payload(),
                    database_path,
                )

                self.assertEqual(output, {})

    def test_other_thread_does_not_activate_this_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database_path = create_goals_database(
                Path(temporary),
                [("another-thread", "active")],
            )

            output = active_goal_stop_hook.stop_hook_output(
                stop_payload(),
                database_path,
            )

        self.assertEqual(output, {})

    def test_malformed_or_non_stop_inputs_are_noops(self) -> None:
        malformed_payloads: tuple[object, ...] = (
            None,
            [],
            {},
            stop_payload(hook_event_name="PostToolUse"),
            stop_payload(session_id=""),
            stop_payload(turn_id=""),
            stop_payload(stop_hook_active="false"),
        )
        for payload in malformed_payloads:
            with self.subTest(payload=payload):
                self.assertEqual(
                    active_goal_stop_hook.stop_hook_output(
                        payload,
                        Path("/database/must-not-be-read"),
                    ),
                    {},
                )

    def test_missing_or_invalid_database_is_a_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            temporary_path = Path(temporary)
            missing_database = temporary_path / "missing.sqlite"
            invalid_database = temporary_path / "invalid.sqlite"
            invalid_database.write_text("not sqlite", encoding="utf-8")

            self.assertEqual(
                active_goal_stop_hook.stop_hook_output(
                    stop_payload(),
                    missing_database,
                ),
                {},
            )
            self.assertEqual(
                active_goal_stop_hook.stop_hook_output(
                    stop_payload(),
                    invalid_database,
                ),
                {},
            )
            self.assertFalse(missing_database.exists())


class HookProcessTests(unittest.TestCase):
    def run_hook(
        self,
        input_text: str,
        codex_home: Path,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(codex_home)
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
            env=environment,
        )

    def test_executable_path_emits_schema_exact_json_without_mutating_database(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            database_path = create_goals_database(
                codex_home,
                [(THREAD_ID, "active")],
            )
            database_before = database_path.read_bytes()

            result = self.run_hook(json.dumps(stop_payload()), codex_home)

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            self.assertEqual(
                json.loads(result.stdout),
                {
                    "decision": "block",
                    "reason": active_goal_stop_hook.CONTINUATION_REASON,
                },
            )
            self.assertEqual(database_path.read_bytes(), database_before)
            self.assertFalse(Path(f"{database_path}-journal").exists())

    def test_malformed_json_fails_open_with_an_empty_object(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self.run_hook("{not-json", Path(temporary))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "{}\n")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
