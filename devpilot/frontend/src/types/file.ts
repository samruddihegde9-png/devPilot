export type FileNodeType = "file" | "directory";

export interface FileNode {
  name: string;
  path: string;
  type: FileNodeType;
  size?: number | null;
  children?: FileNode[] | null;
}

export interface FileContent {
  path: string;
  content: string;
}
