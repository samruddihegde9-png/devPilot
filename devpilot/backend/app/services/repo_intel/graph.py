"""
Builds a best-effort internal import graph from the scanned files.

This is intentionally conservative: it only records an edge when the import
resolves to another file that was actually scanned in this repository.
External/third-party imports (fastapi, react, lodash, ...) are not turned
into edges — they'd clutter the graph and this view is about *this*
codebase's own structure, not its dependency tree (that's the Overview tab).
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from app.services.repo_intel.scanner import ScanResult

_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+(?:[\w*{}\s,]+\s+from\s+)?|require\()\s*['"](\.[^'"]+)['"]"""
)


@dataclass
class ModuleNode:
    path: str  # folder path used as the "module" grouping
    file_count: int
    description: str


@dataclass
class ModuleEdge:
    source: str
    target: str


def _module_of(file_path: str) -> str:
    parts = file_path.split("/")
    return "/".join(parts[:-1]) if len(parts) > 1 else "(root)"


def _python_internal_imports(content: str, file_path: str, all_paths: set[str]) -> set[str]:
    """Return internal file paths this Python file appears to import."""
    targets: set[str] = set()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return targets

    module_prefixes = {p.rsplit(".", 1)[0].replace("/", ".") for p in all_paths if p.endswith(".py")}

    def resolve(dotted: str) -> str | None:
        candidate = dotted.replace(".", "/") + ".py"
        if candidate in all_paths:
            return candidate
        candidate_init = dotted.replace(".", "/") + "/__init__.py"
        if candidate_init in all_paths:
            return candidate_init
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                resolved = resolve(alias.name)
                if resolved and resolved != file_path:
                    targets.add(resolved)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            if node.module.split(".")[0] in {p.split(".")[0] for p in module_prefixes}:
                resolved = resolve(node.module)
                if resolved and resolved != file_path:
                    targets.add(resolved)

    return targets


def _resolve_relative_js(from_path: str, spec: str, all_paths: set[str]) -> str | None:
    parts = from_path.split("/")[:-1]
    for seg in spec.split("/"):
        if seg == ".":
            continue
        if seg == "..":
            if parts:
                parts.pop()
        else:
            parts.append(seg)
    base = "/".join(parts)
    for suffix in ("", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx", "/index.js"):
        candidate = base + suffix
        if candidate in all_paths:
            return candidate
    return None


def _js_internal_imports(content: str, file_path: str, all_paths: set[str]) -> set[str]:
    targets: set[str] = set()
    for match in _JS_IMPORT_RE.finditer(content):
        spec = match.group(1)
        resolved = _resolve_relative_js(file_path, spec, all_paths)
        if resolved and resolved != file_path:
            targets.add(resolved)
    return targets


def build_file_graph(scan: ScanResult) -> dict[str, set[str]]:
    """file path -> set of internal file paths it imports."""
    all_paths = {f.path for f in scan.files}
    graph: dict[str, set[str]] = {}
    for f in scan.files:
        if f.path.endswith(".py"):
            graph[f.path] = _python_internal_imports(f.content, f.path, all_paths)
        elif f.path.endswith((".ts", ".tsx", ".js", ".jsx")):
            graph[f.path] = _js_internal_imports(f.content, f.path, all_paths)
    return graph


def build_module_graph(scan: ScanResult, file_graph: dict[str, set[str]]) -> tuple[list[ModuleNode], list[ModuleEdge]]:
    file_counts: dict[str, int] = {}
    for f in scan.files:
        file_counts[_module_of(f.path)] = file_counts.get(_module_of(f.path), 0) + 1

    edge_set: set[tuple[str, str]] = set()
    for src_file, targets in file_graph.items():
        src_mod = _module_of(src_file)
        for tgt_file in targets:
            tgt_mod = _module_of(tgt_file)
            if tgt_mod != src_mod:
                edge_set.add((src_mod, tgt_mod))

    modules_in_graph = {m for edge in edge_set for m in edge}
    modules_in_graph.update(file_counts.keys())

    nodes = [
        ModuleNode(path=mod, file_count=file_counts.get(mod, 0), description=_describe_module(mod, scan))
        for mod in sorted(modules_in_graph)
    ]
    # Keep the graph readable: only the modules with real relationships or a
    # meaningful amount of code, capped so the diagram stays legible.
    nodes = sorted(nodes, key=lambda n: (-n.file_count, n.path))[:18]
    kept_paths = {n.path for n in nodes}
    edges = [ModuleEdge(source=s, target=t) for (s, t) in sorted(edge_set) if s in kept_paths and t in kept_paths]

    return nodes, edges


def _describe_module(module_path: str, scan: ScanResult) -> str:
    name = module_path.rsplit("/", 1)[-1] if module_path != "(root)" else "root"
    files_here = [f for f in scan.files if _module_of(f.path) == module_path]
    exts = {f.path.rsplit(".", 1)[-1] for f in files_here if "." in f.path}
    if exts:
        kind = "/".join(sorted(exts))
        return f"{len(files_here)} file(s) ({kind}) under {name}/"
    return f"{len(files_here)} file(s) under {name}/"
