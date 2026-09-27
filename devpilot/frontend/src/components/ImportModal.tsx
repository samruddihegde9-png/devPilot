import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, FileUp, FolderUp, GitBranch, Loader2, X } from "lucide-react";
import { useRef, useState } from "react";

import { api, ApiError } from "../services/api";
import type { Project } from "../types/project";

type Tab = "git" | "upload";

interface Props {
  open: boolean;
  onClose: () => void;
  /** Called with the newly created project so Landing can navigate to it. */
  onImported: (project: Project) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function isGitUrl(value: string): boolean {
  return /^https?:\/\/.+/.test(value) || /^git@.+:.+/.test(value);
}

// ---------------------------------------------------------------------------
// Sub-panels
// ---------------------------------------------------------------------------

interface GitPanelProps {
  onImported: (project: Project) => void;
}

function GitPanel({ onImported }: GitPanelProps) {
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [status, setStatus] = useState<"idle" | "cloning" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleClone() {
    const trimmedUrl = url.trim();
    if (!trimmedUrl) {
      setError("Enter a Git URL.");
      return;
    }
    if (!isGitUrl(trimmedUrl)) {
      setError("Must be an https:// or git@host:path URL.");
      return;
    }
    setStatus("cloning");
    setError(null);
    try {
      const project = await api.importGit({
        git_url: trimmedUrl,
        name: name.trim() || undefined,
      });
      setStatus("done");
      // Small delay so the user sees the success state before navigating.
      setTimeout(() => onImported(project), 800);
    } catch (err) {
      setStatus("error");
      setError(
        err instanceof ApiError
          ? err.message
          : "Clone failed. Check the URL and make sure the repository is public."
      );
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1.5 block text-xs font-medium text-ink-300">Repository URL</label>
        <input
          autoFocus
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            setError(null);
          }}
          onKeyDown={(e) => e.key === "Enter" && void handleClone()}
          placeholder="https://github.com/owner/repo.git"
          disabled={status === "cloning"}
          className="w-full rounded-md border border-ink-600 bg-ink-850 px-3 py-2 text-sm text-ink-100 placeholder:text-ink-400 focus:border-amber-500 focus:outline-none disabled:opacity-50"
        />
      </div>

      <div>
        <label className="mb-1.5 block text-xs font-medium text-ink-300">
          Project name <span className="text-ink-500">(optional — defaults to repo name)</span>
        </label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="my-project"
          disabled={status === "cloning"}
          className="w-full rounded-md border border-ink-600 bg-ink-850 px-3 py-2 text-sm text-ink-100 placeholder:text-ink-400 focus:border-amber-500 focus:outline-none disabled:opacity-50"
        />
      </div>

      <p className="text-[11px] text-ink-500">
        Only <strong className="text-ink-400">public</strong> repositories are supported. The clone is
        shallow (--depth 1) and times out after 2 minutes.
      </p>

      {error && <p className="text-xs text-signal-red">{error}</p>}

      {status === "done" && (
        <div className="flex items-center gap-2 text-xs text-green-400">
          <CheckCircle2 size={13} />
          Imported — opening workspace…
        </div>
      )}

      <button
        onClick={() => void handleClone()}
        disabled={status === "cloning" || status === "done"}
        className="flex w-full items-center justify-center gap-2 rounded-md bg-amber-500 py-2 text-sm font-medium text-ink-950 transition-colors hover:bg-amber-400 disabled:opacity-50"
      >
        {status === "cloning" ? (
          <>
            <Loader2 size={14} className="animate-spin" />
            Cloning repository…
          </>
        ) : (
          <>
            <GitBranch size={14} />
            Clone &amp; Import
          </>
        )}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------

interface UploadPanelProps {
  onImported: (project: Project) => void;
}

function UploadPanel({ onImported }: UploadPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const [projectName, setProjectName] = useState("");
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<"idle" | "creating" | "uploading" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ written: number; skipped: string[] } | null>(null);
  const [dragOver, setDragOver] = useState(false);

  function addFiles(incoming: FileList | null) {
    if (!incoming) return;
    const arr = Array.from(incoming);
    setSelectedFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name + f.size));
      const fresh = arr.filter((f) => !existing.has(f.name + f.size));
      return [...prev, ...fresh];
    });
    setError(null);
  }

  function removeFile(index: number) {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleUpload() {
    if (selectedFiles.length === 0) {
      setError("Select at least one file or folder.");
      return;
    }
    const name = projectName.trim() || "Uploaded Project";
    setStatus("creating");
    setError(null);

    let project: Project;
    try {
      project = await api.createProject({ name, template: "python" });
    } catch (err) {
      setStatus("error");
      setError(
        err instanceof ApiError ? err.message : "Could not create project. Is the backend running?"
      );
      return;
    }

    setStatus("uploading");
    try {
      const summary = await api.uploadFiles(project.id, selectedFiles);
      setResult({ written: summary.files_written, skipped: summary.skipped });
      setStatus("done");
      setTimeout(() => onImported(project), 1200);
    } catch (err) {
      setStatus("error");
      setError(
        err instanceof ApiError ? err.message : "Upload failed. The project was created but files weren't written."
      );
    }
  }

  const busy = status === "creating" || status === "uploading";

  return (
    <div className="space-y-4">
      <div>
        <label className="mb-1.5 block text-xs font-medium text-ink-300">
          Project name <span className="text-ink-500">(optional)</span>
        </label>
        <input
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="Uploaded Project"
          disabled={busy}
          className="w-full rounded-md border border-ink-600 bg-ink-850 px-3 py-2 text-sm text-ink-100 placeholder:text-ink-400 focus:border-amber-500 focus:outline-none disabled:opacity-50"
        />
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
        className={`flex flex-col items-center justify-center gap-2 rounded-md border-2 border-dashed px-4 py-8 text-center transition-colors ${
          dragOver ? "border-amber-500 bg-amber-500/5" : "border-ink-700 bg-ink-900/50"
        }`}
      >
        <FileUp size={22} className="text-ink-500" />
        <p className="text-sm text-ink-300">Drag &amp; drop files or folders here</p>
        <p className="text-[11px] text-ink-500">or use the buttons below</p>

        <div className="mt-2 flex gap-2">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={busy}
            className="flex items-center gap-1.5 rounded-md border border-ink-600 px-3 py-1.5 text-xs text-ink-200 hover:border-ink-400 hover:text-ink-100 disabled:opacity-50"
          >
            <FileUp size={12} />
            Add files
          </button>
          <button
            type="button"
            onClick={() => folderInputRef.current?.click()}
            disabled={busy}
            className="flex items-center gap-1.5 rounded-md border border-ink-600 px-3 py-1.5 text-xs text-ink-200 hover:border-ink-400 hover:text-ink-100 disabled:opacity-50"
          >
            <FolderUp size={12} />
            Add folder
          </button>
        </div>

        {/* Hidden inputs */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
        <input
          ref={folderInputRef}
          type="file"
          // @ts-expect-error – non-standard but works in all modern browsers
          webkitdirectory=""
          className="hidden"
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {/* File list */}
      {selectedFiles.length > 0 && (
        <div className="max-h-36 overflow-y-auto rounded-md border border-ink-700 bg-ink-900">
          {selectedFiles.map((f, i) => {
            const displayName =
              (f as File & { webkitRelativePath?: string }).webkitRelativePath || f.name;
            return (
              <div key={i} className="flex items-center justify-between gap-2 px-3 py-1.5 text-xs text-ink-300 odd:bg-ink-900 even:bg-ink-850">
                <span className="truncate">{displayName}</span>
                <button
                  onClick={() => removeFile(i)}
                  className="shrink-0 text-ink-500 hover:text-signal-red"
                  title="Remove"
                >
                  <X size={11} />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {selectedFiles.length > 0 && (
        <p className="text-[11px] text-ink-500">
          {selectedFiles.length} file{selectedFiles.length !== 1 ? "s" : ""} selected
        </p>
      )}

      {error && <p className="text-xs text-signal-red">{error}</p>}

      {status === "done" && result && (
        <div className="rounded-md border border-green-600/30 bg-green-600/5 px-3 py-2 text-xs text-green-400">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 size={12} />
            {result.written} file{result.written !== 1 ? "s" : ""} uploaded — opening workspace…
          </div>
          {result.skipped.length > 0 && (
            <p className="mt-1 text-ink-400">
              Skipped: {result.skipped.slice(0, 4).join(", ")}
              {result.skipped.length > 4 ? ` + ${result.skipped.length - 4} more` : ""}
            </p>
          )}
        </div>
      )}

      <button
        onClick={() => void handleUpload()}
        disabled={busy || status === "done" || selectedFiles.length === 0}
        className="flex w-full items-center justify-center gap-2 rounded-md bg-amber-500 py-2 text-sm font-medium text-ink-950 transition-colors hover:bg-amber-400 disabled:opacity-50"
      >
        {busy ? (
          <>
            <Loader2 size={14} className="animate-spin" />
            {status === "creating" ? "Creating project…" : "Uploading files…"}
          </>
        ) : (
          <>
            <FileUp size={14} />
            Upload &amp; Import
          </>
        )}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main modal
// ---------------------------------------------------------------------------

export default function ImportModal({ open, onClose, onImported }: Props) {
  const [tab, setTab] = useState<Tab>("git");

  function handleImported(project: Project) {
    onImported(project);
    onClose();
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
            {/* Header */}
            <div className="mb-5 flex items-center justify-between">
              <h2 className="text-[15px] font-semibold text-ink-100">Import project</h2>
              <button
                onClick={onClose}
                className="rounded p-1 text-ink-400 hover:bg-ink-800 hover:text-ink-100"
                aria-label="Close"
              >
                <X size={16} />
              </button>
            </div>

            {/* Tabs */}
            <div className="mb-5 flex gap-1 rounded-md border border-ink-700 bg-ink-850 p-1">
              {(["git", "upload"] as Tab[]).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`flex flex-1 items-center justify-center gap-1.5 rounded py-1.5 text-xs font-medium transition-colors ${
                    tab === t
                      ? "bg-ink-700 text-ink-100"
                      : "text-ink-400 hover:text-ink-200"
                  }`}
                >
                  {t === "git" ? <GitBranch size={13} /> : <FolderUp size={13} />}
                  {t === "git" ? "From GitHub / Git URL" : "Upload files / folder"}
                </button>
              ))}
            </div>

            {tab === "git" ? (
              <GitPanel onImported={handleImported} />
            ) : (
              <UploadPanel onImported={handleImported} />
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
