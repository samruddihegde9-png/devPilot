export interface ImportantFile {
  path: string;
  reason: string;
}

export interface KeyModule {
  path: string;
  file_count: number;
}

export interface DependencyInfo {
  python: string[];
  node: string[];
}

export interface RepoOverview {
  project_name: string;
  primary_language: string;
  languages: Record<string, number>;
  frameworks: string[];
  file_count: number;
  analyzed_file_count: number;
  total_lines: number;
  important_files: ImportantFile[];
  key_modules: KeyModule[];
  dependencies: DependencyInfo;
  skipped_binary_count: number;
  skipped_large_count: number;
}

export interface ArchitectureModule {
  path: string;
  file_count: number;
  description: string;
  x: number;
  y: number;
}

export interface ArchitectureRelation {
  source: string;
  target: string;
}

export interface Architecture {
  explanation: string;
  explanation_source: "ai" | "heuristic";
  modules: ArchitectureModule[];
  relations: ArchitectureRelation[];
}

export type IssueSeverity = "low" | "medium" | "high";

export interface Issue {
  file: string;
  line: number | null;
  function: string | null;
  description: string;
  severity: IssueSeverity;
  suggested_fix: string;
  rule_id: string;
}

export interface TestSuggestion {
  target_file: string;
  target_symbol: string;
  description: string;
  suggested_cases: string[];
  generated_test_code: string | null;
  generated_test_path: string | null;
}

export interface UsedSnippet {
  path: string;
  start_line: number;
  end_line: number;
  snippet: string;
}

export interface AskResponse {
  answer: string;
  mode: "ai" | "retrieval" | "none";
  used_files: UsedSnippet[];
}

export interface ScanSummary {
  project_id: string;
  scanned_at: string;
  file_count: number;
  analyzed_file_count: number;
  issue_count: number;
  issue_count_high: number;
  test_suggestion_count: number;
  llm_enabled: boolean;
}
