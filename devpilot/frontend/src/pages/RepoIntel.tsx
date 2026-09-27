import { AlertTriangle, FlaskConical, LayoutGrid, Loader2, MessageSquare, Network, ScanSearch } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import AskPanel from "../components/repo-intel/AskPanel";
import ArchitecturePanel from "../components/repo-intel/ArchitecturePanel";
import IssuesPanel from "../components/repo-intel/IssuesPanel";
import OverviewPanel from "../components/repo-intel/OverviewPanel";
import TestsPanel from "../components/repo-intel/TestsPanel";
import { api, ApiError } from "../services/api";
import type { Architecture, AskResponse, Issue, RepoOverview, ScanSummary, TestSuggestion } from "../types/repoIntel";
import type { Project } from "../types/project";

type TabId = "overview" | "architecture" | "issues" | "tests" | "ask";

const TABS: { id: TabId; label: string; icon: typeof LayoutGrid }[] = [
  { id: "overview", label: "Overview", icon: LayoutGrid },
  { id: "architecture", label: "Architecture", icon: Network },
  { id: "issues", label: "Issues", icon: AlertTriangle },
  { id: "tests", label: "Tests", icon: FlaskConical },
  { id: "ask", label: "Ask DevPilot", icon: MessageSquare },
];

export default function RepoIntel() {
  const { projectId } = useParams<{ projectId: string }>();

  const [project, setProject] = useState<Project | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [scanning, setScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [summary, setSummary] = useState<ScanSummary | null>(null);
  const [checkedForExistingScan, setCheckedForExistingScan] = useState(false);

  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [overview, setOverview] = useState<RepoOverview | null>(null);
  const [architecture, setArchitecture] = useState<Architecture | null>(null);
  const [issues, setIssues] = useState<Issue[] | null>(null);
  const [tests, setTests] = useState<TestSuggestion[] | null>(null);
  const [tabLoading, setTabLoading] = useState(false);
  const [tabError, setTabError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    (async () => {
      try {
        const p = await api.getProject(projectId);
        if (!cancelled) setProject(p);
      } catch {
        if (!cancelled) setLoadError("Project not found.");
      }
      // A previous scan this session is still cached server-side; try to pick it up
      // so reopening this tab doesn't force a re-scan.
      try {
        const existing = await api.getRepoSummary(projectId);
        if (!cancelled) setSummary(existing);
      } catch {
        // Not scanned yet this session — normal, the Scan button below handles it.
      } finally {
        if (!cancelled) setCheckedForExistingScan(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const runScan = useCallback(async () => {
    if (!projectId) return;
    setScanning(true);
    setScanError(null);
    try {
      const result = await api.scanRepo(projectId);
      setSummary(result);
      setOverview(null);
      setArchitecture(null);
      setIssues(null);
      setTests(null);
      setActiveTab("overview");
    } catch (err) {
      setScanError(
        err instanceof ApiError ? `Scan failed (${err.status}): ${err.message}` : "Could not scan the repository."
      );
    } finally {
      setScanning(false);
    }
  }, [projectId]);

  const loadTab = useCallback(
    async (tab: TabId) => {
      if (!projectId || !summary) return;
      setTabError(null);
      try {
        if (tab === "overview" && !overview) {
          setTabLoading(true);
          setOverview(await api.getRepoOverview(projectId));
        } else if (tab === "architecture" && !architecture) {
          setTabLoading(true);
          setArchitecture(await api.getRepoArchitecture(projectId));
        } else if (tab === "issues" && !issues) {
          setTabLoading(true);
          setIssues(await api.getRepoIssues(projectId));
        } else if (tab === "tests" && !tests) {
          setTabLoading(true);
          setTests(await api.getRepoTests(projectId));
        }
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.status === 409) {
            // In-memory cache was cleared (server restart / first load without scanning).
            setTabError("The scan results are no longer cached. Click Scan Repository to run a fresh scan.");
          } else {
            setTabError(`Could not load ${tab} (${err.status}): ${err.message}`);
          }
        } else {
          setTabError("Could not load this tab — is the backend still running?");
        }
      } finally {
        setTabLoading(false);
      }
    },
    [projectId, summary, overview, architecture, issues, tests]
  );

  useEffect(() => {
    if (summary) void loadTab(activeTab);
  }, [activeTab, summary, loadTab]);

  async function handleAsk(question: string): Promise<AskResponse> {
    if (!projectId) throw new Error("No project");
    return api.askRepo(projectId, question);
  }

  if (loadError) {
    return <div className="flex h-screen items-center justify-center text-sm text-ink-400">{loadError}</div>;
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <header className="flex h-12 shrink-0 items-center justify-between border-b border-ink-800 bg-ink-900 px-3">
        <div className="flex items-center gap-2">
          <Link
            to={projectId ? `/workspace/${projectId}` : "/"}
            className="rounded px-1.5 py-1 text-ink-400 hover:bg-ink-800 hover:text-ink-100"
          >
            ← Workspace
          </Link>
          <span className="text-ink-600">/</span>
          <ScanSearch size={14} className="text-amber-400" />
          <span className="text-[13px] font-medium text-ink-100">Repository Intelligence</span>
          {project && <span className="text-[13px] text-ink-500">· {project.name}</span>}
        </div>
        <button
          onClick={runScan}
          disabled={scanning}
          className="flex items-center gap-1.5 rounded-md bg-amber-500 px-3 py-1.5 text-xs font-medium text-ink-950 transition-colors hover:bg-amber-400 disabled:opacity-50"
        >
          {scanning && <Loader2 size={13} className="animate-spin" />}
          {summary ? "Re-scan" : "Scan Repository"}
        </button>
      </header>

      {!checkedForExistingScan ? (
        <div className="flex flex-1 items-center justify-center text-sm text-ink-500">Loading…</div>
      ) : !summary ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
          <ScanSearch size={28} className="text-ink-600" />
          <p className="text-sm text-ink-300">This project hasn't been scanned yet.</p>
          <p className="max-w-sm text-xs text-ink-500">
            Scanning reads the files in this project's workspace and builds an overview, an architecture summary,
            a list of potential issues, and test suggestions — nothing leaves your machine unless{" "}
            <code className="rounded bg-ink-800 px-1 py-0.5">OPENAI_API_KEY</code> is configured.
          </p>
          {scanError && <p className="text-xs text-signal-red">{scanError}</p>}
          <button
            onClick={runScan}
            disabled={scanning}
            className="mt-1 flex items-center gap-1.5 rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-ink-950 hover:bg-amber-400 disabled:opacity-50"
          >
            {scanning && <Loader2 size={14} className="animate-spin" />}
            Scan Repository
          </button>
        </div>
      ) : (
        <div className="flex min-h-0 flex-1">
          <nav className="w-44 shrink-0 border-r border-ink-800 bg-ink-900 p-2">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-[13px] ${
                    active ? "bg-amber-500/10 text-amber-300" : "text-ink-300 hover:bg-ink-800 hover:text-ink-100"
                  }`}
                >
                  <Icon size={14} />
                  {tab.label}
                </button>
              );
            })}

            <div className="mt-4 border-t border-ink-800 pt-3 text-[11px] text-ink-500">
              <p>{summary.analyzed_file_count} files analyzed</p>
              {summary.issue_count_high > 0 && (
                <p className="text-signal-red">{summary.issue_count_high} high-severity issue(s)</p>
              )}
              {!summary.llm_enabled && <p className="mt-2 text-ink-600">Running without an LLM key (heuristic mode).</p>}
            </div>
          </nav>

          <div className="min-h-0 flex-1 overflow-y-auto p-5">
            {tabError && <p className="mb-3 text-xs text-signal-red">{tabError}</p>}
            {tabLoading && (
              <div className="flex items-center gap-2 text-sm text-ink-500">
                <Loader2 size={14} className="animate-spin" /> Loading…
              </div>
            )}

            {!tabLoading && activeTab === "overview" && overview && <OverviewPanel overview={overview} />}
            {!tabLoading && activeTab === "architecture" && architecture && (
              <ArchitecturePanel architecture={architecture} />
            )}
            {!tabLoading && activeTab === "issues" && issues && <IssuesPanel issues={issues} />}
            {!tabLoading && activeTab === "tests" && tests && <TestsPanel tests={tests} />}
            {activeTab === "ask" && (
              <div className="h-full">
                <AskPanel onAsk={handleAsk} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
