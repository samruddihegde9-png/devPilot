import { AnimatePresence, motion } from "framer-motion";
import { Code2, FolderGit2, Package, X } from "lucide-react";
import { useState } from "react";

import type { ProjectTemplate } from "../types/project";

interface Props {
  open: boolean;
  onClose: () => void;
  onCreate: (name: string, template: ProjectTemplate) => Promise<void>;
}

const TEMPLATES: { id: ProjectTemplate; label: string; hint: string; icon: typeof Code2 }[] = [
  { id: "python", label: "Python", hint: "pytest, plain scripts", icon: Code2 },
  { id: "fastapi", label: "FastAPI", hint: "API app + TestClient", icon: Package },
  { id: "react", label: "React", hint: "TSX component scaffold", icon: FolderGit2 },
  { id: "node", label: "Node.js", hint: "node --test", icon: Code2 },
];

export default function CreateProjectModal({ open, onClose, onCreate }: Props) {
  const [name, setName] = useState("");
  const [template, setTemplate] = useState<ProjectTemplate>("python");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Give the project a name.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await onCreate(name.trim(), template);
      setName("");
      setTemplate("python");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the project.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="w-full max-w-md rounded-lg border border-ink-700 bg-ink-900 p-6 shadow-2xl"
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.16 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-[15px] font-semibold text-ink-100">Create a project</h2>
              <button
                onClick={onClose}
                className="rounded p-1 text-ink-400 hover:bg-ink-800 hover:text-ink-100"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="project-name" className="mb-1.5 block text-xs font-medium text-ink-300">
                  Project name
                </label>
                <input
                  id="project-name"
                  autoFocus
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="jwt-auth-service"
                  className="w-full rounded-md border border-ink-600 bg-ink-850 px-3 py-2 text-sm text-ink-100 placeholder:text-ink-400 focus:border-amber-500 focus:outline-none"
                />
              </div>

              <div>
                <span className="mb-1.5 block text-xs font-medium text-ink-300">Template</span>
                <div className="grid grid-cols-2 gap-2">
                  {TEMPLATES.map((t) => {
                    const Icon = t.icon;
                    const active = template === t.id;
                    return (
                      <button
                        type="button"
                        key={t.id}
                        onClick={() => setTemplate(t.id)}
                        className={`flex flex-col items-start gap-1 rounded-md border px-3 py-2.5 text-left transition-colors ${
                          active
                            ? "border-amber-500/70 bg-amber-500/10"
                            : "border-ink-600 bg-ink-850 hover:border-ink-500"
                        }`}
                      >
                        <Icon size={15} className={active ? "text-amber-400" : "text-ink-400"} />
                        <span className={`text-sm font-medium ${active ? "text-ink-100" : "text-ink-200"}`}>
                          {t.label}
                        </span>
                        <span className="text-[11px] text-ink-400">{t.hint}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {error && <p className="text-xs text-signal-red">{error}</p>}

              <button
                type="submit"
                disabled={submitting}
                className="w-full rounded-md bg-amber-500 py-2 text-sm font-medium text-ink-950 transition-colors hover:bg-amber-400 disabled:opacity-50"
              >
                {submitting ? "Creating…" : "Create Project"}
              </button>
            </form>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
