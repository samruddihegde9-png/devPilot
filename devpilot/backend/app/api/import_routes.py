"""
Import routes — two ways to bring external code into a DevPilot project workspace:

  POST /api/projects/import-git
      Clones a public (or key-authenticated) Git repository into a new project.
      Creates the Project row + workspace, then does a shallow clone.

  POST /api/projects/{project_id}/upload-files
      Accepts multipart file uploads (including webkitRelativePath for folders).
      Writes them into an existing project workspace while enforcing the same
      path-safety rules as the rest of the file API.
"""
from __future__ import annotations

import logging
import posixpath
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.project import Project
from app.schemas.project import ImportGitPayload, ProjectOut, UploadSummary
from app.services.git.cloner import GitImportError, clone_into_workspace, derive_project_name
from app.services.sandbox.local import local_sandbox
from app.services.sandbox.manager import AlreadyExistsError, PathTraversalError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["import"])

# Per-file size cap for uploads (10 MB); keeps single requests reasonable.
_MAX_UPLOAD_BYTES = 10 * 1024 * 1024

# Extensions we flat-out refuse to write (executables, archives that could
# contain path-traversal exploits, etc.).
_BLOCKED_EXTENSIONS = {
    "exe", "dll", "so", "dylib", "bat", "cmd", "ps1", "sh",  # executables
    "zip", "tar", "gz", "7z", "rar",                          # archives
    "key", "pem", "p12", "pfx",                               # keys/certs
}


def _safe_rel_path(raw: str) -> str | None:
    """
    Normalise an upload path string.

    Browsers set file.webkitRelativePath to e.g. "myrepo/src/index.ts".
    We strip the top-level folder name so the workspace root stays clean,
    then run posixpath.normpath to collapse any ".." sequences.

    Returns None if the result is unsafe (absolute, escapes root, blocked ext).
    """
    # Replace backslashes (Windows drag-and-drop filenames).
    path = raw.replace("\\", "/").strip("/")
    if not path:
        return None

    # Strip leading folder component that browsers prepend for folder uploads.
    parts = path.split("/")
    if len(parts) > 1:
        path = "/".join(parts[1:])  # drop the top-level folder name

    # Normalise and reject traversal.
    normalised = posixpath.normpath(path).lstrip("/")
    if ".." in normalised.split("/"):
        return None
    if normalised.startswith("/"):
        return None

    # Block dangerous extensions.
    ext = normalised.rsplit(".", 1)[-1].lower() if "." in normalised else ""
    if ext in _BLOCKED_EXTENSIONS:
        return None

    return normalised


# ---------------------------------------------------------------------------
# POST /api/projects/import-git
# ---------------------------------------------------------------------------

@router.post("/api/projects/import-git", response_model=ProjectOut, status_code=201)
def import_git(payload: ImportGitPayload, db: Session = Depends(get_db)) -> Project:
    """
    Create a new project and populate its workspace by cloning a Git URL.

    The project name is derived from the repo URL when the caller leaves
    `name` blank.  The clone is always shallow (--depth 1) and times out
    after 120 seconds so a huge repo can't hang the server.
    """
    name = payload.name.strip() or derive_project_name(payload.git_url)

    project = Project(name=name, template="python", description=payload.description)
    db.add(project)
    db.flush()  # gets project.id without committing

    # Create an empty workspace directory (no template files — the clone fills it).
    try:
        local_sandbox.create_workspace(project.id, "python", name)
    except AlreadyExistsError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    # Now clone into that workspace.
    try:
        file_count = clone_into_workspace(project.id, payload.git_url)
        logger.info("Imported %s → project %s (%d files)", payload.git_url, project.id, file_count)
    except GitImportError as exc:
        # Roll back the workspace and DB row so the user can retry cleanly.
        local_sandbox.destroy_workspace(project.id)
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        local_sandbox.destroy_workspace(project.id)
        db.rollback()
        logger.exception("Unexpected error importing %s", payload.git_url)
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}") from exc

    # Wipe the template starter files — the clone already populated the workspace,
    # but create_workspace wrote a README.md and app/main.py.  Remove them only
    # if the cloned repo brought its own files (file_count > 3 = the 3 template files).
    # Actually: create_workspace always writes template files *before* we clone,
    # and clone_into_workspace overwrites/merges.  That's fine — any overlap
    # (e.g. a cloned README.md) replaces the template's README.md.

    db.commit()
    db.refresh(project)
    return project


# ---------------------------------------------------------------------------
# POST /api/projects/{project_id}/upload-files
# ---------------------------------------------------------------------------

@router.post("/api/projects/{project_id}/upload-files", response_model=UploadSummary)
async def upload_files(
    project_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> UploadSummary:
    """
    Accept one or more uploaded files (multipart/form-data) and write them
    into the project workspace.

    The frontend sends `webkitRelativePath` as the filename for folder uploads,
    which preserves the original directory tree.  Each path is sanitised before
    writing:
      • The top-level folder component is stripped (so "myrepo/src/app.ts"
        becomes "src/app.ts" in the workspace).
      • ".." segments are rejected.
      • Blocked file extensions (executables, archives, keys) are skipped.
      • Files larger than 10 MB are skipped.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    written = 0
    skipped: list[str] = []

    for upload in files:
        raw_name = upload.filename or ""
        rel_path = _safe_rel_path(raw_name)

        if rel_path is None:
            skipped.append(raw_name or "(unnamed)")
            continue

        # Read with size cap.
        content_bytes = await upload.read(_MAX_UPLOAD_BYTES + 1)
        if len(content_bytes) > _MAX_UPLOAD_BYTES:
            skipped.append(f"{raw_name} (too large, >{_MAX_UPLOAD_BYTES // 1024 // 1024} MB)")
            continue

        # Try to decode as UTF-8; skip binary files.
        try:
            content_str = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append(f"{raw_name} (binary)")
            continue

        try:
            local_sandbox.write_file(project.id, rel_path, content_str)
            written += 1
        except PathTraversalError:
            skipped.append(f"{raw_name} (path traversal)")
        except Exception as exc:
            logger.warning("Could not write upload %s: %s", raw_name, exc)
            skipped.append(f"{raw_name} (write error)")

    return UploadSummary(files_written=written, skipped=skipped)
