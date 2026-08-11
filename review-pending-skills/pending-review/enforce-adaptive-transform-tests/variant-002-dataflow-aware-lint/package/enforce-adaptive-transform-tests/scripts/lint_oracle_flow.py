#!/usr/bin/env python3
"""Find textual test oracles whose values derive from rendered source."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable


PRODUCERS = {
    "render_source",
    "rendered_source",
    "to_source",
    "syntax_text",
    "node_text",
    "transformation_output",
}
SNAPSHOT_SINKS = {"assert_snapshot", "match_snapshot", "snapshot"}
FUNCTION_SINKS = {"contains", "regex_match", "regex_search"}
METHOD_SINKS = {"startswith", "endswith", "count", "contains"}


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None


def infer_identity_wrappers(tree: ast.AST) -> set[str]:
    wrappers: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or len(node.body) != 1:
            continue
        returned = node.body[0]
        if not isinstance(returned, ast.Return) or not isinstance(returned.value, ast.Name):
            continue
        parameters = {argument.arg for argument in node.args.args}
        if returned.value.id in parameters:
            wrappers.add(node.name)
    return wrappers


class OracleFlowAnalyzer(ast.NodeVisitor):
    def __init__(self, path: Path, wrappers: set[str]) -> None:
        self.path = path
        self.wrappers = wrappers
        self.tainted_scopes: list[set[str]] = [set()]
        self.findings: list[dict[str, object]] = []
        self.exempt_depth = 0
        self.seen: set[tuple[int, int, str]] = set()

    @property
    def tainted(self) -> set[str]:
        return self.tainted_scopes[-1]

    def add_finding(self, node: ast.AST, rule: str, detail: str) -> None:
        key = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0), rule)
        if key in self.seen or self.exempt_depth:
            return
        self.seen.add(key)
        self.findings.append(
            {
                "path": self.path.as_posix(),
                "line": key[0],
                "column": key[1] + 1,
                "rule": rule,
                "detail": detail,
            }
        )

    def expression_is_tainted(self, node: ast.AST | None) -> bool:
        if node is None:
            return False
        if isinstance(node, ast.Name):
            return node.id in self.tainted
        if isinstance(node, ast.Call):
            name = call_name(node.func) or ""
            short = name.rsplit(".", 1)[-1]
            if short in PRODUCERS:
                return True
            if short in self.wrappers:
                return any(self.expression_is_tainted(argument) for argument in node.args)
            return self.expression_is_tainted(node.func) or any(
                self.expression_is_tainted(argument) for argument in node.args
            )
        if isinstance(node, ast.Attribute):
            return self.expression_is_tainted(node.value)
        if isinstance(node, ast.Subscript):
            return self.expression_is_tainted(node.value)
        return any(self.expression_is_tainted(child) for child in ast.iter_child_nodes(node))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        decorators = {call_name(item) for item in node.decorator_list}
        self.tainted_scopes.append(set())
        if "exact_output_contract" in decorators:
            self.exempt_depth += 1
        for statement in node.body:
            self.visit(statement)
        if "exact_output_contract" in decorators:
            self.exempt_depth -= 1
        self.tainted_scopes.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node: ast.Assign) -> None:
        if self.expression_is_tainted(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.tainted.add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and self.expression_is_tainted(node.value):
            self.tainted.add(node.target.id)
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        operands = [node.left, *node.comparators]
        if any(self.expression_is_tainted(operand) for operand in operands):
            for operator in node.ops:
                if isinstance(operator, (ast.Eq, ast.NotEq)):
                    self.add_finding(node, "raw-equality", "rendered-source-derived value reaches equality")
                elif isinstance(operator, (ast.In, ast.NotIn)):
                    self.add_finding(node, "membership", "rendered-source-derived value reaches membership oracle")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = call_name(node.func) or ""
        short = name.rsplit(".", 1)[-1]
        if isinstance(node.func, ast.Attribute) and short in METHOD_SINKS:
            if self.expression_is_tainted(node.func.value):
                self.add_finding(node, f"method-{short}", f"tainted source reaches .{short}()")
        if short in SNAPSHOT_SINKS and any(self.expression_is_tainted(item) for item in node.args):
            self.add_finding(node, "snapshot", "rendered-source-derived value reaches snapshot oracle")
        if short in FUNCTION_SINKS and any(self.expression_is_tainted(item) for item in node.args):
            self.add_finding(node, f"function-{short}", f"tainted source reaches {short}()")
        if name in {"re.search", "re.match", "re.fullmatch"} and any(
            self.expression_is_tainted(item) for item in node.args[1:]
        ):
            self.add_finding(node, "regex", "rendered-source-derived value reaches regex oracle")
        self.generic_visit(node)


def analyze(path: Path, configured_wrappers: Iterable[str]) -> dict[str, object]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    wrappers = infer_identity_wrappers(tree) | set(configured_wrappers)
    analyzer = OracleFlowAnalyzer(path, wrappers)
    analyzer.visit(tree)
    analyzer.findings.sort(key=lambda item: (int(item["line"]), int(item["column"]), str(item["rule"])))
    return {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "wrappers": sorted(wrappers),
        "findings": analyzer.findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="+")
    parser.add_argument("--wrapper", action="append", default=[])
    args = parser.parse_args(argv)
    reports: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    for path in args.paths:
        try:
            reports.append(analyze(path, args.wrapper))
        except (OSError, SyntaxError) as error:
            errors.append({"path": path.as_posix(), "error": str(error)})
    finding_count = sum(len(report["findings"]) for report in reports)  # type: ignore[arg-type]
    print(
        json.dumps(
            {
                "schema_version": 1,
                "status": "error" if errors else ("findings" if finding_count else "clean"),
                "finding_count": finding_count,
                "reports": reports,
                "errors": errors,
            },
            indent=2,
            sort_keys=True,
        )
    )
    if errors:
        return 2
    return 1 if finding_count else 0


if __name__ == "__main__":
    sys.exit(main())
