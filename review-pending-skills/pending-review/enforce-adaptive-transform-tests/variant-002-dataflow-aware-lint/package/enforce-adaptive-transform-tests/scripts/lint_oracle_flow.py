#!/usr/bin/env python3
"""Advisory rendered-source oracle analysis for selected Python files."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable

PRODUCERS = {'render_source', 'rendered_source', 'to_source', 'syntax_text', 'node_text', 'transformation_output'}
STRUCTURAL_PRODUCERS = {'parse_source', 'ast.parse'}
STRUCTURAL_QUERIES = {'functions', 'owners', 'nodes', 'query', 'find', 'function_count'}
SNAPSHOT_SINKS = {'assert_snapshot', 'match_snapshot', 'snapshot'}
FUNCTION_SINKS = {'contains', 'regex_match', 'regex_search', 'assert_equal', 'assert_equals', 'assertEqual'}
METHOD_SINKS = {'startswith', 'endswith', 'count', 'contains'}
TEXT, STRUCTURE, UNKNOWN = frozenset({'text'}), frozenset({'structure'}), frozenset({'unknown'})


def display(value: str) -> str:
    return re.sub(re.escape(str(Path.home())) + r'(?=$|[/\s\x27\x22:,)])', '~', value)


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = call_name(node.value)
        return f'{prefix}.{node.attr}' if prefix else node.attr
    return None


class OracleFlowAnalyzer:
    def __init__(self, path: Path, wrappers: Iterable[str]) -> None:
        self.path = path
        self.wrappers = set(wrappers)
        self.env = {}
        self.functions = {}
        self.findings = []
        self.unknown = []
        self.active = set()
        self.visited = set()
        self.exempt = False
        self.in_assert = False
        self.returns = []

    def observation(self, node: ast.AST, rule: str, value: frozenset[str]) -> None:
        if self.exempt:
            return
        row = dict(path=display(str(self.path)), line=node.lineno, column=node.col_offset + 1, rule=rule)
        if 'text' in value and not any(all(f[k] == v for k, v in row.items()) for f in self.findings):
            self.findings.append({**row, 'detail': 'rendered-source provenance reaches a textual oracle'})
        if 'unknown' in value:
            self.unknown_at(node, 'oracle receives an unmodeled value')

    def unknown_at(self, node: ast.AST, detail: str) -> None:
        row = dict(line=node.lineno, detail=detail)
        if not self.exempt and row not in self.unknown:
            self.unknown.append(row)

    def expression(self, node: ast.AST | None) -> frozenset[str]:
        if node is None or isinstance(node, ast.Constant):
            return frozenset()
        if isinstance(node, ast.Name):
            return self.env.get(node.id, UNKNOWN)
        if isinstance(node, ast.Call):
            return self.call(node)
        if isinstance(node, ast.Attribute):
            value = self.expression(node.value)
            return value if 'text' in value else UNKNOWN
        if isinstance(node, ast.Compare):
            value = frozenset().union(*(self.expression(n) for n in [node.left, *node.comparators]))
            if self.in_assert:
                for op in node.ops:
                    if isinstance(op, (ast.Eq, ast.NotEq, ast.In, ast.NotIn)):
                        self.observation(node, 'membership' if isinstance(op, (ast.In, ast.NotIn)) else 'raw-equality', value)
            return frozenset() if self.in_assert else value
        if isinstance(node, (ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.JoinedStr, ast.FormattedValue)):
            return frozenset().union(*(self.expression(n) for n in ast.iter_child_nodes(node) if isinstance(n, ast.expr)))
        self.unknown_at(node, f'unsupported expression: {type(node).__name__}')
        return UNKNOWN

    def call(self, node: ast.Call) -> frozenset[str]:
        name = call_name(node.func) or ''
        short = name.rsplit('.', 1)[-1]
        args = [self.expression(arg) for arg in node.args]
        keywords = {kw.arg: self.expression(kw.value) for kw in node.keywords}
        values = frozenset().union(*args, *keywords.values())
        if name in self.functions:
            return self.invoke(self.functions[name], args, keywords, node)
        if short in PRODUCERS:
            return TEXT
        if name in STRUCTURAL_PRODUCERS:
            return STRUCTURE
        if name in self.wrappers:
            return values
        receiver = self.expression(node.func.value) if isinstance(node.func, ast.Attribute) else frozenset()
        if receiver == STRUCTURE and short in STRUCTURAL_QUERIES:
            return STRUCTURE
        if name == 'len' and values == STRUCTURE:
            return frozenset()
        if name in {'str', 'len'}:
            return values
        sink = self.call_sink(name, short)
        if sink:
            self.observation(node, sink, values | receiver)
            return frozenset()
        # Formatting/source-string methods preserve text. Other calls are not proof of a safe value.
        if receiver == TEXT and short in METHOD_SINKS | {'strip', 'replace', 'format', 'join', 'lower', 'upper'}:
            return TEXT
        self.unknown_at(node, f'unmodeled call: {name or "dynamic callable"}')
        return UNKNOWN

    def call_sink(self, name, short):
        if short in SNAPSHOT_SINKS:
            return 'snapshot'
        if short in FUNCTION_SINKS and (self.in_assert or short.startswith('assert')):
            return f'function-{short}'
        if self.in_assert and short in METHOD_SINKS:
            return f'method-{short}'
        if self.in_assert and name in {'re.search', 're.match', 're.fullmatch'}:
            return 'regex'
        return None

    def invoke(self, binding, args, keywords, site):
        node, closure, functions = binding
        if id(node) in self.active or node.args.vararg or node.args.kwarg or None in keywords:
            self.unknown_at(site, 'recursive or variadic local call is not modeled')
            return UNKNOWN
        parameters = [*node.args.posonlyargs, *node.args.args]
        names = [p.arg for p in parameters]
        if len(args) > len(names) or set(names[:len(args)]) & keywords.keys():
            self.unknown_at(site, 'local argument binding cannot be established')
            return UNKNOWN
        allowed = set(names) | {p.arg for p in node.args.kwonlyargs}
        if set(keywords) - allowed or set(keywords) & {p.arg for p in node.args.posonlyargs}:
            self.unknown_at(site, 'unsupported local keyword binding')
            return UNKNOWN
        env = dict(closure)
        env.update({name: UNKNOWN for name in names + [p.arg for p in node.args.kwonlyargs]})
        env.update(zip(names, args))
        env.update(keywords)
        saved = self.env, self.functions, self.exempt, self.in_assert, self.returns
        self.env, self.functions = env, dict(functions)
        self.exempt = any(call_name(d) == 'exact_output_contract' for d in node.decorator_list)
        self.in_assert, self.returns = False, []
        self.active.add(id(node)); self.visited.add(id(node))
        self.block(node.body)
        result = frozenset().union(*self.returns)
        self.active.remove(id(node))
        self.env, self.functions, self.exempt, self.in_assert, self.returns = saved
        return result

    def block(self, statements):
        for node in statements:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions[node.name] = (node, self.env, self.functions)
        for node in statements:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Import, ast.ImportFrom, ast.Pass)):
                continue
            if isinstance(node, ast.Return):
                self.returns.append(self.expression(node.value))
                break
            self.statement(node)

    def statement(self, node):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = self.expression(node.value)
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    self.env[target.id] = value
                else:
                    self.unknown_at(node, 'container or destructuring assignment is not modeled')
        elif isinstance(node, ast.Assert):
            self.in_assert = True
            value = self.expression(node.test)
            self.observation(node, 'assertion', value)
            self.in_assert = False
        elif isinstance(node, ast.Expr):
            self.expression(node.value)
        else:
            self.unknown_at(node, f'unsupported statement: {type(node).__name__}')
            # Preserve uncertainty after unmodeled control flow, including potentially reassigned names.
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                    self.env[child.id] = UNKNOWN

    def analyze(self, tree):
        self.block(tree.body)
        entries = [b for n, b in self.functions.items() if n.startswith('test_')]
        for binding in entries:
            self.invoke(binding, [], {}, binding[0])
        # Uncalled local helpers are disclosed, not optimistically certified clean.
        for binding in list(self.functions.values()):
            if id(binding[0]) not in self.visited:
                self.unknown_at(binding[0], 'function not reached by a selected test or module call')


def analyze(path: Path, configured_wrappers: Iterable[str]) -> dict[str, object]:
    raw = path.expanduser().read_bytes()
    tree = ast.parse(raw.decode('utf-8'), filename=display(str(path)))
    analyzer = OracleFlowAnalyzer(path, configured_wrappers)
    analyzer.analyze(tree)
    return dict(path=display(str(path)), sha256=hashlib.sha256(raw).hexdigest(),
                wrappers=sorted(configured_wrappers), findings=analyzer.findings,
                coverage='unknown' if analyzer.unknown else 'complete-within-model', unknown=analyzer.unknown)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', type=Path, nargs='+', help='explicit Python files, not directory roots')
    parser.add_argument('--wrapper', action='append', default=[])
    args = parser.parse_args(argv)
    reports, errors = [], []
    for path in args.paths:
        try:
            reports.append(analyze(path, args.wrapper))
        except (OSError, UnicodeError, SyntaxError, ValueError, RecursionError) as error:
            errors.append(dict(path=display(str(path)), error=display(str(error))))
    findings = sum(len(r['findings']) for r in reports)
    unknown = sum(len(r['unknown']) for r in reports)
    status = 'error' if errors else 'findings' if findings else 'unknown' if unknown else 'clean'
    print(json.dumps(dict(schema_version=1, status=status, finding_count=findings, unknown_count=unknown,
                          reports=reports, errors=errors), indent=2, sort_keys=True))
    return 2 if errors else 1 if findings else 3 if unknown else 0


if __name__ == '__main__':
    sys.exit(main())
