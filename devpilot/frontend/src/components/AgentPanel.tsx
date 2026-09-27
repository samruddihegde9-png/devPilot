import { Bot, Sparkles } from "lucide-react";

const PLAN_STAGES = ["Understand project", "Create plan", "Implement", "Test", "Review"];

export default function AgentPanel() {
  return (
    <aside className="flex h-full flex-col border-l border-ink-800 bg-ink-900">
      <div className="flex items-center gap-2 border-b border-ink-800 px-3 py-2.5">
        <Bot size={14} className="text-ink-400" />
        <span className="text-xs font-medium uppercase tracking-wide text-ink-400">Agent</span>
        <span className="ml-auto flex items-center gap-1.5 rounded-full border border-ink-700 px-2 py-0.5 text-[10px] text-ink-400">
          <span className="h-1.5 w-1.5 rounded-full bg-ink-500" />
          Idle
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <div className="rounded-md border border-dashed border-ink-700 bg-ink-850 p-3">
          <div className="mb-1.5 flex items-center gap-1.5 text-ink-300">
            <Sparkles size={13} />
            <span className="text-xs font-medium">Agent runs arrive in Phase 2</span>
          </div>
          <p className="text-[11px] leading-relaxed text-ink-500">
            This panel is wired for the orchestrator, but the planner, coder, tester and debugger aren't
            connected yet. Not implemented yet — the task box below is disabled until Phase 2.
          </p>
        </div>

        <div className="mt-4">
          <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-ink-500">Plan (preview)</p>
          <ul className="space-y-1.5">
            {PLAN_STAGES.map((stage) => (
              <li key={stage} className="flex items-center gap-2 text-[12px] text-ink-500">
                <span className="h-1.5 w-1.5 rounded-full border border-ink-600" />
                {stage}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="border-t border-ink-800 p-3">
        <label className="mb-1.5 block text-[11px] font-medium text-ink-400">What should DevPilot build?</label>
        <textarea
          disabled
          rows={2}
          placeholder="Add JWT authentication to this FastAPI app"
          className="w-full resize-none rounded-md border border-ink-700 bg-ink-850 px-2.5 py-2 text-[12px] text-ink-400 placeholder:text-ink-600 disabled:cursor-not-allowed"
        />
        <button
          disabled
          className="mt-2 w-full rounded-md bg-ink-700 py-1.5 text-[12px] font-medium text-ink-400 disabled:cursor-not-allowed"
          title="Not implemented yet"
        >
          Run Agent
        </button>
      </div>
    </aside>
  );
}
