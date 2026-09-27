from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ImportantFile(BaseModel):
    path: str
    reason: str


class KeyModule(BaseModel):
    path: str
    file_count: int


class DependencyInfo(BaseModel):
    python: list[str] = Field(default_factory=list)
    node: list[str] = Field(default_factory=list)


class RepoOverview(BaseModel):
    project_name: str
    primary_language: str
    languages: dict[str, int]
    frameworks: list[str]
    file_count: int
    analyzed_file_count: int
    total_lines: int
    important_files: list[ImportantFile]
    key_modules: list[KeyModule]
    dependencies: DependencyInfo
    skipped_binary_count: int
    skipped_large_count: int


class ArchitectureModule(BaseModel):
    path: str
    file_count: int
    description: str
    x: float
    y: float


class ArchitectureRelation(BaseModel):
    source: str
    target: str


class Architecture(BaseModel):
    explanation: str
    explanation_source: Literal["ai", "heuristic"]
    modules: list[ArchitectureModule]
    relations: list[ArchitectureRelation]


IssueSeverity = Literal["low", "medium", "high"]


class Issue(BaseModel):
    file: str
    line: Optional[int] = None
    function: Optional[str] = None
    description: str
    severity: IssueSeverity
    suggested_fix: str
    rule_id: str


class TestSuggestion(BaseModel):
    target_file: str
    target_symbol: str
    description: str
    suggested_cases: list[str]
    generated_test_code: Optional[str] = None
    generated_test_path: Optional[str] = None


class UsedSnippet(BaseModel):
    path: str
    start_line: int
    end_line: int
    snippet: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    mode: Literal["ai", "retrieval", "none"]
    used_files: list[UsedSnippet]


class ScanSummary(BaseModel):
    project_id: str
    scanned_at: datetime
    file_count: int
    analyzed_file_count: int
    issue_count: int
    issue_count_high: int
    test_suggestion_count: int
    llm_enabled: bool


class RepoIntelBundle(BaseModel):
    """Everything produced by a single scan, cached and served from this."""

    summary: ScanSummary
    overview: RepoOverview
    architecture: Architecture
    issues: list[Issue]
    tests: list[TestSuggestion]
