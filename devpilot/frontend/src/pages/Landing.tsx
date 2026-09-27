import { FolderGit2, GitBranch, Loader2, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import CreateProjectModal from "../components/CreateProjectModal";
import ImportModal from "../components/ImportModal";
import { api, ApiError } from "../services/api";
import type { Project, ProjectTemplate } from "../types/project";

const DEMO_PROJECT_NAME = "Demo FastAPI App";

export default function Landing() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  useEffect(() => {
    void loadProjects();
  }, []);

  async function loadProjects() {
    try {
      const data = await api.listProjects();
      setProjects(data);
      setLoadError(null);
    } catch (err) {
      setLoadError(
        err instanceof ApiError
          ? `Could not reach the backend (${err.status}).`
          : "Could not reach the backend. Is it running on the configured API URL?"
      );
      setProjects([]);
    }
  }

  async function handleCreate(name: string, template: ProjectTemplate) {
    const project = await api.createProject({ name, template });
    setModalOpen(false);
    navigate(`/workspace/${project.id}`);
  }

  function handleImported(project: Project) {
    setImportOpen(false);
    void loadProjects();
    navigate(`/workspace/${project.id}`);
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Delete this project and its workspace? This can't be undone.")) return;
    await api.deleteProject(id);
    void loadProjects();
  }

  async function handleTryDemo() {
    setDemoLoading(true);
    try {
      const existing = (projects ?? []).find((p) => p.name === DEMO_PROJECT_NAME);
      if (existing) {
        navigate(`/workspace/${existing.id}`);
        return;
      }
      const project = await api.createProject({
        name: DEMO_PROJECT_NAME,
        template: "fastapi",
        description: "A small FastAPI app for trying out DevPilot.",
      });
      navigate(`/workspace/${project.id}`);
    } catch {
      setLoadError("Could not create the demo project. Is the backend running?");
    } finally {
      setDemoLoading(false);
    }
  }

  return (
    <div className="min-h-full bg-ink-950">
      <div className="mx-auto max-w-3xl px-6 pb-24 pt-24">
        <div className="mb-2 flex items-center gap-2 font-mono text-xs font-semibold tracking-wide text-amber-400">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
          DEVPILOT
        </div>

        <h1 className="max-w-xl text-3xl font-semibold leading-tight tracking-tight text-ink-100 sm:text-4xl">
          Build with an AI engineer, not just an AI chatbot.
        </h1>
        <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-ink-300">
          DevPilot plans, writes, tests and debugs code inside isolated project workspaces.
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <button
            onClick={() => setModalOpen(true)}
            className="flex items-center gap-1.5 rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-ink-950 transition-colors hover:bg-amber-400"
          >
            <Plus size={15} />
            New Project
          </button>
          <button
            onClick={() => setImportOpen(true)}
            className="flex items-center gap-1.5 rounded-md border border-ink-700 px-4 py-2 text-sm font-medium text-ink-200 transition-colors hover:border-ink-500 hover:text-ink-100"
          >
            <GitBranch size={15} />
            Import
          </button>
          <button
            onClick={handleTryDemo}
            disabled={demoLoading}
            className="flex items-center gap-1.5 rounded-md border border-ink-700 px-4 py-2 text-sm font-medium text-ink-200 transition-colors hover:border-ink-500 hover:text-ink-100 disabled:opacity-50"
          >
            {demoLoading && <Loader2 size={14} className="animate-spin" />}
            Try Demo
          </button>
        </div>

        <div className="mt-16">
          <p className="mb-3 text-xs font-medium uppercase tracking-wide text-ink-500">Your projects</p>

          {loadError && (
            <p className="rounded-md border border-signal-red/30 bg-signal-red/5 px-3 py-2 text-xs text-signal-red">
              {loadError}
            </p>
          )}

          {projects === null && !loadError && <p className="text-sm text-ink-500">Loading…</p>}

          {projects !== null && projects.length === 0 && !loadError && (
            <p className="rounded-md border border-dashed border-ink-700 px-3 py-6 text-center text-sm text-ink-500">
              No projects yet. Create one to get started.
            </p>
          )}

          <ul className="divide-y divide-ink-800 rounded-md border border-ink-800">
            {(projects ?? []).map((p) => (
              <li
                key={p.id}
                onClick={() => navigate(`/workspace/${p.id}`)}
                className="group flex cursor-pointer items-center justify-between gap-3 bg-ink-900/40 px-4 py-3 transition-colors hover:bg-ink-900"
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <FolderGit2 size={15} className="shrink-0 text-ink-400" />
                  <div className="overflow-hidden">
                    <p className="truncate text-sm text-ink-100">{p.name}</p>
                    <p className="truncate text-xs text-ink-500">
                      {p.template} · updated {new Date(p.updated_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => handleDelete(p.id, e)}
                  className="shrink-0 rounded p-1.5 text-ink-500 opacity-0 hover:bg-ink-800 hover:text-signal-red group-hover:opacity-100"
                  title="Delete project"
                >
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <CreateProjectModal open={modalOpen} onClose={() => setModalOpen(false)} onCreate={handleCreate} />
      <ImportModal open={importOpen} onClose={() => setImportOpen(false)} onImported={handleImported} />
    </div>
  );
}
