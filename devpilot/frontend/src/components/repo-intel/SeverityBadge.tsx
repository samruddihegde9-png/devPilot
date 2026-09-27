import type { IssueSeverity } from "../../types/repoIntel";

const STYLES: Record<IssueSeverity, string> = {
  high: "bg-signal-red/10 text-signal-red border-signal-red/30",
  medium: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  low: "bg-ink-700/50 text-ink-300 border-ink-600",
};

export default function SeverityBadge({ severity }: { severity: IssueSeverity }) {
  return (
    <span className={`shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-medium uppercase ${STYLES[severity]}`}>
      {severity}
    </span>
  );
}
