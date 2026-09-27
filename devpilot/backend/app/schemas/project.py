from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProjectTemplate = Literal["python", "fastapi", "react", "node"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    template: ProjectTemplate
    description: str = Field(default="", max_length=2000)


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    template: ProjectTemplate
    description: str
    created_at: datetime
    updated_at: datetime


class ImportGitPayload(BaseModel):
    """Payload for POST /api/projects/import-git."""

    git_url: str = Field(min_length=5, max_length=500)
    name: str = Field(default="", max_length=200)  # blank → derived from repo name
    description: str = Field(default="", max_length=2000)


class UploadSummary(BaseModel):
    """Returned by the file-upload endpoint."""

    files_written: int
    skipped: list[str]  # paths rejected for safety / size
