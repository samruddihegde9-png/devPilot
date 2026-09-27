import { useState } from "react";
import { ChevronDown, ChevronRight, FlaskConical } from "lucide-react";

import type { TestSuggestion } from "../../types/repoIntel";

function TestCard({ s }: { s: TestSuggestion }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="rounded-md border border-ink-800 bg-ink-850 p-3">
      <button className="flex w-full items-start justify-between gap-3 text-left" onClick={() => setOpen((o) => !o)}>
        <div className="min-w-0">
          <p className="truncate font-mono text-xs text-ink-200">
            {s.target_file} · <span className="text-amber-300">{s.target_symbol}()</span>
          </p>
          <p className="mt-0.5 text-[12px] text-ink-500">{s.description}</p>
        </div>
        {s.generated_test_code ? (
          open ? <ChevronDown size={14} className="mt-0.5 shrink-0 text-ink-400" /> : <ChevronRight size={14} className="mt-0.5 shrink-0 text-ink-400" />
        ) : null}
      </button>

      <ul className="mt-2 space-y-1">
        {s.suggested_cases.map((c, i) => (
          <li key={i} className="flex items-start gap-1.5 text-[12px] text-ink-300">
            <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-ink-500" />
            {c}
          </li>
        ))}
      </ul>

      {s.generated_test_code && open && (
        <div className="mt-2 rounded-md border border-ink-700 bg-ink-950 p-2.5">
          <p className="mb-1 text-[10px] uppercase tracking-wide text-ink-500">
            Suggested test {s.generated_test_path && <>· {s.generated_test_path}</>}
          </p>
          <pre className="overflow-x-auto font-mono text-[11px] leading-relaxed text-ink-200">
            <code>{s.generated_test_code}</code>
          </pre>
        </div>
      )}
    </li>
  );
}

export default function TestsPanel({ tests }: { tests: TestSuggestion[] }) {
  if (tests.length === 0) {
    return (
      <p className="rounded-md border border-dashed border-ink-700 px-3 py-6 text-center text-sm text-ink-500">
        No untested functions were identified in the analyzed files.
      </p>
    );
  }

  const withCode = tests.filter((t) => t.generated_test_code).length;

  return (
    <div>
      <p className="mb-3 flex items-center gap-1.5 text-[11px] text-ink-500">
        <FlaskConical size={12} />
        {tests.length} suggestion(s) · {withCode} with a generated test skeleton (only for simple, side-effect-free
        functions — click a card with an arrow to expand)
      </p>
      <ul className="space-y-2">
        {tests.map((s, i) => (
          <TestCard key={`${s.target_file}-${s.target_symbol}-${i}`} s={s} />
        ))}
      </ul>
    </div>
  );
}
