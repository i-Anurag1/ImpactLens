"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  api, clearToken, ApiError,
  RepoSummary, AnalysisResult, EvidenceStatus,
} from "../lib/api";
import RiskBadge from "../components/RiskBadge";
import DependencyGraph from "../components/DependencyGraph";

type Tab =
  | "overview" | "analysis" | "graph" | "risk" | "tests"
  | "history" | "explanation" | "checkpoints" | "settings";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Repository Overview" },
  { id: "analysis", label: "Change Analysis" },
  { id: "graph", label: "Dependency Graph" },
  { id: "risk", label: "Risk Report" },
  { id: "tests", label: "Test Recommendations" },
  { id: "history", label: "Historical Evidence" },
  { id: "explanation", label: "AI Explanation" },
  { id: "checkpoints", label: "Checkpoints" },
  { id: "settings", label: "Settings" },
];

export default function Dashboard() {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);
  const [tab, setTab] = useState<Tab>("overview");
  const [repos, setRepos] = useState<RepoSummary[]>([]);
  const [repo, setRepo] = useState<RepoSummary | null>(null);
  const [overview, setOverview] = useState<any>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);
  const canAnalyze = repo?.role === "developer" || repo?.role === "admin";

  useEffect(() => {
    (async () => {
      try {
        const me = await api.me();
        setUser(me);
        const r = await api.listRepos();
        setRepos(r);
        if (r.length) {
          setRepo(r[0]);
          const ov = await api.repoOverview(r[0].id);
          setOverview(ov);
        }
      } catch (e) {
        router.push("/");
        return;
      } finally {
        setAuthChecked(true);
      }
    })();
  }, [router]);

  async function runAnalysis() {
    if (!repo) return;
    setAnalyzing(true);
    setError(null);
    try {
      const result = await api.analyze(repo.id, overview?.demo_commit ? "PR: Fix currency rounding in processPayment" : undefined);
      setAnalysis(result);
      setTab("risk");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Analysis failed unexpectedly.");
    } finally {
      setAnalyzing(false);
    }
  }

  function signOut() {
    clearToken();
    router.push("/");
  }

  if (!authChecked) {
    return <CenterMessage text="Loading your workspace…" />;
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 border-r border-ink-700 flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-ink-700">
          <div className="font-display font-semibold">ImpactLens AI</div>
          {repo && <div className="text-mist-500 text-xs mt-1 font-mono">{repo.full_name}</div>}
        </div>
        <nav className="flex-1 py-3">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`w-full text-left px-5 py-2.5 text-sm transition-colors ${
                tab === t.id ? "bg-ink-800 text-mist-100 border-r-2 border-signal-indigo" : "text-mist-300 hover:bg-ink-800/60"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="px-5 py-4 border-t border-ink-700 text-xs text-mist-500 flex items-center justify-between">
          <span>{user?.display_name} {repo && <span className="ml-1 text-signal-indigo uppercase">· {repo.role}</span>}</span>
          <button onClick={signOut} className="hover:text-mist-100">Sign out</button>
        </div>
      </aside>

      <main className="flex-1 p-8 max-w-6xl">
        {!repo && (
          <EmptyState
            title="No repository connected yet"
            body="Connect a GitHub repository to start analyzing changes. This build ships with a demo repository already connected."
          />
        )}

        {repo && tab === "overview" && <OverviewTab overview={overview} onAnalyze={runAnalysis} analyzing={analyzing} error={error} canAnalyze={canAnalyze} />}
        {repo && tab === "analysis" && <AnalysisTab overview={overview} analysis={analysis} onAnalyze={runAnalysis} analyzing={analyzing} error={error} canAnalyze={canAnalyze} />}
        {repo && tab === "graph" && (
          analysis ? (
            <div className="rise-in">
              <SectionHeader title="Dependency Graph" sub="Click any node to see its file:line evidence and relationships." />
              <EvidenceBanner status={analysis.risk.evidence_status} steps={analysis.verification_plan} />
              <DependencyGraph
                impact={analysis.graph_queries.find((g) => g.query_type === "impact")!}
                changedSymbols={analysis.changed_files.flatMap((f) => f.changed_symbols)}
              />
            </div>
          ) : <NeedsAnalysis onAnalyze={runAnalysis} analyzing={analyzing} />
        )}
        {repo && tab === "risk" && (analysis ? <RiskTab analysis={analysis} /> : <NeedsAnalysis onAnalyze={runAnalysis} analyzing={analyzing} />)}
        {repo && tab === "tests" && (analysis ? <TestsTab analysis={analysis} /> : <NeedsAnalysis onAnalyze={runAnalysis} analyzing={analyzing} />)}
        {repo && tab === "history" && (analysis ? <HistoryTab analysis={analysis} /> : <NeedsAnalysis onAnalyze={runAnalysis} analyzing={analyzing} />)}
        {repo && tab === "explanation" && (analysis ? <ExplanationTab analysis={analysis} /> : <NeedsAnalysis onAnalyze={runAnalysis} analyzing={analyzing} />)}
        {repo && tab === "checkpoints" && <CheckpointsTab repoId={repo.id} />}
        {repo && tab === "settings" && <SettingsTab repoId={repo.id} />}
      </main>
    </div>
  );
}

// ---- shared bits -----------------------------------------------------------
function SectionHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="mb-5">
      <h2 className="font-display text-xl font-semibold text-mist-100">{title}</h2>
      {sub && <p className="text-mist-500 text-sm mt-1">{sub}</p>}
    </div>
  );
}

function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="border border-dashed border-ink-600 rounded-sm p-10 text-center max-w-lg mx-auto mt-16">
      <h3 className="font-display text-lg text-mist-100 mb-2">{title}</h3>
      <p className="text-mist-500 text-sm">{body}</p>
    </div>
  );
}

function NeedsAnalysis({ onAnalyze, analyzing }: { onAnalyze: () => void; analyzing: boolean }) {
  return (
    <EmptyState
      title="Run an analysis to see this"
      body="This view fills in once you analyze a change. Go to Change Analysis, or use the button below."
    />
  );
}

function CenterMessage({ text }: { text: string }) {
  return <div className="min-h-screen flex items-center justify-center text-mist-500">{text}</div>;
}

function EvidenceBanner({ status, steps = [] }: { status: EvidenceStatus; steps?: string[] }) {
  if (status === "CONFIRMED") {
    return <div className="mb-5 border border-signal-low/40 bg-risk-LOW rounded-sm p-3 text-sm text-mist-300"><span className="text-signal-low font-medium">CONFIRMED</span> structural evidence.</div>;
  }
  return (
    <div className="mb-5 border border-signal-high/50 bg-risk-HIGH rounded-sm p-4">
      <p className="text-signal-high text-sm font-medium">{status} — graph evidence is not a runtime guarantee</p>
      <p className="text-mist-300 text-xs mt-1">Recommendations use the available evidence as a lead. Inspect source, callers/callees, tests, and runtime behavior before merging.</p>
      {steps.length > 0 && <ul className="mt-2 list-disc list-inside text-xs text-mist-300 space-y-1">{steps.map((step) => <li key={step}>{step}</li>)}</ul>}
    </div>
  );
}

// ---- Overview ---------------------------------------------------------------
function OverviewTab({
  overview, onAnalyze, analyzing, error, canAnalyze,
}: {
  overview: any;
  onAnalyze: () => void;
  analyzing: boolean;
  error: string | null;
  canAnalyze: boolean;
}) {
  if (!overview) return <CenterMessage text="Loading repository…" />;
  return (
    <div className="rise-in">
      <SectionHeader title="Repository Overview" sub={overview.repository.full_name} />
      <div className="grid grid-cols-2 gap-4 mb-6">
        <Stat label="Default branch" value={overview.repository.default_branch} />
        <Stat label="Indexed symbols" value={overview.graph_snapshot.symbol_count} />
        <Stat label="Traced edges" value={overview.graph_snapshot.edge_count} />
        <Stat label="Last indexed" value={new Date(overview.graph_snapshot.last_indexed_at).toLocaleString()} />
      </div>
      {overview.demo_commit && (
        <div className="bg-ink-800 border border-ink-600 rounded-sm p-4">
          <p className="text-mist-500 text-xs mb-1">Pending change ready to analyze</p>
          <p className="font-mono text-sm text-mist-100">{overview.demo_commit.pr_title}</p>
          <p className="text-mist-500 text-xs mt-1">
            {overview.demo_commit.base_sha} → {overview.demo_commit.head_sha} · by {overview.demo_commit.author}
          </p>
          <button
            onClick={onAnalyze}
            disabled={analyzing || !canAnalyze}
            className="mt-4 bg-signal-indigo hover:bg-signal-indigo/90 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-sm"
          >
            {analyzing ? "Analyzing…" : canAnalyze ? "Analyze this change" : "Viewer role cannot run analysis"}
          </button>
          {error && <p className="risk-CRITICAL text-xs mt-2">{error}</p>}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="bg-ink-800 border border-ink-600 rounded-sm p-4">
      <p className="text-mist-500 text-xs">{label}</p>
      <p className="font-display text-lg text-mist-100 mt-1">{value}</p>
    </div>
  );
}

// ---- Change Analysis ---------------------------------------------------------
function AnalysisTab({
  overview, analysis, onAnalyze, analyzing, error, canAnalyze,
}: {
  overview: any;
  analysis: AnalysisResult | null;
  onAnalyze: () => void;
  analyzing: boolean;
  error: string | null;
  canAnalyze: boolean;
}) {
  return (
    <div className="rise-in">
      <SectionHeader title="Change Analysis" sub="Select a change and extract what it touches." />
      {overview?.demo_commit && (
        <div className="bg-ink-800 border border-ink-600 rounded-sm p-4 mb-6">
          <p className="font-mono text-sm text-mist-100">{overview.demo_commit.pr_title}</p>
          <p className="text-mist-500 text-xs mt-1">{overview.demo_commit.base_sha} → {overview.demo_commit.head_sha}</p>
          <button
            onClick={onAnalyze}
            disabled={analyzing || !canAnalyze}
            className="mt-3 bg-signal-indigo hover:bg-signal-indigo/90 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-sm"
          >
            {analyzing ? "Analyzing…" : canAnalyze ? analysis ? "Analyze again" : "Analyze this change" : "Viewer role cannot run analysis"}
          </button>
          {error && <p className="risk-CRITICAL text-xs mt-2">{error}</p>}
        </div>
      )}
      {analysis && (
        <div>
          <p className="text-mist-500 text-xs mb-2">Changed files & symbols</p>
          <div className="space-y-2">
            {analysis.changed_files.map((f) => (
              <div key={f.path} className="bg-ink-800 border border-ink-600 rounded-sm p-3">
                <div className="evidence-line text-mist-100">{f.path}</div>
                <div className="text-xs text-mist-500 mt-1">+{f.additions} / -{f.deletions}</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {f.changed_symbols.map((s) => (
                    <span key={s} className="text-xs font-mono bg-ink-700 px-2 py-1 rounded-sm text-mist-300">{s}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4">
            <RiskBadge level={analysis.risk.level} score={analysis.risk.score} />
          </div>
        </div>
      )}
    </div>
  );
}

// ---- Risk Report -------------------------------------------------------------
function RiskTab({ analysis }: { analysis: AnalysisResult }) {
  return (
    <div className="rise-in">
      <SectionHeader title="Risk Report" />
      <EvidenceBanner status={analysis.risk.evidence_status} steps={analysis.verification_plan} />
      <div className="mb-6"><RiskBadge level={analysis.risk.level} score={analysis.risk.score} /></div>
      <div className="space-y-3 mb-6">
        {analysis.risk.factors.map((f) => (
          <div key={f.key} className="bg-ink-800 border border-ink-600 rounded-sm p-3">
            <div className="flex justify-between text-sm">
              <span className="text-mist-100">{f.label}</span>
              <span className="text-mist-500 font-mono text-xs">+{f.contribution} pts</span>
            </div>
            <div className="h-1.5 bg-ink-700 rounded-sm mt-2 overflow-hidden">
              <div className="h-full bg-signal-indigo" style={{ width: `${f.value * 100}%` }} />
            </div>
            <p className="text-mist-500 text-xs mt-2">{f.detail}</p>
          </div>
        ))}
      </div>
      <p className="text-mist-500 text-xs mb-2">Rationale</p>
      <ul className="list-disc list-inside space-y-1 text-sm text-mist-300">
        {analysis.risk.rationale.map((r, i) => <li key={i}>{r}</li>)}
      </ul>
    </div>
  );
}

// ---- Test Recommendations -----------------------------------------------------
function TestsTab({ analysis }: { analysis: AnalysisResult }) {
  return (
    <div className="rise-in">
      <SectionHeader title="Test Recommendations" sub={`${analysis.test_recommendations.length} highest-value tests, ranked — not the full suite.`} />
      <EvidenceBanner status={analysis.risk.evidence_status} steps={analysis.verification_plan} />
      <div className="space-y-3">
        {analysis.test_recommendations.map((t) => (
          <div key={t.test_name} className="bg-ink-800 border border-ink-600 rounded-sm p-4">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-mist-500 text-xs mr-2">#{t.priority_rank}</span>
                <span className="font-mono text-sm text-mist-100">{t.test_name}</span>
                {t.is_hidden_dependency && (
                  <span className="ml-2 text-[11px] risk-CRITICAL bg-risk-CRITICAL border px-1.5 py-0.5 rounded-sm">hidden dependency</span>
                )}
              </div>
              <span className="text-mist-500 text-xs font-mono">{Math.round(t.relevance_score * 100)}% relevant</span>
            </div>
            <div className="evidence-line text-mist-500 mt-1">{t.file}:{t.line}</div>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
              <span className="border border-ink-600 rounded-sm px-1.5 py-0.5 text-mist-300">affected: {t.affected_symbol}</span>
              <span className="border border-ink-600 rounded-sm px-1.5 py-0.5 text-mist-300">history: {t.historical_failure_rate === null ? "none" : `${Math.round(t.historical_failure_rate * 100)}% failure rate`}</span>
              <span className="border border-ink-600 rounded-sm px-1.5 py-0.5 text-mist-300">{t.evidence_status}</span>
            </div>
            <p className="text-mist-300 text-sm mt-2">{t.reason}</p>
            <details className="mt-2">
              <summary className="text-xs text-signal-indigo cursor-pointer">Evidence chain</summary>
              <ol className="mt-2 space-y-1">
                {t.evidence_chain.map((step, i) => (
                  <li key={i} className="evidence-line text-mist-500">
                    {i > 0 && "→ "}{step.symbol.symbol} ({step.symbol.file}:{step.symbol.line})
                  </li>
                ))}
              </ol>
            </details>
            <p className="text-mist-500 text-[11px] mt-2">Evidence: {t.evidence_source}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---- Historical Evidence --------------------------------------------------
function HistoryTab({ analysis }: { analysis: AnalysisResult }) {
  return (
    <div className="rise-in">
      <SectionHeader title="Historical Evidence" sub={String(analysis.provenance.databricks_note || "Historical evidence source unavailable.")} />
      <div className="space-y-2">
        {analysis.historical_failures.length === 0 && (
          <p className="text-mist-500 text-sm">No historical runs recorded for the impacted symbols.</p>
        )}
        {analysis.historical_failures.map((h, i) => (
          <div key={i} className="bg-ink-800 border border-ink-600 rounded-sm p-3 flex justify-between items-center">
            <div>
              <div className="font-mono text-sm text-mist-100">{h.test_name}</div>
              <div className="text-mist-500 text-xs mt-1">{h.symbol} · {h.commit_sha} · {h.occurred_at ? new Date(h.occurred_at).toLocaleDateString() : "time unavailable"}</div>
              {h.failure_message && <div className="text-mist-500 text-xs mt-1 italic">{h.failure_message}</div>}
            </div>
            <span className={`text-xs px-2 py-1 rounded-sm border ${h.outcome === "fail" ? "risk-CRITICAL bg-risk-CRITICAL" : "risk-LOW bg-risk-LOW"}`}>
              {h.outcome.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---- AI Explanation -----------------------------------------------------
function ExplanationTab({ analysis }: { analysis: AnalysisResult }) {
  const e = analysis.ai_explanation;
  return (
    <div className="rise-in">
      <SectionHeader title="AI Explanation" sub={`Generated by: ${e.generated_by}`} />
      <p className="text-mist-300 text-sm leading-relaxed mb-6">{e.summary}</p>

      <p className="text-mist-500 text-xs mb-2">Likely failure modes</p>
      <ul className="list-disc list-inside space-y-1 text-sm text-mist-300 mb-6">
        {e.likely_failure_modes.map((m, i) => <li key={i}>{m}</li>)}
      </ul>

      <p className="text-mist-500 text-xs mb-2">Review checklist</p>
      <ul className="space-y-1.5 text-sm text-mist-300 mb-6">
        {e.review_checklist.map((c, i) => (
          <li key={i} className="flex gap-2">
            <input type="checkbox" className="mt-1" />
            <span>{c}</span>
          </li>
        ))}
      </ul>

      <p className="text-mist-500 text-xs mt-6 pt-4 border-t border-ink-600">{e.disclaimer}</p>
    </div>
  );
}

// ---- Checkpoints -----------------------------------------------------------
function CheckpointsTab({ repoId }: { repoId: string }) {
  const [checkpoints, setCheckpoints] = useState<any[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.checkpoints(repoId).then(setCheckpoints).catch((e) => setError(e.message));
  }, [repoId]);

  if (error) return <ErrorState message={error} />;
  if (!checkpoints) return <CenterMessage text="Loading checkpoints…" />;

  if (checkpoints.length === 0) {
    return <EmptyState title="No verified Entire checkpoints available" body="This environment cannot retrieve valid Entire checkpoint/session records. No checkpoint IDs are shown or inferred." />;
  }

  return (
    <div className="rise-in">
      <SectionHeader title="Checkpoints" sub="What changed, why, and which session or person produced it." />
      <div className="space-y-3">
        {checkpoints.map((c) => (
          <div key={c.id} className="bg-ink-800 border border-ink-600 rounded-sm p-4">
            <div className="flex justify-between items-start">
              <p className="font-display text-sm text-mist-100">{c.title}</p>
              <span className="text-xs text-mist-500">{c.author_type === "ai_agent" ? "AI agent" : "Human"}</span>
            </div>
            <p className="text-mist-300 text-sm mt-1">{c.summary}</p>
            {c.prompt_excerpt && (
              <p className="evidence-line text-mist-500 mt-2 italic">{c.prompt_excerpt}</p>
            )}
            <div className="text-xs text-mist-500 mt-2">
              {c.author_name}{c.session_id ? ` · session ${c.session_id}` : ""} · {c.commit_sha}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---- Settings ----------------------------------------------------------
function SettingsTab({ repoId }: { repoId: string }) {
  const [settingsData, setSettingsData] = useState<any>(null);
  const [audit, setAudit] = useState<any[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.settings(repoId).then(setSettingsData).catch((e) => setError(e.message));
    api.auditLog(repoId).then(setAudit).catch(() => setAudit([]));
  }, [repoId]);

  if (error) return <ErrorState message={error} />;
  if (!settingsData) return <CenterMessage text="Loading settings…" />;

  return (
    <div className="rise-in">
      <SectionHeader title="Settings" />
      <p className="text-mist-500 text-xs mb-2">Integration status</p>
      <div className="grid grid-cols-2 gap-3 mb-6">
        {Object.entries(settingsData.integrations).map(([k, v]: any) => (
          <div key={k} className="bg-ink-800 border border-ink-600 rounded-sm p-3">
            <p className="text-mist-500 text-xs">{k.replace(/_/g, " ")}</p>
            <p className="text-mist-100 text-sm mt-1 font-mono">{String(v)}</p>
          </div>
        ))}
      </div>

      <p className="text-mist-500 text-xs mb-2">Members & roles</p>
      <div className="space-y-2 mb-6">
        {settingsData.members.map((m: any) => (
          <div key={m.user_id} className="bg-ink-800 border border-ink-600 rounded-sm p-3 flex justify-between">
            <span className="text-mist-100 text-sm">{m.github_login}</span>
            <span className="text-mist-500 text-xs uppercase">{m.role}</span>
          </div>
        ))}
      </div>

      {audit && audit.length > 0 && (
        <>
          <p className="text-mist-500 text-xs mb-2">Recent audit log</p>
          <div className="space-y-1">
            {audit.slice(0, 10).map((a) => (
              <div key={a.id} className="evidence-line text-mist-500 flex justify-between">
                <span>{a.action} — {a.detail}</span>
                <span>{new Date(a.created_at).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="border border-signal-critical/40 bg-risk-CRITICAL rounded-sm p-6 max-w-lg">
      <p className="risk-CRITICAL text-sm font-medium mb-1">Something went wrong</p>
      <p className="text-mist-300 text-sm">{message}</p>
    </div>
  );
}
