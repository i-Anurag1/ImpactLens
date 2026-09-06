# ImpactLens AI

Turns every code change into an evidence-backed test plan, by combining **Entire
Graph's** code relationships, **Entire Checkpoints'** development context,
**Databricks'** historical engineering data, and AI reasoning that explains —
never invents — that evidence.

This build runs completely standalone with zero external accounts: GitHub
OAuth, the Entire CLI, and Databricks are all behind adapter interfaces that
default to clearly-labeled mock/demo data. Flip a handful of environment
variables and each one switches to the real service without touching the
frontend or the risk/evidence logic.

## The demo flow

1. **Sign in** (demo GitHub identity, real OAuth is a config away)
2. **Repository Overview** — the bundled demo repo (`checkout-service`) is
   already connected, with one pending change: *"Fix currency rounding in
   processPayment."*
3. **Analyze the change** — the backend extracts the changed symbols, queries
   Entire Graph for impact/callers/diff, and discovers that
   `PaymentService.processPayment` reaches `InventoryService.reserveStock`
   through a shared rounding utility that isn't touched by the diff at all —
   a **hidden dependency**.
4. **Risk Report** — deterministic engine scores this **HIGH** (52/100) from
   dependency depth, consumer count, public-API exposure, coverage gaps, and
   historical failure rate. No LLM involved in this step.
5. **Test Recommendations** — 4 ranked tests (not the whole suite), each with
   a full evidence chain down to file:line, including the hidden-dependency
   test that a line-diff review would never surface.
6. **Historical Evidence** — seeded Databricks-style test-run history shows
   this exact code has failed before.
7. **AI Explanation** — a plain-language summary, failure modes, and review
   checklist generated *from* the structured evidence above — the model
   cannot change the score or invent a dependency.
8. **Checkpoints** — shows the AI coding-agent session and prompt that
   produced the change (Entire CLI checkpoint context).

## Architecture

```
┌────────────────────┐        ┌──────────────────────────────────────┐
│   Next.js / React    │  HTTP  │              FastAPI                  │
│   (Tailwind, TS)      │◀──────▶│  auth · repos · analyze · checkpoints │
│   9 dashboard views   │        │  settings (RBAC, audit log)           │
└────────────────────┘        └───────────────┬────────────────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    ▼                           ▼                           ▼
          entire_adapter.py           risk_engine.py /          databricks_adapter.py
      (Entire Graph + CLI,            ranker.py /                (historical evidence,
       mock ↔ real via env var)       ai_explain.py               mock ↔ real via env var)
                                     (deterministic scoring
                                      + template/LLM explain)
                                                │
                                                ▼
                                     PostgreSQL / SQLite
                                (users, repos, RBAC, analyses, audit log)
```

- **Backend never fakes success.** Every mocked adapter response is labeled
  (`source`, `heuristic`, `seeded_demo_data`) and surfaced to the UI.
- **Risk engine is pure arithmetic** (`risk_engine.py`) — no network calls,
  fully deterministic, unit-tested (`backend/tests/test_risk_engine.py`).
- **The AI layer only explains.** It receives the already-computed risk +
  evidence as structured JSON and is instructed (and structurally unable) to
  invent dependencies or change the score — see `ai_explain.py`.

## Running it

### Option A — Docker Compose (recommended)
```bash
docker compose up --build
```
- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (docs at `/docs`)

### Option B — local dev
```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# frontend, in a second terminal
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000, click **"Sign in with GitHub (demo)"**, and run
the analysis.

### Tests
```bash
cd backend
pip install pytest
pytest -q
```

## Switching mocks to real services

Nothing in the frontend or in `risk_engine.py` / `test_ranker` needs to
change for any of these — only the adapter files and `.env`.

| Integration | Env vars | What changes |
|---|---|---|
| **GitHub OAuth** | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_OAUTH_REDIRECT_URI` | Wire the standard OAuth code-exchange flow into `auth.py` in place of `demo_login()`; store the returned access token encrypted in `User.github_access_token_encrypted`. |
| **Entire CLI / Entire Graph** | `USE_REAL_ENTIRE_CLI=true`, `ENTIRE_CLI_PATH`, `ENTIRE_REPOS_ROOT` | `entire_adapter.py`'s functions call `_run_real_cli([...])`, which shells out to the documented commands (`entire graph search/def/neighbors/impact/diff/snapshot`, `entire checkpoint list`) per [Entire CLI](https://github.com/entireio/cli) and [Entire Graph](https://github.com/entireio/entire-graph). Response shape is already normalized into `GraphQueryResult`/`Checkpoint`, so nothing downstream changes. |
| **Databricks** | `USE_REAL_DATABRICKS=true`, `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH`, `DATABRICKS_TOKEN` | `databricks_adapter.py`'s functions issue Databricks SQL against the Delta tables described in its module docstring instead of reading `demo_data.py`. |
| **AI explanation (LLM)** | `USE_REAL_LLM=true`, `ANTHROPIC_API_KEY` | `ai_explain.py` calls the Anthropic Messages API with the same structured evidence and a system prompt that forbids inventing facts; falls back to the deterministic template engine otherwise. |
| **Database** | `DATABASE_URL=postgresql+psycopg2://...` | SQLAlchemy models are already Postgres-ready; no schema changes needed. |

## What's real vs. mocked in this build

- **Real:** RBAC (owner/member/reviewer), JWT sessions, rate limiting, audit
  log, the deterministic risk engine, test ranking and evidence-chain
  construction, the full REST API, the interactive dependency graph, and all
  9 dashboard views.
- **Mocked (clearly labeled in the UI and API responses):** the GitHub OAuth
  identity, the Entire Graph/CLI responses (structured exactly like the real
  CLI's documented output), the Databricks historical test-run data, and the
  AI explanation (template engine by default; a real Claude call is one env
  var + API key away).

## Extending for a new "curveball" requirement

The pipeline in `backend/app/routers/analyze.py::_run_pipeline` is a plain
function composing independent modules (`entire_adapter`, `risk_engine`,
`ranker`, `databricks_adapter`, `ai_explain`). A new data source or scoring
rule is a new module plus one more line in that function and one more
`RiskFactor`/weight in `risk_engine.WEIGHTS` — no rewrite required.

## Project layout

```
backend/
  app/
    config.py            # every real-vs-mock switch, env-driven
    db.py                 # SQLAlchemy models (Postgres-ready)
    schemas.py             # shared evidence/risk Pydantic models
    demo_data.py            # the seeded demo repo + hidden dependency
    entire_adapter.py        # Entire Graph/CLI adapter (mock ↔ real)
    databricks_adapter.py     # historical intelligence adapter (mock ↔ real)
    risk_engine.py              # deterministic risk scoring
    ranker.py                    # test ranking + evidence chains
    ai_explain.py                 # explanation layer (template ↔ real LLM)
    auth.py                        # mock GitHub OAuth + JWT + RBAC
    routers/                        # FastAPI route modules
  tests/test_risk_engine.py          # determinism + evidence-grounding tests
frontend/
  app/
    page.tsx                          # login
    dashboard/page.tsx                  # all 9 dashboard views
    components/DependencyGraph.tsx        # interactive graph
    lib/api.ts                              # typed API client
docker-compose.yml
```
