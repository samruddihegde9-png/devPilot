import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.project import Project
from app.schemas.repo_intel import (
    Architecture,
    AskRequest,
    AskResponse,
    Issue,
    RepoOverview,
    ScanSummary,
    TestSuggestion,
)
from app.services.repo_intel.service import repo_intel_service
from app.services.sandbox.manager import NotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/repo-intel", tags=["repo-intel"])

_NOT_SCANNED_DETAIL = "This project hasn't been scanned yet. POST /repo-intel/scan first."


def _require_project(project_id: str, db: Session) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/scan", response_model=ScanSummary, status_code=201)
def scan_repository(project_id: str, db: Session = Depends(get_db)) -> ScanSummary:
    project = _require_project(project_id, db)
    try:
        bundle = repo_intel_service.scan(project_id, project.name)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Scan failed for project %s", project_id)
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}") from exc
    return bundle.summary


@router.get("/summary", response_model=ScanSummary)
def get_summary(project_id: str, db: Session = Depends(get_db)) -> ScanSummary:
    """Returns the cached summary from the last scan, without re-scanning.

    Lets the frontend pick up an already-scanned project (e.g. after
    navigating away and back) without paying for a fresh scan.
    """
    _require_project(project_id, db)
    bundle = repo_intel_service.get(project_id)
    if bundle is None:
        raise HTTPException(status_code=409, detail=_NOT_SCANNED_DETAIL)
    return bundle.summary


@router.get("/overview", response_model=RepoOverview)
def get_overview(project_id: str, db: Session = Depends(get_db)) -> RepoOverview:
    _require_project(project_id, db)
    bundle = repo_intel_service.get(project_id)
    if bundle is None:
        raise HTTPException(status_code=409, detail=_NOT_SCANNED_DETAIL)
    return bundle.overview


@router.get("/architecture", response_model=Architecture)
def get_architecture(project_id: str, db: Session = Depends(get_db)) -> Architecture:
    _require_project(project_id, db)
    bundle = repo_intel_service.get(project_id)
    if bundle is None:
        raise HTTPException(status_code=409, detail=_NOT_SCANNED_DETAIL)
    return bundle.architecture


@router.get("/issues", response_model=list[Issue])
def get_issues(project_id: str, db: Session = Depends(get_db)) -> list[Issue]:
    _require_project(project_id, db)
    bundle = repo_intel_service.get(project_id)
    if bundle is None:
        raise HTTPException(status_code=409, detail=_NOT_SCANNED_DETAIL)
    return bundle.issues


@router.get("/tests", response_model=list[TestSuggestion])
def get_tests(project_id: str, db: Session = Depends(get_db)) -> list[TestSuggestion]:
    _require_project(project_id, db)
    bundle = repo_intel_service.get(project_id)
    if bundle is None:
        raise HTTPException(status_code=409, detail=_NOT_SCANNED_DETAIL)
    return bundle.tests


@router.post("/ask", response_model=AskResponse)
def ask_repository(project_id: str, payload: AskRequest, db: Session = Depends(get_db)) -> AskResponse:
    _require_project(project_id, db)
    response = repo_intel_service.ask(project_id, payload.question)
    if response is None:
        raise HTTPException(status_code=409, detail=_NOT_SCANNED_DETAIL)
    return response
