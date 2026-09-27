export type ProjectTemplate = "python" | "fastapi" | "react" | "node";

export interface Project {
  id: string;
  name: string;
  template: ProjectTemplate;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreatePayload {
  name: string;
  template: ProjectTemplate;
  description?: string;
}

export interface ImportGitPayload {
  git_url: string;
  name?: string;
  description?: string;
}

export interface UploadSummary {
  files_written: number;
  skipped: string[];
}
