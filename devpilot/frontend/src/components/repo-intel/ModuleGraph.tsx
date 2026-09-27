import type { ArchitectureModule, ArchitectureRelation } from "../../types/repoIntel";

const WIDTH = 640;
const HEIGHT = 320;
const PADDING = 70;

function labelFor(path: string): string {
  return path.split("/").pop() || path;
}

export default function ModuleGraph({
  modules,
  relations,
}: {
  modules: ArchitectureModule[];
  relations: ArchitectureRelation[];
}) {
  if (modules.length === 0) {
    return <p className="text-xs text-ink-500">Not enough structure yet to draw a module diagram.</p>;
  }

  const byPath = new Map(modules.map((m) => [m.path, m]));
  const point = (m: ArchitectureModule) => ({
    x: PADDING + m.x * (WIDTH - 2 * PADDING),
    y: PADDING + m.y * (HEIGHT - 2 * PADDING),
  });

  return (
    <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full rounded-md border border-ink-800 bg-ink-950">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="#5B6580" />
        </marker>
      </defs>

      {relations.map((rel, i) => {
        const source = byPath.get(rel.source);
        const target = byPath.get(rel.target);
        if (!source || !target) return null;
        const a = point(source);
        const b = point(target);
        return (
          <line
            key={`${rel.source}-${rel.target}-${i}`}
            x1={a.x}
            y1={a.y}
            x2={b.x}
            y2={b.y}
            stroke="#3B4459"
            strokeWidth={1.5}
            markerEnd="url(#arrow)"
          />
        );
      })}

      {modules.map((m) => {
        const { x, y } = point(m);
        const label = labelFor(m.path);
        return (
          <g key={m.path}>
            <rect
              x={x - 52}
              y={y - 16}
              width={104}
              height={32}
              rx={6}
              fill="#131822"
              stroke="#E8A33D"
              strokeOpacity={0.5}
            />
            <text x={x} y={y - 2} textAnchor="middle" fontSize={11} fill="#DDE1EA" fontFamily="JetBrains Mono, monospace">
              {label.length > 14 ? `${label.slice(0, 13)}…` : label}
            </text>
            <text x={x} y={y + 11} textAnchor="middle" fontSize={9} fill="#8891A6">
              {m.file_count} file{m.file_count === 1 ? "" : "s"}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
