import type { Issue } from "../../types/repoIntel";
import SeverityBadge from "./SeverityBadge";

export default function IssuesPanel({ issues }: { issues: Issue[] }) {
  if (issues.length === 0) {
    return (
      <p className="rounded-md border border-dashed border-ink-700 px-3 py-6 text-center text-sm text-ink-500">
        No issues found by the current rule set. This checks for a specific set of common problems (swallowed
        exceptions, hardcoded secrets, long functions, ...) — it isn't a full linter.
      </p>
    );
  }

  return (
    <ul className="space-y-2">
      {issues.map((issue, i) => (
        <li key={`${issue.file}-${issue.line}-${issue.rule_id}-${i}`} className="rounded-md border border-ink-800 bg-ink-850 p-3">
          <div className="mb-1.5 flex items-start justify-between gap-3">
            <span className="truncate font-mono text-xs text-ink-200">
              {issue.file}
              {issue.line != null && <span className="text-ink-500">:{issue.line}</span>}
              {issue.function && <span className="text-ink-500"> · {issue.function}()</span>}
            </span>
            <SeverityBadge severity={issue.severity} />
          </div>
          <p className="text-[13px] text-ink-200">{issue.description}</p>
          <p className="mt-1 text-[12px] text-ink-500">
            <span className="text-ink-400">Suggested fix:</span> {issue.suggested_fix}
          </p>
        </li>
      ))}
    </ul>
  );
}
