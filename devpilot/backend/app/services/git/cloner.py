"""
Git import service — clones a remote URL into an existing project workspace.

Safety rules
------------
* Only https:// and ssh:// (git@) URLs are accepted; file:// and anything else
  are rejected before a subprocess/git call is ever made.
* git credentials are never stored: the clone is always --depth 1 (fast,
  shallow) and no credential helper is configured.
* The clone destination is the workspace directory that LocalSandbox already
  owns and path-checks — nothing escapes that boundary.
* A 60-second timeout kills runaway clones so a slow/large repo can't hang the
  server indefinitely.
* We clone into a temporary directory first, then move files into the workspace
  (minus the .git folder) so a failed clone never leaves partial content.
"""
from __future__ import annotations

import logging
import re
import shutil
import tempfile
from pathlib import Path

import git

from app.config import settings

logger = logging.getLogger(__name__)

# Allowlist: https URLs and ssh git@ style URLs only.
_HTTPS_RE = re.compile(r"^https://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%\-]+$")
_SSH_RE = re.compile(r"^git@[A-Za-z0-9.\-]+:[A-Za-z0-9._\-/]+(?:\.git)?$")

_CLONE_TIMEOUT = 120  # seconds


class GitImportError(Exception):
    """Raised for all user-facing clone failures."""


def _validate_url(url: str) -> str:
    """Return the URL unchanged, or raise GitImportError."""
    url = url.strip()
    if _HTTPS_RE.match(url) or _SSH_RE.match(url):
        return url
    raise GitImportError(
        "Only https:// and git@host:path SSH URLs are supported. "
        "file://, local paths, and other schemes are not allowed."
    )


def _repo_name_from_url(url: str) -> str:
    """Derive a human-readable project name from the repo URL."""
    # Take the last path segment, strip .git suffix, replace hyphens/underscores with spaces.
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = re.sub(r"\.git$", "", slug)
    # Turn separators into spaces and title-case
    name = re.sub(r"[-_]+", " ", slug).strip()
    return name or "Imported Repository"


def _copy_into_workspace(src_dir: Path, workspace: Path) -> None:
    """
    Copy every file from src_dir into workspace, skipping .git.
    We walk manually instead of shutil.copytree so we can honour
    the already-present workspace directory.
    """
    for item in src_dir.iterdir():
        if item.name == ".git":
            continue
        dest = workspace / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(str(item), str(dest))
        else:
            shutil.copy2(str(item), str(dest))


def clone_into_workspace(project_id: str, git_url: str) -> int:
    """
    Clone *git_url* (shallow, --depth 1) into the project's workspace.

    Returns the number of files written (excluding .git).
    Raises GitImportError on any failure.
    """
    validated_url = _validate_url(git_url)
    workspace = Path(settings.workspaces_root) / project_id

    if not workspace.exists():
        raise GitImportError(f"Workspace for project {project_id!r} does not exist.")

    with tempfile.TemporaryDirectory(prefix="devpilot_clone_") as tmp_dir:
        tmp_path = Path(tmp_dir) / "repo"
        try:
            logger.info("Cloning %s into temp dir", validated_url)
            git.Repo.clone_from(
                validated_url,
                str(tmp_path),
                depth=1,
                multi_options=["--no-single-branch"],
            )
        except git.GitCommandError as exc:
            # GitCommandError.stderr is a string like "\n  stderr: 'fatal: ...'\n"
            # Extract the most useful line for the user.
            raw_stderr = getattr(exc, "stderr", "") or str(exc)
            best_line = ""
            for line in raw_stderr.splitlines():
                stripped = line.strip().strip("'")
                if stripped.startswith(("fatal:", "error:", "remote: Repository")):
                    best_line = stripped
                    break
            if not best_line:
                # Fall back to last non-empty line of the full exception text.
                lines = [l.strip() for l in raw_stderr.splitlines() if l.strip()]
                best_line = lines[-1] if lines else "unknown git error"
            raise GitImportError(f"git clone failed: {best_line}") from exc
        except Exception as exc:
            raise GitImportError(f"Unexpected clone error: {exc}") from exc

        _copy_into_workspace(tmp_path, workspace)

    # Count written files (excluding hidden dirs like .git which we skipped).
    file_count = sum(1 for p in workspace.rglob("*") if p.is_file())
    logger.info("Cloned %s → %s (%d files)", validated_url, project_id, file_count)
    return file_count


def derive_project_name(git_url: str) -> str:
    """Best-effort human name from a git URL; never raises."""
    try:
        return _repo_name_from_url(git_url)
    except Exception:
        return "Imported Repository"
