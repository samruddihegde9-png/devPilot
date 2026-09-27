import Editor from "@monaco-editor/react";
import { Save } from "lucide-react";
import { useEffect, useState } from "react";

interface Props {
  path: string | null;
  content: string;
  dirty: boolean;
  saving: boolean;
  onChange: (value: string) => void;
  onSave: () => void;
}

function languageForPath(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase();
  switch (ext) {
    case "py":
      return "python";
    case "ts":
    case "tsx":
      return "typescript";
    case "js":
    case "jsx":
      return "javascript";
    case "json":
      return "json";
    case "md":
      return "markdown";
    case "css":
      return "css";
    case "html":
      return "html";
    case "yml":
    case "yaml":
      return "yaml";
    default:
      return "plaintext";
  }
}

export default function CodeEditor({ path, content, dirty, saving, onChange, onSave }: Props) {
  const [localPath, setLocalPath] = useState(path);

  useEffect(() => {
    setLocalPath(path);
  }, [path]);

  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "s") {
        e.preventDefault();
        if (dirty) onSave();
      }
    }
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [dirty, onSave]);

  if (!path) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-1 text-ink-500">
        <p className="text-sm">No file open</p>
        <p className="text-xs text-ink-600">Select a file from the project tree to view or edit it.</p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-ink-800 bg-ink-900 px-3 py-1.5">
        <div className="flex items-center gap-2 overflow-hidden">
          <span className="truncate font-mono text-xs text-ink-300">{localPath}</span>
          {dirty && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-amber-400" title="Unsaved changes" />}
        </div>
        <button
          onClick={onSave}
          disabled={!dirty || saving}
          className="flex items-center gap-1 rounded px-2 py-1 text-[11px] font-medium text-ink-300 hover:bg-ink-800 hover:text-ink-100 disabled:opacity-40"
        >
          <Save size={12} />
          {saving ? "Saving…" : "Save"}
        </button>
      </div>
      <div className="min-h-0 flex-1">
        <Editor
          key={path}
          path={path}
          language={languageForPath(path)}
          value={content}
          theme="vs-dark"
          onChange={(value) => onChange(value ?? "")}
          options={{
            fontSize: 13,
            fontFamily: "JetBrains Mono, ui-monospace, monospace",
            minimap: { enabled: false },
            automaticLayout: true,
            scrollBeyondLastLine: false,
            padding: { top: 12 },
            tabSize: 2,
          }}
        />
      </div>
    </div>
  );
}
