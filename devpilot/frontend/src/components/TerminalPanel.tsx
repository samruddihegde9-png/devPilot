import { TerminalSquare } from "lucide-react";

export default function TerminalPanel() {
  return (
    <div className="flex h-full flex-col border-t border-ink-800 bg-ink-950">
      <div className="flex items-center gap-2 border-b border-ink-800 px-3 py-1.5">
        <TerminalSquare size={13} className="text-ink-400" />
        <span className="text-[11px] font-medium uppercase tracking-wide text-ink-400">Terminal / Test Results</span>
      </div>
      <div className="flex flex-1 items-center px-3 font-mono text-[12px] text-ink-500">
        <span className="text-ink-600">$</span>
        <span className="ml-2">Command execution is not implemented yet — arrives in Phase 3.</span>
      </div>
    </div>
  );
}
