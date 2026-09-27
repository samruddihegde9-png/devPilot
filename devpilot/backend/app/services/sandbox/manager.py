"""
`SandboxManager` is the boundary between DevPilot's application code (API
routes today, the agent's tools starting Phase 2) and wherever a project's
files actually live and its commands actually run.

`LocalSandbox` (local.py) is the only implementation in this phase: it reads
and writes real files on the host's disk, scoped to one directory per
project. It is intentionally the *only* place in the codebase that touches
the filesystem for project content, so every path-safety rule lives in one
file.

`DockerSandbox` / `CloudSandbox` (Phase 2's "22. DOCKER SANDBOX") can later
implement this same interface — routing `execute()` into a locked-down
container instead of a subprocess — without any caller needing to change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.file import FileNode


@dataclass
class ExecutionResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float
    timed_out: bool = False


class SandboxError(Exception):
    """Base class for sandbox failures (bad path, missing file, etc.)."""


class PathTraversalError(SandboxError):
    """Raised when a requested path would escape the project workspace."""


class NotFoundError(SandboxError):
    """Raised when a requested file or directory does not exist."""


class AlreadyExistsError(SandboxError):
    """Raised when creating a file/directory that already exists."""


class SandboxManager(ABC):
    @abstractmethod
    def create_workspace(self, project_id: str, template: str, project_name: str) -> None:
        """Create the workspace directory and seed it with starter files."""

    @abstractmethod
    def destroy_workspace(self, project_id: str) -> None:
        """Permanently delete a project's workspace directory."""

    @abstractmethod
    def list_tree(self, project_id: str) -> list[FileNode]:
        """Return the full file tree for a project, rooted at its workspace."""

    @abstractmethod
    def read_file(self, project_id: str, rel_path: str) -> str:
        ...

    @abstractmethod
    def write_file(self, project_id: str, rel_path: str, content: str) -> None:
        ...

    @abstractmethod
    def create_entry(self, project_id: str, rel_path: str, entry_type: str, content: str = "") -> None:
        ...

    @abstractmethod
    def delete_entry(self, project_id: str, rel_path: str) -> None:
        ...

    @abstractmethod
    def rename_entry(self, project_id: str, rel_path: str, new_rel_path: str) -> None:
        ...

    @abstractmethod
    def entry_type(self, project_id: str, rel_path: str) -> str:
        """Return "file" or "directory" for an existing entry."""

    @abstractmethod
    def execute(self, project_id: str, command: list[str], timeout_seconds: int) -> ExecutionResult:
        """
        Run a command inside the project's workspace. Implemented starting
        Phase 3 ("17. TESTING" / "19. TERMINAL"); LocalSandbox raises
        NotImplementedError for now so nothing pretends to execute code.
        """
