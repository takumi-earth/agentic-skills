"""Observe literal nested goal calls without evaluating JavaScript or goal state."""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass
import json
import re
from typing import Any, Callable


_LEXEME = re.compile(
    r"(?P<space>\s+)|(?P<comment>//[^\r\n\u2028\u2029]*|/\*[\s\S]*?\*/)"
    r"|(?P<string>\"(?:\\[\s\S]|[^\"\\])*\"|'(?:\\[\s\S]|[^'\\])*')"
    r"|(?P<template>`(?:\\[\s\S]|[^`\\])*`)"
    r"|(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)"
    r"|(?P<number>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    r"|(?P<punct>[{}\[\]().,:;=+*?!<>|&%~-])"
)
_PAIRS = {"(": ")", "[": "]", "{": "}"}
_Output = tuple[int, str, dict[str, Any] | None]


class UnsupportedSyntax(ValueError):
    """Identify a source shape outside the deliberately bounded grammar."""


@dataclass(frozen=True)
class _Token:
    kind: str
    text: str
    offset: int


def _tokens(source: str) -> list[_Token]:
    result = []
    cursor = 0
    while cursor < len(source):
        match = _LEXEME.match(source, cursor)
        if match is None:
            raise UnsupportedSyntax(f"unsupported lexical syntax at input offset {cursor}")
        kind = match.lastgroup
        text = match.group()
        if kind == "template" and "${" in text:
            raise UnsupportedSyntax("template interpolation is outside the inspected grammar")
        if kind not in {"space", "comment"}:
            result.append(_Token(str(kind), text, cursor))
        cursor = match.end()
    return result


def _call_end(tokens: list[_Token], opening: int) -> int:
    stack: list[str] = []
    for index in range(opening, len(tokens)):
        token = tokens[index].text
        if token in _PAIRS:
            stack.append(_PAIRS[token])
        elif token in _PAIRS.values():
            if not stack or token != stack.pop():
                raise UnsupportedSyntax("unbalanced call delimiters")
            if not stack:
                return index + 1
    raise UnsupportedSyntax("unterminated call")


def _quoted_value(raw: str) -> str:
    # Accept common JS/Python string escapes, never Python-only named/octal escapes.
    if re.search(r"\\(?![\\'\"/bfnrtv]|0(?!\d)|x[0-9a-fA-F]{2}|u[0-9a-fA-F]{4}|\r?\n)", raw):
        raise UnsupportedSyntax("unsupported string escape")
    return ast.literal_eval(raw.replace("\\/", "/"))


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise UnsupportedSyntax("duplicate literal object property")
        result[key] = value
    return result


