import type { FileContent, FileNode } from "../types/file";
import type { ImportGitPayload, Project, ProjectCreatePayload, UploadSummary } from "../types/project";
import type {
  Architecture,
  AskResponse,
  Issue,
  RepoOverview,
  ScanSummary,
  TestSuggestion,
} from "../types/repoIntel";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // response had no JSON body — fall back to statusText
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  // --- Projects ---
  listProjects: () => request<Project[]>("/api/projects"),
  getProject: (id: string) => request<Project>(`/api/projects/${id}`),
  createProject: (payload: ProjectCreatePayload) =>
    request<Project>("/api/projects", { method: "POST", body: JSON.stringify(payload) }),
  deleteProject: (id: string) => request<void>(`/api/projects/${id}`, { method: "DELETE" }),

  // --- Import ---
  importGit: (payload: ImportGitPayload) =>
    request<Project>("/api/projects/import-git", { method: "POST", body: JSON.stringify(payload) }),
  uploadFiles: (projectId: string, files: File[]) => {
    const form = new FormData();
    for (const f of files) {
      // webkitRelativePath carries the folder-relative path for folder uploads;
      // fall back to the plain filename for single-file picks.
      const name = (f as File & { webkitRelativePath?: string }).webkitRelativePath || f.name;
      form.append("files", f, name);
    }
    return request<UploadSummary>(`/api/projects/${projectId}/upload-files`, {
      method: "POST",
      body: form,
      // Do NOT set Content-Type — the browser must set it with the boundary.
      headers: {},
    });
  },

  // --- Files ---
  getFileTree: (projectId: string) => request<FileNode[]>(`/api/projects/${projectId}/files`),
  readFile: (projectId: string, path: string) =>
    request<FileContent>(`/api/projects/${projectId}/files/${encodePath(path)}`),
  writeFile: (projectId: string, path: string, content: string) =>
    request<FileContent>(`/api/projects/${projectId}/files/${encodePath(path)}`, {
      method: "PUT",
      body: JSON.stringify({ content }),
    }),
  createFile: (projectId: string, path: string, type: "file" | "directory", content = "") =>
    request<FileNode>(`/api/projects/${projectId}/files`, {
      method: "POST",
      body: JSON.stringify({ path, type, content }),
    }),
  deleteFile: (projectId: string, path: string) =>
    request<void>(`/api/projects/${projectId}/files/${encodePath(path)}`, { method: "DELETE" }),
  renameFile: (projectId: string, path: string, newPath: string) =>
    request<FileNode>(`/api/projects/${projectId}/files/${encodePath(path)}`, {
      method: "PATCH",
      body: JSON.stringify({ new_path: newPath }),
    }),

  // --- Repository Intelligence ---
  scanRepo: (projectId: string) =>
    request<ScanSummary>(`/api/projects/${projectId}/repo-intel/scan`, { method: "POST" }),
  getRepoSummary: (projectId: string) => request<ScanSummary>(`/api/projects/${projectId}/repo-intel/summary`),
  getRepoOverview: (projectId: string) =>
    request<RepoOverview>(`/api/projects/${projectId}/repo-intel/overview`),
  getRepoArchitecture: (projectId: string) =>
    request<Architecture>(`/api/projects/${projectId}/repo-intel/architecture`),
  getRepoIssues: (projectId: string) => request<Issue[]>(`/api/projects/${projectId}/repo-intel/issues`),
  getRepoTests: (projectId: string) => request<TestSuggestion[]>(`/api/projects/${projectId}/repo-intel/tests`),
  askRepo: (projectId: string, question: string) =>
    request<AskResponse>(`/api/projects/${projectId}/repo-intel/ask`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};

function encodePath(path: string): string {
  // Encode each segment individually so "/" stays a path separator, matching
  // the backend's {path:path} route converter.
  return path.split("/").map(encodeURIComponent).join("/");
}
