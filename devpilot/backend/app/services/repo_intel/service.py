"""
Orchestrates a Repository Intelligence scan and caches the result per
project, the same process-wide-singleton pattern `local_sandbox` already
uses (see app/services/sandbox/local.py) — fine for this local, single-user
MVP; a real cache/store would replace this before multi-instance deployment.

The cache holds both the rendered `RepoIntelBundle` (served to overview/
architecture/issues/tests endpoints) and the raw `ScanResult` (needed by
`ask()` to re-retrieve relevant excerpts per question without re-scanning).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.services.repo_intel import architecture as architecture_mod
from app.services.repo_intel import issues as issues_mod
from app.services.repo_intel import overview as overview_mod
from app.services.repo_intel import qa as qa_mod
from app.services.repo_intel import tests_suggest
from app.services.repo_intel.language import detect
from app.services.repo_intel.llm import llm_available
from app.services.repo_intel.scanner import ScanResult, scan_workspace
from app.schemas.repo_intel import AskResponse, RepoIntelBundle, ScanSummary


@dataclass
class _CacheEntry:
    scan: ScanResult
    bundle: RepoIntelBundle


class RepoIntelService:
    def __init__(self) -> None:
        self._cache: dict[str, _CacheEntry] = {}

    def scan(self, project_id: str, project_name: str) -> RepoIntelBundle:
        scan_result = scan_workspace(project_id)
        detection = detect(scan_result)

        overview = overview_mod.build_overview(project_name, scan_result, detection)
        architecture = architecture_mod.build_architecture(overview, scan_result, detection)
        issues = issues_mod.find_issues(scan_result)
        tests = tests_suggest.suggest_tests(scan_result)

        summary = ScanSummary(
            project_id=project_id,
            scanned_at=datetime.now(timezone.utc),
            file_count=overview.file_count,
            analyzed_file_count=overview.analyzed_file_count,
            issue_count=len(issues),
            issue_count_high=sum(1 for i in issues if i.severity == "high"),
            test_suggestion_count=len(tests),
            llm_enabled=llm_available(),
        )

        bundle = RepoIntelBundle(
            summary=summary,
            overview=overview,
            architecture=architecture,
            issues=issues,
            tests=tests,
        )
        self._cache[project_id] = _CacheEntry(scan=scan_result, bundle=bundle)
        return bundle

    def get(self, project_id: str) -> RepoIntelBundle | None:
        entry = self._cache.get(project_id)
        return entry.bundle if entry else None

    def ask(self, project_id: str, question: str) -> AskResponse | None:
        entry = self._cache.get(project_id)
        if entry is None:
            return None
        return qa_mod.ask(entry.scan, question)

    def invalidate(self, project_id: str) -> None:
        self._cache.pop(project_id, None)


repo_intel_service = RepoIntelService()
