import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import AgentPanel from "../components/AgentPanel";
import CodeEditor from "../components/CodeEditor";
import FileTree from "../components/FileTree";
import NamePromptModal from "../components/NamePromptModal";
import TerminalPanel from "../components/TerminalPanel";
import Topbar from "../components/Topbar";
import { api } from "../services/api";
import type { FileNode } from "../types/file";
import type { Project } from "../types/project";

export default function Workspace() {
  const { projectId } = useParams<{ projectId: string }>();

  const [project, setProject] = useState<Project | null>(null);
  const [tree, setTree] = useState<FileNode[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [savedContent, setSavedContent] = useState("");
  const [fileLoading, setFileLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [createRequest, setCreateRequest] = useState<{ parentPath: string; type: "file" | "directory" } | null>(
    null
  );

  const loadTree = useCallback(async () => {
    if (!projectId) return;
    try {
      const data = await api.getFileTree(projectId);
      setTree(data);
    } catch {
      setLoadError("Could not load the project file tree.");
    }
  }, [projectId]);

  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    (async () => {
      try {
        const p = await api.getProject(projectId);
        if (!cancelled) setProject(p);
      } catch {
        if (!cancelled) setLoadError("Project not found.");
      }
      await loadTree();
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId, loadTree]);

  async function handleSelect(node: FileNode) {
    if (!projectId || node.type !== "file") return;
    setFileLoading(true);
    setSelectedPath(node.path);
    try {
      const file = await api.readFile(projectId, node.path);
      setContent(file.content);
      setSavedContent(file.content);
    } catch {
      setContent("// Could not load this file.");
      setSavedContent("// Could not load this file.");
    } finally {
      setFileLoading(false);
    }
  }

  async function handleSave() {
    if (!projectId || !selectedPath) return;
    setSaving(true);
    try {
      await api.writeFile(projectId, selectedPath, content);
      setSavedContent(content);
    } finally {
      setSaving(false);
    }
  }

  async function handleCreateConfirm(rawName: string) {
    if (!projectId || !createRequest) return;
    const parent = createRequest.parentPath;
    const path = parent ? `${parent}/${rawName}` : rawName;
    await api.createFile(projectId, path, createRequest.type, createRequest.type === "file" ? "" : undefined);
    setCreateRequest(null);
    await loadTree();
    if (createRequest.type === "file") {
      await handleSelect({ name: rawName, path, type: "file" });
    }
  }

  async function handleDelete(node: FileNode) {
    if (!projectId) return;
    if (!confirm(`Delete ${node.path}? This can't be undone.`)) return;
    await api.deleteFile(projectId, node.path);
    if (selectedPath === node.path || selectedPath?.startsWith(`${node.path}/`)) {
      setSelectedPath(null);
      setContent("");
      setSavedContent("");
    }
    await loadTree();
  }

  const dirty = content !== savedContent;

  if (loadError) {
    return (
      <div className="flex h-screen flex-col">
        <Topbar project={null} />
        <div className="flex flex-1 items-center justify-center text-sm text-ink-400">{loadError}</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <Topbar project={project} />
      <div className="grid min-h-0 flex-1 grid-cols-[220px_1fr_260px] grid-rows-[1fr_180px]">
        <div className="row-span-1 overflow-y-auto border-b border-r border-ink-800 bg-ink-900">
          <div className="border-b border-ink-800 px-3 py-2 text-[11px] font-medium uppercase tracking-wide text-ink-500">
            Project
          </div>
          <FileTree
            tree={tree}
            selectedPath={selectedPath}
            onSelect={handleSelect}
            onCreate={(parentPath, type) => setCreateRequest({ parentPath, type })}
            onDelete={handleDelete}
          />
        </div>

        <div className="row-span-1 min-h-0 min-w-0 border-b border-ink-800 bg-ink-950">
          {fileLoading ? (
            <div className="flex h-full items-center justify-center text-sm text-ink-500">Loading file…</div>
          ) : (
            <CodeEditor
              path={selectedPath}
              content={content}
              dirty={dirty}
              saving={saving}
              onChange={setContent}
              onSave={handleSave}
            />
          )}
        </div>

        <div className="row-span-1 min-h-0 border-b border-ink-800">
          <AgentPanel />
        </div>

        <div className="col-span-3 min-h-0">
          <TerminalPanel />
        </div>
      </div>

      <NamePromptModal
        open={createRequest !== null}
        title={createRequest?.type === "directory" ? "New folder name" : "New file name"}
        placeholder={createRequest?.type === "directory" ? "utils" : "app/utils.py"}
        confirmLabel="Create"
        onCancel={() => setCreateRequest(null)}
        onConfirm={handleCreateConfirm}
      />
    </div>
  );
}
