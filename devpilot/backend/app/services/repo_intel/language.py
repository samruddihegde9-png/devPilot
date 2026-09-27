"""
Heuristic language/framework/dependency detection over a `ScanResult`.
Nothing here calls an LLM — it's plain pattern matching over filenames,
extensions, and well-known manifest files, so the overview is always
grounded in what's actually on disk.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.schemas.repo_intel import DependencyInfo
from app.services.repo_intel.scanner import ScanResult

_EXT_LANGUAGE = {
    "py": "Python",
    "ts": "TypeScript",
    "tsx": "TypeScript (React)",
    "js": "JavaScript",
    "jsx": "JavaScript (React)",
    "json": "JSON",
    "md": "Markdown",
    "css": "CSS",
    "html": "HTML",
    "yml": "YAML",
    "yaml": "YAML",
    "go": "Go",
    "rs": "Rust",
    "java": "Java",
    "rb": "Ruby",
}

_FRONTEND_FRAMEWORK_DEPS = {
    "react": "React",
    "vue": "Vue",
    "svelte": "Svelte",
    "@angular/core": "Angular",
    "next": "Next.js",
    "vite": "Vite",
}
_BACKEND_PY_MARKERS = {
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
}


@dataclass
class DetectionResult:
    primary_language: str
    languages: dict[str, int]  # language -> file count
    frameworks: list[str]
    dependencies: DependencyInfo


def _language_counts(scan: ScanResult) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in scan.files:
        ext = f.path.rsplit(".", 1)[-1].lower() if "." in f.path else ""
        lang = _EXT_LANGUAGE.get(ext)
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return counts


def _parse_requirements_txt(content: str) -> list[str]:
    names = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0].strip()
        if name:
            names.append(name.lower())
    return names


def _parse_package_json(content: str) -> tuple[list[str], list[str]]:
    """Returns (all_dep_names, frameworks_detected)."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return [], []
    deps = {}
    deps.update(data.get("dependencies", {}) or {})
    deps.update(data.get("devDependencies", {}) or {})
    names = sorted(deps.keys())
    frameworks = [label for dep, label in _FRONTEND_FRAMEWORK_DEPS.items() if dep in deps]
    return names, frameworks


def detect(scan: ScanResult) -> DetectionResult:
    languages = _language_counts(scan)
    primary_language = max(languages, key=languages.get) if languages else "Unknown"

    frameworks: set[str] = set()
    node_deps: list[str] = []
    python_deps: list[str] = []

    for f in scan.files:
        base = f.path.rsplit("/", 1)[-1]
        if base == "requirements.txt":
            reqs = _parse_requirements_txt(f.content)
            python_deps.extend(reqs)
            for dep in reqs:
                if dep in _BACKEND_PY_MARKERS:
                    frameworks.add(_BACKEND_PY_MARKERS[dep])
        elif base == "pyproject.toml":
            for dep, label in _BACKEND_PY_MARKERS.items():
                if dep in f.content.lower():
                    frameworks.add(label)
        elif base == "package.json":
            names, fw = _parse_package_json(f.content)
            node_deps.extend(names)
            frameworks.update(fw)

    # De-dupe while keeping things readable.
    python_deps = sorted(set(python_deps))
    node_deps = sorted(set(node_deps))

    return DetectionResult(
        primary_language=primary_language,
        languages=languages,
        frameworks=sorted(frameworks),
        dependencies=DependencyInfo(python=python_deps, node=node_deps),
    )
