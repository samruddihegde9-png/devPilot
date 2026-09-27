"""
LocalSandbox is the local-disk implementation of SandboxManager. It is the
only place in the backend that reads or writes project files, and the only
place a raw filesystem `Path` for a project workspace is ever constructed.

Path safety: every public method resolves its `rel_path` argument through
`_resolve()`, which:
  1. rejects absolute paths ("/etc/passwd", "C:\\Windows\\...")
  2. rejects any path segment equal to ".." (so "../../../etc/passwd" and
     "app/../../secrets" are both rejected before touching disk)
  3. resolves the final path with `Path.resolve()` and verifies it is still
     inside the project's workspace directory — a second, independent check
     in case a symlink or an OS quirk slipped past step 2.

Nothing outside `{workspaces_root}/{project_id}/` is ever read, written, or
listed by this class.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from app.config import settings
from app.schemas.file import FileNode
from app.services.sandbox.manager import (
    AlreadyExistsError,
    ExecutionResult,
    NotFoundError,
    PathTraversalError,
    SandboxManager,
)
from app.services.sandbox.templates import render_template

# Directories we never show in the file tree or allow the agent to touch.
_IGNORED_DIR_NAMES = {".git", "node_modules", "__pycache__", ".venv", ".pytest_cache"}


class BinaryFileError(Exception):
    """Raised when reading a file that is not valid UTF-8 text."""

    def __init__(self, rel_path: str):
        super().__init__(f"{rel_path!r} is not a readable text file")


class LocalSandbox(SandboxManager):
    def __init__(self, workspaces_root: str | None = None):
        self.root = Path(workspaces_root or settings.workspaces_root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Path safety
    # ------------------------------------------------------------------ #

    def _workspace_root(self, project_id: str) -> Path:
        if not project_id or any(c in project_id for c in ("/", "\\", "..")):
            raise PathTraversalError(f"Invalid project id: {project_id!r}")
        return self.root / project_id

    def _resolve(self, project_id: str, rel_path: str, must_exist: bool = False) -> Path:
        workspace = self._workspace_root(project_id)
        rel_path = (rel_path or "").strip().replace("\\", "/")

        if rel_path.startswith("/") or (len(rel_path) > 1 and rel_path[1] == ":"):
            raise PathTraversalError(f"Absolute paths are not allowed: {rel_path!r}")

        segments = [s for s in rel_path.split("/") if s not in ("", ".")]
        if any(s == ".." for s in segments):
            raise PathTraversalError(f"Path traversal is not allowed: {rel_path!r}")

        candidate = (workspace / Path(*segments)) if segments else workspace
        resolved_workspace = workspace.resolve() if workspace.exists() else workspace
        resolved = candidate.resolve() if candidate.exists() else candidate.absolute()

        try:
            resolved.relative_to(resolved_workspace)
        except ValueError as exc:
            raise PathTraversalError(f"Resolved path escapes the project workspace: {rel_path!r}") from exc

        if must_exist and not candidate.exists():
            raise NotFoundError(f"No such file or directory: {rel_path!r}")

        return candidate

    # ------------------------------------------------------------------ #
    # Workspace lifecycle
    # ------------------------------------------------------------------ #

    def create_workspace(self, project_id: str, template: str, project_name: str) -> None:
        workspace = self._workspace_root(project_id)
        if workspace.exists():
            raise AlreadyExistsError(f"Workspace already exists for project {project_id!r}")
        workspace.mkdir(parents=True)

        for rel_path, content in render_template(template, project_name).items():
            file_path = self._resolve(project_id, rel_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

    def destroy_workspace(self, project_id: str) -> None:
        workspace = self._workspace_root(project_id)
        if workspace.exists():
            shutil.rmtree(workspace)

    # ------------------------------------------------------------------ #
    # File tree
    # ------------------------------------------------------------------ #

    def list_tree(self, project_id: str) -> list[FileNode]:
        workspace = self._workspace_root(project_id)
        if not workspace.exists():
            raise NotFoundError(f"No workspace for project {project_id!r}")
        return self._list_dir(workspace, workspace)

    def _list_dir(self, dir_path: Path, workspace: Path) -> list[FileNode]:
        entries: list[FileNode] = []
        for child in sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name in _IGNORED_DIR_NAMES:
                continue
            rel = str(child.relative_to(workspace)).replace("\\", "/")
            if child.is_dir():
                entries.append(
                    FileNode(
                        name=child.name,
                        path=rel,
                        type="directory",
                        children=self._list_dir(child, workspace),
                    )
                )
            else:
                entries.append(
                    FileNode(name=child.name, path=rel, type="file", size=child.stat().st_size)
                )
        return entries

    # ------------------------------------------------------------------ #
    # File CRUD
    # ------------------------------------------------------------------ #

    def read_file(self, project_id: str, rel_path: str) -> str:
        path = self._resolve(project_id, rel_path, must_exist=True)
        if path.is_dir():
            raise NotFoundError(f"{rel_path!r} is a directory, not a file")
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise BinaryFileError(rel_path) from exc

    def write_file(self, project_id: str, rel_path: str, content: str) -> None:
        path = self._resolve(project_id, rel_path)
        if path.is_dir():
            raise NotFoundError(f"{rel_path!r} is a directory, not a file")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def create_entry(self, project_id: str, rel_path: str, entry_type: str, content: str = "") -> None:
        path = self._resolve(project_id, rel_path)
        if path.exists():
            raise AlreadyExistsError(f"{rel_path!r} already exists")
        if entry_type == "directory":
            path.mkdir(parents=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def delete_entry(self, project_id: str, rel_path: str) -> None:
        path = self._resolve(project_id, rel_path, must_exist=True)
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def rename_entry(self, project_id: str, rel_path: str, new_rel_path: str) -> None:
        src = self._resolve(project_id, rel_path, must_exist=True)
        dst = self._resolve(project_id, new_rel_path)
        if dst.exists():
            raise AlreadyExistsError(f"{new_rel_path!r} already exists")
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)

    def entry_type(self, project_id: str, rel_path: str) -> str:
        path = self._resolve(project_id, rel_path, must_exist=True)
        return "directory" if path.is_dir() else "file"

    # ------------------------------------------------------------------ #
    # Execution — implemented in Phase 3
    # ------------------------------------------------------------------ #

    def execute(self, project_id: str, command: list[str], timeout_seconds: int) -> ExecutionResult:
        raise NotImplementedError(
            "Command execution is not implemented yet. It arrives in Phase 3 (sandboxed "
            "subprocess execution with timeouts and output limits)."
        )


# Simple process-wide singleton; swap for DI if the app grows multiple sandbox backends.
local_sandbox = LocalSandbox()
