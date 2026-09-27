import { ChevronDown, ChevronRight, File, FilePlus, Folder, FolderPlus, FolderOpen, Trash2 } from "lucide-react";
import { useState } from "react";

import type { FileNode } from "../types/file";

interface Props {
  tree: FileNode[];
  selectedPath: string | null;
  onSelect: (node: FileNode) => void;
  onCreate: (parentPath: string, type: "file" | "directory") => void;
  onDelete: (node: FileNode) => void;
}

export default function FileTree({ tree, selectedPath, onSelect, onCreate, onDelete }: Props) {
  return (
    <div className="select-none py-1 text-[13px]">
      {tree.length === 0 ? (
        <p className="px-3 py-2 text-xs text-ink-400">No files yet.</p>
      ) : (
        tree.map((node) => (
          <TreeNode
            key={node.path}
            node={node}
            depth={0}
            selectedPath={selectedPath}
            onSelect={onSelect}
            onCreate={onCreate}
            onDelete={onDelete}
          />
        ))
      )}
      <div className="mt-1 flex gap-1 border-t border-ink-800 px-2 pt-2">
        <button
          onClick={() => onCreate("", "file")}
          className="flex items-center gap-1 rounded px-1.5 py-1 text-[11px] text-ink-400 hover:bg-ink-800 hover:text-ink-100"
          title="New file at project root"
        >
          <FilePlus size={12} /> File
        </button>
        <button
          onClick={() => onCreate("", "directory")}
          className="flex items-center gap-1 rounded px-1.5 py-1 text-[11px] text-ink-400 hover:bg-ink-800 hover:text-ink-100"
          title="New folder at project root"
        >
          <FolderPlus size={12} /> Folder
        </button>
      </div>
    </div>
  );
}

function TreeNode({
  node,
  depth,
  selectedPath,
  onSelect,
  onCreate,
  onDelete,
}: {
  node: FileNode;
  depth: number;
  selectedPath: string | null;
  onSelect: (node: FileNode) => void;
  onCreate: (parentPath: string, type: "file" | "directory") => void;
  onDelete: (node: FileNode) => void;
}) {
  const [open, setOpen] = useState(depth < 1);
  const isDir = node.type === "directory";
  const active = selectedPath === node.path;

  return (
    <div>
      <div
        className={`group flex items-center gap-1 rounded px-1.5 py-1 hover:bg-ink-800 ${
          active ? "bg-amber-500/10 text-amber-300" : "text-ink-200"
        }`}
        style={{ paddingLeft: 8 + depth * 14 }}
      >
        <button
          className="flex flex-1 items-center gap-1.5 overflow-hidden text-left"
          onClick={() => (isDir ? setOpen((o) => !o) : onSelect(node))}
        >
          {isDir ? (
            open ? (
              <ChevronDown size={13} className="shrink-0 text-ink-400" />
            ) : (
              <ChevronRight size={13} className="shrink-0 text-ink-400" />
            )
          ) : (
            <span className="w-[13px] shrink-0" />
          )}
          {isDir ? (
            open ? (
              <FolderOpen size={13} className="shrink-0 text-amber-400/80" />
            ) : (
              <Folder size={13} className="shrink-0 text-ink-400" />
            )
          ) : (
            <File size={13} className="shrink-0 text-ink-400" />
          )}
          <span className="truncate">{node.name}</span>
        </button>
        <span className="hidden items-center gap-0.5 group-hover:flex">
          {isDir && (
            <button
              onClick={() => onCreate(node.path, "file")}
              className="rounded p-0.5 text-ink-400 hover:text-ink-100"
              title="New file here"
            >
              <FilePlus size={12} />
            </button>
          )}
          <button
            onClick={() => onDelete(node)}
            className="rounded p-0.5 text-ink-400 hover:text-signal-red"
            title="Delete"
          >
            <Trash2 size={12} />
          </button>
        </span>
      </div>
      {isDir && open && node.children && node.children.length > 0 && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
              onCreate={onCreate}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
