from __future__ import annotations

from app.services.repo_intel.language import DetectionResult, detect
from app.services.repo_intel.scanner import ScanResult
from app.schemas.repo_intel import KeyModule, ImportantFile, RepoOverview

_IMPORTANT_BASENAMES = {
    "readme.md": "Project documentation entry point",
    "package.json": "Node/JS dependency & script manifest",
    "requirements.txt": "Python dependency manifest",
    "pyproject.toml": "Python project/dependency manifest",
    "docker-compose.yml": "Local service orchestration",
    "dockerfile": "Container build definition",
    ".env.example": "Documents required environment variables",
    "main.py": "Likely application entry point",
    "app.py": "Likely application entry point",
    "index.js": "Likely application entry point",
    "index.ts": "Likely application entry point",
    "main.tsx": "Frontend entry point",
    "main.ts": "Frontend entry point",
    "app.tsx": "Root UI component",
    "config.py": "Application configuration",
    "vite.config.ts": "Frontend build configuration",
}


def _important_files(scan: ScanResult) -> list[ImportantFile]:
    found: list[ImportantFile] = []
    for f in scan.files:
        base = f.path.rsplit("/", 1)[-1].lower()
        if base in _IMPORTANT_BASENAMES:
            found.append(ImportantFile(path=f.path, reason=_IMPORTANT_BASENAMES[base]))
    # Keep root-level and shallow files first, then by path for stability.
    found.sort(key=lambda x: (x.path.count("/"), x.path))
    return found[:20]


def _key_modules(scan: ScanResult) -> list[KeyModule]:
    """Top-level-ish folders ranked by how many source files they contain."""
    counts: dict[str, int] = {}
    for f in scan.files:
        parts = f.path.split("/")
        if len(parts) < 2:
            continue
        # Use the first two path segments when the first is a thin wrapper
        # (e.g. "app/services" instead of just "app") so modules stay specific.
        folder = "/".join(parts[:-1])
        counts[folder] = counts.get(folder, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [KeyModule(path=path, file_count=count) for path, count in ranked[:12]]


def build_overview(project_name: str, scan: ScanResult, detection: DetectionResult | None = None) -> RepoOverview:
    detection = detection or detect(scan)
    total_lines = sum(f.content.count("\n") + 1 for f in scan.files)

    return RepoOverview(
        project_name=project_name,
        primary_language=detection.primary_language,
        languages=detection.languages,
        frameworks=detection.frameworks,
        file_count=scan.total_files_seen,
        analyzed_file_count=len(scan.files),
        total_lines=total_lines,
        important_files=_important_files(scan),
        key_modules=_key_modules(scan),
        dependencies=detection.dependencies,
        skipped_binary_count=len(scan.skipped_binary),
        skipped_large_count=len(scan.skipped_large),
    )
