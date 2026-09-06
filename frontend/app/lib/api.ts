const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("il_token");
}

export function setToken(token: string) {
  window.localStorage.setItem("il_token", token);
}

export function clearToken() {
  window.localStorage.removeItem("il_token");
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

// ---- Types (mirror backend/app/schemas.py) --------------------------------
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type EvidenceStatus = "CONFIRMED" | "PARTIAL" | "VERIFY REQUIRED";

export interface SymbolRef {
  symbol: string;
  file: string;
  line: number;
  kind: string;
}

export interface GraphEdge {
  source: SymbolRef;
  target: SymbolRef;
  relation: string;
  confidence: number;
  evidence_note: string;
}

export interface GraphQueryResult {
  query_type: string;
  query: string;
  nodes: SymbolRef[];
  edges: GraphEdge[];
  confidence: number;
  heuristic: boolean;
  source: string;
  limitations: string[];
  evidence_status: EvidenceStatus;
  is_complete: boolean;
  verification_steps: string[];
}

export interface ChangedFile {
  path: string;
  additions: number;
  deletions: number;
  changed_symbols: string[];
}

export interface RiskFactor {
  key: string;
  label: string;
  value: number;
  weight: number;
  contribution: number;
  detail: string;
}

export interface RiskResult {
  score: number;
  level: RiskLevel;
  factors: RiskFactor[];
  rationale: string[];
  graph_confidence: number;
  evidence_status: EvidenceStatus;
  verification_required: boolean;
}

export interface EvidenceStep {
  symbol: SymbolRef;
  relation_to_next: string | null;
}

export interface TestRecommendation {
  test_name: string;
  file: string;
  line: number;
  priority_rank: number;
  relevance_score: number;
  reason: string;
  evidence_chain: EvidenceStep[];
  historical_failure_rate: number | null;
  is_hidden_dependency: boolean;
  affected_symbol: string;
  evidence_source: string;
  evidence_status: EvidenceStatus;
  verification_required: boolean;
}

export interface HistoricalFailure {
  commit_sha: string;
  symbol: string;
  test_name: string;
  outcome: string;
  failure_message: string | null;
  occurred_at: string;
  seeded_demo_data: boolean;
}

export interface Checkpoint {
  id: string;
  title: string;
  summary: string;
  author_type: string;
  author_name: string;
  session_id: string | null;
  prompt_excerpt: string | null;
  files_changed: string[];
  commit_sha: string | null;
  created_at: string;
}

export interface AIExplanation {
  summary: string;
  likely_failure_modes: string[];
  review_checklist: string[];
  test_justifications: Record<string, string>;
  generated_by: string;
  disclaimer: string;
}

export interface AnalysisResult {
  analysis_id: string;
  repository: string;
  ref_label: string;
  base_sha: string;
  head_sha: string;
  changed_files: ChangedFile[];
  graph_queries: GraphQueryResult[];
  risk: RiskResult;
  test_recommendations: TestRecommendation[];
  historical_failures: HistoricalFailure[];
  checkpoints: Checkpoint[];
  ai_explanation: AIExplanation;
  provenance: Record<string, string | boolean>;
  verification_plan: string[];
}

export interface RepoSummary {
  id: string;
  full_name: string;
  default_branch: string;
  is_demo: boolean;
  role: string;
}

// ---- API calls -------------------------------------------------------------
export const api = {
  authStatus: () => request<{ github_oauth_configured: boolean; local_demo_available: boolean }>("/api/auth/status"),
  demoLogin: () => request<{ token: string; user: any; demo_mode: boolean }>("/api/auth/demo-login", { method: "POST" }),
  me: () => request<any>("/api/auth/me"),
  listRepos: () => request<RepoSummary[]>("/api/repos"),
  repoOverview: (repoId: string) => request<any>(`/api/repos/${repoId}/overview`),
  analyze: (repoId: string, refLabel?: string) =>
    request<AnalysisResult>(`/api/repos/${repoId}/analyze${refLabel ? `?ref_label=${encodeURIComponent(refLabel)}` : ""}`, {
      method: "POST",
    }),
  listAnalyses: (repoId: string) => request<any[]>(`/api/repos/${repoId}/analyses`),
  checkpoints: (repoId: string) => request<Checkpoint[]>(`/api/repos/${repoId}/checkpoints`),
  settings: (repoId: string) => request<any>(`/api/repos/${repoId}/settings`),
  auditLog: (repoId: string) => request<any[]>(`/api/repos/${repoId}/audit-log`),
};