def _literal_status(tokens: list[_Token]) -> str:
    fragments = []
    for index, token in enumerate(tokens):
        following = tokens[index + 1].text if index + 1 < len(tokens) else ""
        if token.kind == "string":
            fragments.append(json.dumps(_quoted_value(token.text)))
        elif token.kind == "name" and following == ":":
            fragments.append(json.dumps(token.text))
        elif token.kind == "number" or token.text in {"true", "false", "null"}:
            fragments.append(token.text)
        elif token.text == "," and following in {"}", "]"}:
            continue
        elif token.text in {"{", "}", "[", "]", ":", ",", "-"}:
            fragments.append(token.text)
        else:
            raise UnsupportedSyntax("goal arguments are not a literal object")
    value = json.loads("".join(fragments), object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or value.get("status") not in ("complete", "blocked"):
        raise UnsupportedSyntax("expected a literal complete or blocked status property")
    return value["status"]


def _forwards_result(tokens: list[_Token], start: int, end: int) -> bool:
    """Recognize only a single direct result-emitting expression or const binding."""
    prefix = [token.text for token in tokens[:start]]
    suffix = [token.text for token in tokens[end:]]
    if suffix and suffix[-1] == ";":
        suffix.pop()
    if prefix == ["text", "(", "await"] and suffix == [")"]:
        return True
    if len(prefix) != 4 or prefix[0] != "const" or prefix[2:] != ["=", "await"]:
        return False
    name = prefix[1]
    return (
        tokens[1].kind == "name"
        and name not in {"tools", "text"}
        and suffix == [";", "text", "(", name, ")"]
    )


def _scan(source: str) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        tokens = _tokens(source)
    except UnsupportedSyntax as error:
        return [], [str(error)]
    sites = []
    issues = []
    for start in range(len(tokens) - 3):
        if [item.text for item in tokens[start : start + 4]] != ["tools", ".", "update_goal", "("]:
            continue
        if start and tokens[start - 1].text == ".":
            continue
        try:
            end = _call_end(tokens, start + 3)
            status = _literal_status(tokens[start + 4 : end - 1])
        except (ValueError, SyntaxError, RecursionError) as error:
            issues.append(f"unsupported goal arguments at input offset {tokens[start].offset}: {error}")
            continue
        sites.append({
            "arguments": {"status": status},
            "input_offset": tokens[start].offset,
            "input_line": source.count("\n", 0, tokens[start].offset) + 1,
            "result_forwarded": _forwards_result(tokens, start, end),
        })
    return sites, issues


def _result_failure(value: dict[str, Any]) -> str | None:
    for flag, failure in (("ok", False), ("success", False), ("isError", True)):
        if flag in value:
            if not isinstance(value[flag], bool):
                return "unsupported-output"
            if value[flag] is failure:
                return "failed-output"
    if "exit_code" in value:
        if type(value["exit_code"]) is not int:
            return "unsupported-output"
        if value["exit_code"] != 0:
            return "failed-output"
    if "status" in value and not isinstance(value["status"], str):
        return "unsupported-output"
    if value.get("error") or value.get("status") in ("failed", "error", "failure"):
        return "failed-output"
    return None


def _goal_result(value: Any, depth: int = 0) -> tuple[str, dict[str, Any] | None]:
    """Decode declared result fields; never search arbitrary string leaves."""
    if depth > 8:
        return "unsupported-output", None
    if isinstance(value, str):
        try:
            value = json.loads(value, object_pairs_hook=_unique_object)
        except (ValueError, RecursionError):
            return "unsupported-output", None
    if not isinstance(value, dict):
        return "unsupported-output", None
    failure = _result_failure(value)
    if failure is not None:
        return failure, None
    if "goal" in value and "content" in value:
        return "unsupported-output", None
    goal = value.get("goal")
    if isinstance(goal, str):
        try:
            goal = json.loads(goal, object_pairs_hook=_unique_object)
        except (ValueError, RecursionError):
            return "unsupported-output", None
    if isinstance(goal, dict) and goal.get("status") in ("active", "blocked", "complete"):
        return "goal-result", goal
    content = value.get("content")
    if isinstance(content, list) and len(content) == 1:
        block = content[0]
        if isinstance(block, dict) and block.get("type") == "text":
            return _goal_result(block.get("text"), depth + 1)
    return "unsupported-output", None


class NestedGoalEvidence:
    """Keep call sites and every correlated outer output until the input ends."""

    def __init__(self, compact_goal: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._calls: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._outputs: dict[str, list[_Output]] = defaultdict(list)
        self._compact_goal = compact_goal
        self.issues: list[dict[str, Any]] = []

    def observe(self, payload: dict[str, Any], line: int, timestamp: Any) -> None:
        call_id = payload.get("call_id")
        if payload.get("type") == "custom_tool_call_output" and isinstance(call_id, str):
            state, goal = "unattributed-output", None
            if any(call["sites"] for call in self._calls.get(call_id, [])):
                state, goal = _goal_result(payload.get("output"))
            # Retain bounded goal fields and correlation metadata, not arbitrary output bodies.
            summary = self._compact_goal(goal) if goal is not None else None
            self._outputs[call_id].append((line, state, summary))
            return
        if not (
            payload.get("type") == "custom_tool_call"
            and payload.get("name") in ("exec", "functions.exec")
            and payload.get("status") == "completed"
        ):
            return
        source = payload.get("input")
        if not isinstance(source, str) or not isinstance(call_id, str) or not call_id:
            self.issues.append({"line": line, "reason": "exec input or call ID is malformed"})
            return
        sites, issues = _scan(source)
        self.issues.extend({"line": line, "call_id": call_id, "reason": reason} for reason in issues)
        self._calls[call_id].append({"line": line, "timestamp": timestamp, "sites": sites, "issues": issues})

    def events(self) -> list[dict[str, Any]]:
        result = []
        for call_id, calls in self._calls.items():
            outputs = self._outputs.get(call_id, [])
            for call in calls:
                for site in call["sites"]:
                    confirmation, goal = self._confirmation(calls, call, site, outputs)
                    result.append({
                        "kind": "nested_goal_call_site", "tool": "update_goal",
                        "call_id": call_id, "line": call["line"], "timestamp": call["timestamp"],
                        "arguments": site["arguments"], "input_offset": site["input_offset"],
                        "input_line": site["input_line"], "output_confirmation": confirmation,
                        "output_lines": [line for line, _, _ in outputs],
                        "output": {"goal": goal} if goal is not None else None,
                    })
        return sorted(result, key=lambda item: (item["line"], item["input_offset"]))

    @staticmethod
    def _confirmation(
        calls: list[dict[str, Any]], call: dict[str, Any],
        site: dict[str, Any], outputs: list[_Output],
    ) -> tuple[str, dict[str, Any] | None]:
        if not outputs:
            return "missing-output", None
        if len(calls) != 1 or len(outputs) != 1 or outputs[0][0] <= call["line"]:
            return "ambiguous-correlation", None
        if len(call["sites"]) != 1 or call["issues"] or not site["result_forwarded"]:
            return "unattributed-output", None
        _, state, goal = outputs[0]
        if goal is None:
            return state, None
        if goal["status"] != site["arguments"]["status"]:
            return "status-mismatch", goal
        return "confirmed", goal
