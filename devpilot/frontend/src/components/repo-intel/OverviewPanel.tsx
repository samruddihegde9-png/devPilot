import type { ReactNode } from "react";

import type { RepoOverview } from "../../types/repoIntel";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-ink-500">{title}</p>
      {children}
    </div>
  );
}

export default function OverviewPanel({ overview }: { overview: RepoOverview }) {
  const langEntries = Object.entries(overview.languages).sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-300">
          {overview.primary_language}
        </span>
        {overview.frameworks.map((fw) => (
          <span key={fw} className="rounded-md border border-ink-600 bg-ink-850 px-2.5 py-1 text-xs text-ink-200">
            {fw}
          </span>
        ))}
        <span className="ml-auto text-xs text-ink-500">
          {overview.analyzed_file_count} of {overview.file_count} files analyzed · {overview.total_lines} lines
        </span>
      </div>

      {langEntries.length > 0 && (
        <Section title="Languages">
          <div className="flex flex-wrap gap-2">
            {langEntries.map(([lang, count]) => (
              <span key={lang} className="rounded border border-ink-700 bg-ink-850 px-2 py-1 text-[11px] text-ink-300">
                {lang} <span className="text-ink-500">· {count}</span>
              </span>
            ))}
          </div>
        </Section>
      )}

      <Section title="Important files">
        {overview.important_files.length === 0 ? (
          <p className="text-xs text-ink-500">No recognizable entry points or manifests found yet.</p>
        ) : (
          <ul className="divide-y divide-ink-800 rounded-md border border-ink-800">
            {overview.important_files.map((f) => (
              <li key={f.path} className="flex items-center justify-between gap-3 px-3 py-2">
                <span className="truncate font-mono text-xs text-ink-200">{f.path}</span>
                <span className="shrink-0 text-[11px] text-ink-500">{f.reason}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Key modules">
        {overview.key_modules.length === 0 ? (
          <p className="text-xs text-ink-500">Not enough structure yet to identify distinct modules.</p>
        ) : (
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {overview.key_modules.map((m) => (
              <div key={m.path} className="rounded-md border border-ink-700 bg-ink-850 px-3 py-2">
                <p className="truncate font-mono text-[11px] text-ink-200">{m.path}</p>
                <p className="text-[10px] text-ink-500">{m.file_count} file(s)</p>
              </div>
            ))}
          </div>
        )}
      </Section>

      {(overview.dependencies.python.length > 0 || overview.dependencies.node.length > 0) && (
        <Section title="Dependencies">
          <div className="grid gap-3 sm:grid-cols-2">
            {overview.dependencies.python.length > 0 && (
              <div className="rounded-md border border-ink-700 bg-ink-850 p-2.5">
                <p className="mb-1.5 text-[11px] font-medium text-ink-400">Python</p>
                <div className="flex flex-wrap gap-1">
                  {overview.dependencies.python.map((d) => (
                    <span key={d} className="rounded bg-ink-800 px-1.5 py-0.5 font-mono text-[10px] text-ink-300">
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {overview.dependencies.node.length > 0 && (
              <div className="rounded-md border border-ink-700 bg-ink-850 p-2.5">
                <p className="mb-1.5 text-[11px] font-medium text-ink-400">Node</p>
                <div className="flex flex-wrap gap-1">
                  {overview.dependencies.node.map((d) => (
                    <span key={d} className="rounded bg-ink-800 px-1.5 py-0.5 font-mono text-[10px] text-ink-300">
                      {d}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Section>
      )}

      {(overview.skipped_binary_count > 0 || overview.skipped_large_count > 0) && (
        <p className="text-[11px] text-ink-600">
          Skipped {overview.skipped_binary_count} binary file(s) and {overview.skipped_large_count} file(s) past the
          size budget for this scan.
        </p>
      )}
    </div>
  );
}
