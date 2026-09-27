from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.project import Project
from app.schemas.file import FileContent, FileCreate, FileNode, FileRename, FileWrite
from app.services.sandbox.local import BinaryFileError, local_sandbox
from app.services.sandbox.manager import AlreadyExistsError, NotFoundError, PathTraversalError

router = APIRouter(prefix="/api/projects/{project_id}/files", tags=["files"])


def _require_project(project_id: str, db: Session) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=list[FileNode])
def get_file_tree(project_id: str, db: Session = Depends(get_db)) -> list[FileNode]:
    _require_project(project_id, db)
    try:
        return local_sandbox.list_tree(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{path:path}", response_model=FileContent)
def read_file(project_id: str, path: str, db: Session = Depends(get_db)) -> FileContent:
    _require_project(project_id, db)
    try:
        content = local_sandbox.read_file(project_id, path)
    except PathTraversalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except BinaryFileError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    return FileContent(path=path, content=content)


@router.put("/{path:path}", response_model=FileContent)
def write_file(project_id: str, path: str, payload: FileWrite, db: Session = Depends(get_db)) -> FileContent:
    _require_project(project_id, db)
    try:
        local_sandbox.write_file(project_id, path, payload.content)
    except PathTraversalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileContent(path=path, content=payload.content)


@router.post("", response_model=FileNode, status_code=201)
def create_file(project_id: str, payload: FileCreate, db: Session = Depends(get_db)) -> FileNode:
    _require_project(project_id, db)
    try:
        local_sandbox.create_entry(project_id, payload.path, payload.type, payload.content)
    except PathTraversalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    name = payload.path.rstrip("/").split("/")[-1]
    return FileNode(name=name, path=payload.path, type=payload.type)


@router.delete("/{path:path}", status_code=204)
def delete_file(project_id: str, path: str, db: Session = Depends(get_db)) -> None:
    _require_project(project_id, db)
    try:
        local_sandbox.delete_entry(project_id, path)
    except PathTraversalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{path:path}", response_model=FileNode)
def rename_file(project_id: str, path: str, payload: FileRename, db: Session = Depends(get_db)) -> FileNode:
    _require_project(project_id, db)
    try:
        local_sandbox.rename_entry(project_id, path, payload.new_path)
    except PathTraversalError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    name = payload.new_path.rstrip("/").split("/")[-1]
    entry_type = local_sandbox.entry_type(project_id, payload.new_path)
    return FileNode(name=name, path=payload.new_path, type=entry_type)
