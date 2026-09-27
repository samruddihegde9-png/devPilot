"""
Test suggestions. Two tiers, deliberately kept honest:

1. Every public function/class gets a plain-English suggestion of what to
   test (happy path, edge cases, error cases) — always safe to produce.
2. Only simple, side-effect-free-looking Python functions (few params, no
   obvious I/O/network/DB calls in the body) get an actual generated pytest
   skeleton. Anything more complex (FastAPI routes, DB access, async I/O,
   React components) gets a suggestion only — generating plausible-looking
   but wrong test code for those would be worse than not generating any.
"""
from __future__ import annotations

import ast
import re

from app.services.repo_intel.scanner import ScanResult
from app.schemas.repo_intel import TestSuggestion

_JS_EXPORT_FN_RE = re.compile(
    r"export\s+(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)"
)
_JS_EXPORT_CONST_FN_RE = re.compile(
    r"export\s+const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>"
)

_RISKY_CALL_NAMES = {
    "open", "requests", "httpx", "urlopen", "socket", "execute", "cursor",
    "commit", "session", "post", "get", "put", "delete", "connect",
}


def _module_import_path(file_path: str) -> str:
    return file_path[:-3].replace("/", ".") if file_path.endswith(".py") else file_path


def _looks_simple_and_pure(node: ast.FunctionDef) -> bool:
    if isinstance(node, ast.AsyncFunctionDef):
        return False
    if len(node.args.args) > 3:
        return False
    if node.decorator_list:
        return False
    for inner in ast.walk(node):
        if isinstance(inner, (ast.With, ast.AsyncWith, ast.Try)):
            return False
        if isinstance(inner, ast.Call):
            fname = ""
            if isinstance(inner.func, ast.Name):
                fname = inner.func.id
            elif isinstance(inner.func, ast.Attribute):
                fname = inner.func.attr
            if fname.lower() in _RISKY_CALL_NAMES:
                return False
    return True


def _literal_for_annotation(annotation: ast.expr | None, index: int) -> str:
    ann = ast.unparse(annotation) if annotation is not None else ""
    ann = ann.lower()
    if "int" in ann:
        return str(index + 1)
    if "float" in ann:
        return f"{index + 1}.0"
    if "bool" in ann:
        return "True"
    if "list" in ann:
        return "[]"
    if "dict" in ann:
        return "{}"
    if "str" in ann or ann == "":
        return f'"example{index}"'
    return f'"example{index}"'


def _generate_pytest_skeleton(func_path: str, node: ast.FunctionDef, module_import: str) -> str:
    args = [a.arg for a in node.args.args]
    call_args = ", ".join(_literal_for_annotation(a.annotation, i) for i, a in enumerate(node.args.args))
    return (
        f"from {module_import} import {node.name}\n\n\n"
        f"def test_{node.name}_returns_expected_value():\n"
        f"    result = {node.name}({call_args})\n"
        f"    assert result is not None  # TODO: replace with the actual expected value\n"
    )


def _python_suggestions(f_path: str, content: str) -> list[TestSuggestion]:
    if "test" in f_path.lower():
        return []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    module_import = _module_import_path(f_path)
    suggestions: list[TestSuggestion] = []

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_"):
            continue

        cases = [
            f"Typical/expected input for `{node.name}`",
            "An edge case (empty input, zero, None, or boundary value)",
        ]
        if any(isinstance(n, ast.Raise) for n in ast.walk(node)):
            cases.append("An input that should trigger the function's error/raise path")

        generated_code = None
        generated_path = None
        if isinstance(node, ast.FunctionDef) and _looks_simple_and_pure(node):
            generated_code = _generate_pytest_skeleton(f_path, node, module_import)
            test_dir = "tests"
            base = f_path.rsplit("/", 1)[-1]
            generated_path = f"{test_dir}/test_{base}"

        suggestions.append(
            TestSuggestion(
                target_file=f_path,
                target_symbol=node.name,
                description=f"`{node.name}` in `{f_path}` has no matching test yet.",
                suggested_cases=cases,
                generated_test_code=generated_code,
                generated_test_path=generated_path,
            )
        )

    return suggestions


def _js_suggestions(f_path: str, content: str) -> list[TestSuggestion]:
    if "test" in f_path.lower() or f_path.endswith((".tsx", ".jsx")):
        # React components need rendering/DOM setup we won't fabricate — suggest only, no code.
        pass

    suggestions: list[TestSuggestion] = []
    seen: set[str] = set()
    for pattern in (_JS_EXPORT_FN_RE, _JS_EXPORT_CONST_FN_RE):
        for match in pattern.finditer(content):
            name = match.group(1)
            if name in seen or name == "default":
                continue
            seen.add(name)
            cases = [
                f"Typical/expected input for `{name}`",
                "An edge case (empty input, missing/undefined value)",
            ]
            suggestions.append(
                TestSuggestion(
                    target_file=f_path,
                    target_symbol=name,
                    description=f"Exported function `{name}` in `{f_path}` has no matching test yet.",
                    suggested_cases=cases,
                    generated_test_code=None,  # JS/TS runner varies by project; suggestion only, no fabricated code.
                    generated_test_path=None,
                )
            )
    return suggestions


def suggest_tests(scan: ScanResult) -> list[TestSuggestion]:
    suggestions: list[TestSuggestion] = []
    for f in scan.files:
        if f.path.endswith(".py"):
            suggestions.extend(_python_suggestions(f.path, f.content))
        elif f.path.endswith((".ts", ".tsx", ".js", ".jsx")):
            suggestions.extend(_js_suggestions(f.path, f.content))
    return suggestions[:60]
