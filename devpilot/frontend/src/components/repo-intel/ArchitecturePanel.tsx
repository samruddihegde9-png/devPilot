import { Sparkles } from "lucide-react";

import type { Architecture } from "../../types/repoIntel";
import ModuleGraph from "./ModuleGraph";

export default function ArchitecturePanel({ architecture }: { architecture: Architecture }) {
  return (
    <div className="space-y-6">
      <div className="rounded-md border border-ink-800 bg-ink-850 p-4">
        <div className="mb-2 flex items-center gap-1.5">
          {architecture.explanation_source === "ai" && <Sparkles size={12} className="text-amber-400" />}
          <p className="text-[11px] font-medium uppercase tracking-wide text-ink-500">
            {architecture.explanation_source === "ai" ? "AI summary, grounded in the repo scan" : "Summary (heuristic)"}
          </p>
        </div>
        <p className="text-[13px] leading-relaxed text-ink-200">{architecture.explanation}</p>
      </div>

      <div>
        <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-ink-500">Module diagram</p>
        <ModuleGraph modules={architecture.modules} relations={architecture.relations} />
      </div>

      <div>
        <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-ink-500">Modules</p>
        <div className="grid gap-2 sm:grid-cols-2">
          {architecture.modules.map((m) => (
            <div key={m.path} className="rounded-md border border-ink-700 bg-ink-850 px-3 py-2">
              <p className="truncate font-mono text-xs text-ink-200">{m.path}</p>
              <p className="text-[11px] text-ink-500">{m.description}</p>
            </div>
          ))}
        </div>
      </div>

      {architecture.relations.length > 0 && (
        <div>
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-ink-500">Relationships</p>
          <ul className="space-y-1 font-mono text-[11px] text-ink-400">
            {architecture.relations.map((r, i) => (
              <li key={`${r.source}-${r.target}-${i}`}>
                {r.source} <span className="text-amber-500">→</span> {r.target}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
