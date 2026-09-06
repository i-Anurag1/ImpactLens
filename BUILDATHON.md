# ImpactLens AI — Bengaluru Tech Week Buildathon 2026 / Track 2

## Problem and solution

Reviewers can see a diff but often cannot see indirect consumers, historically
fragile tests, or the uncertainty caused by dynamic code. ImpactLens produces
an evidence-backed merge brief:

```text
Code change / PR
  → Entire Graph structural evidence
  → affected symbols, callers/callees and file:line provenance
  → deterministic risk engine
  → Databricks historical test evidence
  → ranked tests and grounded explanation
  → source/test/runtime verification plan
```

Entire Graph is the **evidence layer**. ImpactLens is the **decision layer**.
The deterministic risk engine owns the score; the AI layer may only summarize
structured evidence and cannot add edges, files, tests, or failure rates.

## Evidence and provenance model

Every graph result has a source, confidence, limitations, completeness flag,
and status:

- `CONFIRMED`: complete, sufficiently confident structural result.
- `PARTIAL`: useful but incomplete/static or fallback evidence. Potential
  relationships raise caution but are never displayed as certain runtime fact.
- `VERIFY REQUIRED`: the graph query is unavailable or cannot resolve the
  relationship. The product preserves the unknown rather than inventing it.

Each ranked test shows its affected symbol, evidence chain with file:line,
historical failure rate when available, graph source, status, and whether
verification is required. Risk factors separately state confirmed/potential
consumer counts and treat low confidence as uncertainty—not as a confirmed
blast radius.

## Curveball: graph is evidence, not an oracle

The invalidated assumption was: *a static graph can always resolve the call
chain needed to rank tests*. It cannot for dynamic dispatch, reflection,
generated code, incomplete dependencies, or parser limitations.

`demo_data.py` includes `INCOMPLETE_ANALYSIS_FIXTURE`, a realistic dynamic
pricing-provider dispatch. It deliberately creates **no edge**. The regression
test verifies that a `VERIFY REQUIRED` result has no fabricated relation, marks
risk/test output as requiring verification, and offers the safe path:

1. inspect changed source and listed callers/callees;
2. run the ranked tests, especially the indirect inventory test;
3. exercise the currency-rounding/dynamic-provider path at runtime.

## Databricks

When enabled, `databricks_adapter.py` reads the configurable
`DATABRICKS_HISTORY_TABLE` (default: `impactlens_history`) through the
Databricks SQL connector. Failure rates influence deterministic test ranking
and risk. If configuration or the warehouse is unavailable, the adapter uses
bundled demo history and surfaces `Bundled demo history (fallback)` plus the
reason. It never labels fallback rows as live Databricks evidence.

## Setup and environment

Required only for real integrations:

```text
GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET
GITHUB_OAUTH_REDIRECT_URI
FRONTEND_URL=http://localhost:3000

USE_REAL_ENTIRE_CLI=true
ENTIRE_CLI_PATH=entire

USE_REAL_DATABRICKS=true
DATABRICKS_HOST
DATABRICKS_HTTP_PATH
DATABRICKS_TOKEN
DATABRICKS_HISTORY_TABLE=impactlens_history
```

Without these values, the application is still demoable with explicitly
labeled local authentication and fallback evidence.

## Demo flow

1. Sign in with GitHub if OAuth is configured, or choose the clearly labeled
   local demo fallback.
2. Confirm user, repository, and role in the dashboard sidebar.
3. Analyze “Fix currency rounding in processPayment”.
4. Inspect the evidence status, graph provenance, risk factors, and ranked
   tests; follow the visible verification plan.
5. Show that viewer role is disabled in UI and blocked by the backend, while
   developer/admin may analyze and admin alone manages roles/audit logs.

## Verification

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm run build
```

## Checkpoints

`.entire/settings.json` is preserved. At final verification the `entire` CLI
was not executable on this shell, so no valid Entire checkpoint/session ID is
claimed or fabricated. The application shows an explicit unavailable state
instead of demo checkpoint IDs. Create/check actual checkpoints in an active
Entire CLI/agent session, then record their real IDs here.

## Limitations and responsible use

ImpactLens prioritizes review work; it does not prove runtime correctness or
replace code review, security review, CI, or production validation. Static
analysis may miss dynamic behavior. Historical rates are retrospective signals
and should not be used to assess individual developers. OAuth secrets,
Databricks tokens, local `.env` files, and generated dependency folders are
excluded from the submission archive.

Final Git SHA: populated by the release commit.
