from __future__ import annotations

import math

from app.services.repo_intel.graph import build_file_graph, build_module_graph
from app.services.repo_intel.language import DetectionResult
from app.services.repo_intel.llm import call_llm
from app.services.repo_intel.scanner import ScanResult
from app.schemas.repo_intel import (
    Architecture,
    ArchitectureModule,
    ArchitectureRelation,
    RepoOverview,
)

_SYSTEM_PROMPT = (
    "You are a senior engineer writing a short, accurate architecture summary "
    "for a developer tool. You are given ONLY facts already extracted from the "
    "repository (detected stack, module list, import relationships). Write 3-5 "
    "plain-English sentences describing how the pieces fit together. Do not "
    "invent files, frameworks, features, or metrics that are not in the given "
    "facts. If the facts are sparse, keep the summary short rather than "
    "padding it."
)


def _heuristic_explanation(overview: RepoOverview, modules: list[ArchitectureModule], relations: list[ArchitectureRelation]) -> str:
    stack_bits = [overview.primary_language]
    if overview.frameworks:
        stack_bits.append(" + ".join(overview.frameworks))
    stack_desc = " / ".join(stack_bits)

    lines = [
        f"This is a {stack_desc} codebase with {overview.analyzed_file_count} analyzed files "
        f"across {len(modules)} identified module(s)."
    ]

    if modules:
        top = sorted(modules, key=lambda m: -m.file_count)[:5]
        mod_desc = ", ".join(f"`{m.path}` ({m.file_count} files)" for m in top)
        lines.append(f"The largest modules are {mod_desc}.")

    if relations:
        sample = relations[:6]
        rel_desc = "; ".join(f"`{r.source}` → `{r.target}`" for r in sample)
        lines.append(f"Observed internal dependencies include: {rel_desc}.")
    else:
        lines.append(
            "No internal cross-module imports were detected between the analyzed files — "
            "modules currently look independent, or the project is still small."
        )

    return " ".join(lines)


def _layout(modules: list[ArchitectureModule]) -> None:
    """Assign simple grid coordinates (0..1) in place, for a dependency-free diagram."""
    n = len(modules)
    if n == 0:
        return
    cols = max(1, math.ceil(math.sqrt(n)))
    rows = max(1, math.ceil(n / cols))
    for i, mod in enumerate(modules):
        col, row = i % cols, i // cols
        mod.x = (col + 0.5) / cols
        mod.y = (row + 0.5) / rows


def build_architecture(overview: RepoOverview, scan: ScanResult, detection: DetectionResult) -> Architecture:
    file_graph = build_file_graph(scan)
    module_nodes, module_edges = build_module_graph(scan, file_graph)

    modules = [
        ArchitectureModule(path=m.path, file_count=m.file_count, description=m.description, x=0.5, y=0.5)
        for m in module_nodes
    ]
    _layout(modules)
    relations = [ArchitectureRelation(source=e.source, target=e.target) for e in module_edges]

    explanation = _heuristic_explanation(overview, modules, relations)

    llm_text = call_llm(
        _SYSTEM_PROMPT,
        "Stack: "
        + overview.primary_language
        + (f" with {', '.join(overview.frameworks)}" if overview.frameworks else "")
        + f"\nModules ({len(modules)}): "
        + ", ".join(f"{m.path} ({m.file_count} files)" for m in modules[:20])
        + f"\nInternal import relationships ({len(relations)}): "
        + "; ".join(f"{r.source} -> {r.target}" for r in relations[:30]),
        max_tokens=350,
    )

    return Architecture(
        explanation=llm_text or explanation,
        explanation_source="ai" if llm_text else "heuristic",
        modules=modules,
        relations=relations,
    )
