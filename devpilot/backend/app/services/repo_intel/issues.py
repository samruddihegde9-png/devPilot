"""
Deliberately simple, deterministic issue detection. Every rule here is a
plain syntactic pattern (ast for Python, regex for JS/TS) — no LLM is
involved, so results are reproducible and each one can point at the exact
rule that fired. This is closer to a lightweight linter than a full static
analyzer; it's meant to catch obvious things a reviewer would flag, not to
replace `ruff`/`eslint`.
"""
from __future__ import annotations

import ast
import re

from app.services.repo_intel.scanner import ScanResult
from app.schemas.repo_intel import Issue

_SECRET_NAME_RE = re.compile(r"(api_?key|secret|password|token)", re.IGNORECASE)
_TODO_RE = re.compile(r"#\s*(TODO|FIXME)|//\s*(TODO|FIXME)", re.IGNORECASE)
_JS_CONSOLE_RE = re.compile(r"\bconsole\.(log|debug)\(")
_JS_EMPTY_CATCH_RE = re.compile(r"catch\s*(\([^)]*\))?\s*{\s*}")
_JS_DEBUGGER_RE = re.compile(r"\bdebugger\s*;")

MAX_FUNCTION_LINES = 55
MAX_FILE_LINES = 500


def _is_test_file(path: str) -> bool:
    lower = path.lower()
    return "test" in lower or lower.startswith("tests/")


def _python_issues(path: str, content: str) -> list[Issue]:
    found: list[Issue] = []
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        return [
            Issue(
                file=path,
                line=exc.lineno,
                function=None,
                description=f"File does not parse as valid Python: {exc.msg}",
                severity="high",
                suggested_fix="Fix the syntax error so this file can be imported/analyzed.",
                rule_id="py-syntax-error",
            )
        ]

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            is_bare = node.type is None
            body_is_pass_only = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
            if is_bare or body_is_pass_only:
                found.append(
                    Issue(
                        file=path,
                        line=node.lineno,
                        function=None,
                        description="Exception is caught and silently discarded"
                        + (" (bare except)" if is_bare else " (empty except body)"),
                        severity="high",
                        suggested_fix="Catch a specific exception type and at least log it, "
                        "or re-raise if it shouldn't be handled here.",
                        rule_id="py-swallowed-exception",
                    )
                )

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, "end_lineno", node.lineno)
            length = end_line - node.lineno + 1
            if length > MAX_FUNCTION_LINES:
                found.append(
                    Issue(
                        file=path,
                        line=node.lineno,
                        function=node.name,
                        description=f"Function `{node.name}` is {length} lines long.",
                        severity="medium",
                        suggested_fix="Consider splitting this into smaller, single-purpose functions.",
                        rule_id="py-long-function",
                    )
                )
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    found.append(
                        Issue(
                            file=path,
                            line=node.lineno,
                            function=node.name,
                            description=f"Function `{node.name}` uses a mutable default argument.",
                            severity="medium",
                            suggested_fix="Use `None` as the default and create the list/dict/set inside the function body.",
                            rule_id="py-mutable-default",
                        )
                    )

        if isinstance(node, ast.Assign) and not _is_test_file(path):
            for target in node.targets:
                if isinstance(target, ast.Name) and _SECRET_NAME_RE.search(target.id):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and node.value.value:
                        found.append(
                            Issue(
                                file=path,
                                line=node.lineno,
                                function=None,
                                description=f"`{target.id}` looks like a hardcoded credential.",
                                severity="high",
                                suggested_fix="Load this from an environment variable/settings object instead of a literal.",
                                rule_id="py-hardcoded-secret",
                            )
                        )

    for lineno, line in enumerate(content.splitlines(), start=1):
        if _TODO_RE.search(line):
            found.append(
                Issue(
                    file=path,
                    line=lineno,
                    function=None,
                    description="Unresolved TODO/FIXME comment.",
                    severity="low",
                    suggested_fix="Resolve it or file a tracked issue and reference it here.",
                    rule_id="todo-comment",
                )
            )

    return found


def _js_issues(path: str, content: str) -> list[Issue]:
    found: list[Issue] = []
    is_test = _is_test_file(path)
    for lineno, line in enumerate(content.splitlines(), start=1):
        if not is_test and _JS_CONSOLE_RE.search(line):
            found.append(
                Issue(
                    file=path,
                    line=lineno,
                    function=None,
                    description="`console.log`/`console.debug` left in source.",
                    severity="low",
                    suggested_fix="Remove it or replace with a real logger before shipping.",
                    rule_id="js-console-log",
                )
            )
        if _JS_EMPTY_CATCH_RE.search(line):
            found.append(
                Issue(
                    file=path,
                    line=lineno,
                    function=None,
                    description="Empty catch block silently discards the error.",
                    severity="high",
                    suggested_fix="At least log the error, or handle/re-throw it explicitly.",
                    rule_id="js-empty-catch",
                )
            )
        if _JS_DEBUGGER_RE.search(line):
            found.append(
                Issue(
                    file=path,
                    line=lineno,
                    function=None,
                    description="`debugger;` statement left in source.",
                    severity="medium",
                    suggested_fix="Remove before committing/shipping.",
                    rule_id="js-debugger-statement",
                )
            )
        if _TODO_RE.search(line):
            found.append(
                Issue(
                    file=path,
                    line=lineno,
                    function=None,
                    description="Unresolved TODO/FIXME comment.",
                    severity="low",
                    suggested_fix="Resolve it or file a tracked issue and reference it here.",
                    rule_id="todo-comment",
                )
            )
    return found


def find_issues(scan: ScanResult) -> list[Issue]:
    issues: list[Issue] = []
    for f in scan.files:
        line_count = f.content.count("\n") + 1
        if line_count > MAX_FILE_LINES:
            issues.append(
                Issue(
                    file=f.path,
                    line=None,
                    function=None,
                    description=f"File is {line_count} lines long.",
                    severity="low",
                    suggested_fix="Consider splitting this file into smaller modules.",
                    rule_id="large-file",
                )
            )

        if f.path.endswith(".py"):
            issues.extend(_python_issues(f.path, f.content))
        elif f.path.endswith((".ts", ".tsx", ".js", ".jsx")):
            issues.extend(_js_issues(f.path, f.content))

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda i: (severity_rank.get(i.severity, 3), i.file, i.line or 0))
    return issues
