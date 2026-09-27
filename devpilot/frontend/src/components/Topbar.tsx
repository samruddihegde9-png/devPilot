import { ArrowLeft, Settings, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

import type { Project } from "../types/project";

interface Props {
  project: Project | null;
}

export default function Topbar({ project }: Props) {
  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b border-ink-800 bg-ink-900 px-3">
      <div className="flex items-center gap-3">
        <Link
          to="/"
          className="flex items-center gap-1 rounded px-1.5 py-1 text-ink-400 hover:bg-ink-800 hover:text-ink-100"
          title="Back to projects"
        >
          <ArrowLeft size={15} />
        </Link>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[13px] font-semibold tracking-tight text-ink-100">DEVPILOT</span>
          {project && (
            <>
              <span className="text-ink-600">/</span>
              <span className="text-[13px] text-ink-300">{project.name}</span>
              <span className="rounded border border-ink-700 px-1.5 py-0.5 text-[10px] uppercase text-ink-400">
                {project.template}
              </span>
            </>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1">
        {project && (
          <Link
            to={`/repo-intel/${project.id}`}
            className="flex items-center gap-1.5 rounded-md border border-ink-700 px-2.5 py-1.5 text-[12px] font-medium text-ink-300 transition-colors hover:border-amber-500/50 hover:text-amber-300"
            title="Scan this project and ask questions about it"
          >
            <Sparkles size={13} />
            Repository Intelligence
          </Link>
        )}
        <button
          className="rounded p-1.5 text-ink-400 hover:bg-ink-800 hover:text-ink-100"
          title="Settings (not implemented yet)"
        >
          <Settings size={15} />
        </button>
      </div>
    </header>
  );
}
