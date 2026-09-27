"""
Repository scanning: turns a project's file tree (as already exposed by
`LocalSandbox`) into a flat list of readable text files, with binary files,
build artifacts, and oversized files filtered out before anything is sent to
an LLM or a heuristic analyzer.

This module never touches the filesystem directly — it goes through
`local_sandbox` (the same path-safety boundary the file-explorer API uses),
so Repository Intelligence can't read or leak anything outside the project's
own workspace.

Jupyter Notebooks (.ipynb) are a special case: the raw JSON is unreadable
for LLM-based QA and heuristic analysis.  We convert them to a plain-text
representation that preserves all meaningful content (markdown prose +
code cells) while stripping the noisy metadata, outputs, and JSON structure.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from app.schemas.file import FileNode
from app.services.sandbox.local import BinaryFileError, local_sandbox
from app.services.sandbox.manager import NotFoundError

logger = logging.getLogger(__name__)

# Extra directories/files to skip during analysis, beyond what the sandbox's
# file tree already hides (.git, node_modules, __pycache__, .venv, ...).
_EXTRA_IGNORED_NAMES = {
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".cache",
    "coverage",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "egg-info",
    ".DS_Store",
    "workspaces",
}

# Extensions we don't try to read as source (images, fonts, archives, locks).
_SKIP_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "ico", "webp", "bmp",
    "woff", "woff2", "ttf", "eot", "otf",
    "zip", "tar", "gz", "7z", "rar",
    "pdf", "mp3", "mp4", "mov", "avi",
    "pyc", "pyo", "so", "dll", "exe", "bin",
    "lock",
}
_SKIP_FILENAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock"}

# ---------------------------------------------------------------------------
# Jupyter Notebook conversion
# ---------------------------------------------------------------------------

def _notebook_to_text(raw_json: str, path: str) -> str:
    """Convert a Jupyter Notebook's raw JSON into a human-readable text form.

    Extracts markdown cells (as-is) and code cells (fenced with ```) in
    notebook order.  Cell outputs, metadata, and execution counts are
    discarded — they are noisy and not useful for code analysis or Q&A.

    Returns the original raw JSON unchanged on any parse error so the
    file still gets indexed (just less readably).
    """
    try:
        nb = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        logger.debug("Could not parse %s as JSON — indexing raw content", path)
        return raw_json

    cells = nb.get("cells", [])
    if not cells:
        return raw_json

    parts: list[str] = [f"# Notebook: {path}\n"]
    for cell in cells:
        cell_type = cell.get("cell_type", "")
        source = cell.get("source", [])
        # source can be a list of strings (nbformat ≤4) or a single string.
        text = "".join(source) if isinstance(source, list) else str(source)
        text = text.strip()
        if not text:
            continue

        if cell_type == "markdown":
            parts.append(text)
        elif cell_type == "code":
            parts.append(f"```python\n{text}\n```")
        # raw cells are uncommon and usually contain non-code content;
        # include them as plain text so they remain searchable.
        elif cell_type == "raw":
            parts.append(text)

    result = "\n\n".join(parts)
    return result if result.strip() else raw_json

# Per-file and total content budgets so a large repo can never be dumped
# wholesale into an LLM prompt or blow up memory during analysis.
MAX_FILE_BYTES = 40_000
MAX_TOTAL_BYTES = 1_200_000
MAX_FILES = 400


@dataclass
class ScannedFile:
    path: str
    size: int
    content: str
    truncated: bool


@dataclass
class ScanResult:
    files: list[ScannedFile]
    tree: list[FileNode]
    skipped_binary: list[str]
    skipped_large: list[str]
    total_files_seen: int


def _is_ignored_path(path: str) -> bool:
    segments = path.split("/")
    return any(seg in _EXTRA_IGNORED_NAMES for seg in segments)


def _should_read(node: FileNode) -> bool:
    if node.name in _SKIP_FILENAMES:
        return False
    ext = node.name.rsplit(".", 1)[-1].lower() if "." in node.name else ""
    if ext in _SKIP_EXTENSIONS:
        return False
    return True


def _flatten_files(nodes: list[FileNode], out: list[FileNode]) -> None:
    for node in nodes:
        if _is_ignored_path(node.path):
            continue
        if node.type == "directory":
            if node.children:
                _flatten_files(node.children, out)
        else:
            out.append(node)


def scan_workspace(project_id: str) -> ScanResult:
    """Read every eligible text file in a project's workspace, within budget."""
    tree = local_sandbox.list_tree(project_id)
    # NOTE: .ipynb files are NOT in _SKIP_EXTENSIONS so they are read and
    # converted below; they should NOT be added to _SKIP_EXTENSIONS.

    all_files: list[FileNode] = []
    _flatten_files(tree, all_files)
    total_files_seen = len(all_files)

    scanned: list[ScannedFile] = []
    skipped_binary: list[str] = []
    skipped_large: list[str] = []
    total_bytes = 0

    for node in all_files:
        if len(scanned) >= MAX_FILES:
            break
        if not _should_read(node):
            continue
        if total_bytes >= MAX_TOTAL_BYTES:
            skipped_large.append(node.path)
            continue

        try:
            content = local_sandbox.read_file(project_id, node.path)
        except BinaryFileError:
            skipped_binary.append(node.path)
            continue
        except NotFoundError:
            continue

        # Convert Jupyter Notebooks to readable text before budgeting / indexing.
        if node.path.endswith(".ipynb"):
            content = _notebook_to_text(content, node.path)

        raw_bytes = content.encode("utf-8", errors="ignore")
        truncated = False
        if len(raw_bytes) > MAX_FILE_BYTES:
            content = raw_bytes[:MAX_FILE_BYTES].decode("utf-8", errors="ignore")
            truncated = True

        total_bytes += len(content.encode("utf-8", errors="ignore"))
        scanned.append(
            ScannedFile(path=node.path, size=node.size or len(raw_bytes), content=content, truncated=truncated)
        )

    return ScanResult(
        files=scanned,
        tree=tree,
        skipped_binary=skipped_binary,
        skipped_large=skipped_large,
        total_files_seen=total_files_seen,
    )
