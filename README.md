# ImpactLens AI

ImpactLens turns a code change into an auditable merge decision:

`change → structural evidence → impact → deterministic risk → historical test signal → ranked tests → verify`

The product does not treat a graph as an oracle. Every analysis declares one
of `CONFIRMED`, `PARTIAL`, or `VERIFY REQUIRED`, exposes provenance, and gives
the reviewer a concrete verification path.

## Run locally

```powershell
# backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload

# frontend (second terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. If OAuth is not configured, choose **Continue
in local demo**; it is intentionally distinct from GitHub OAuth.

## Authentication and authorization

- GitHub OAuth uses `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, and
  `GITHUB_OAUTH_REDIRECT_URI`. The backend exchanges the code, encrypts the
  provider access token at rest, and returns only an ImpactLens session JWT.
- `FRONTEND_URL` controls the post-OAuth callback destination.
- Without all OAuth variables, the app stays runnable through a clearly
  labeled local demo identity. It never claims that fallback is GitHub OAuth.
- Repository RBAC is enforced on the backend: `viewer` can read, `developer`
  and `admin` can run analysis, and only `admin` can change roles or read the
  audit log. Missing sessions return 401; insufficient roles return 403.

## Evidence modes

Set `USE_REAL_ENTIRE_CLI=true` and `ENTIRE_CLI_PATH` to enable actual Entire
Graph commands. If the CLI cannot be invoked, ImpactLens returns an empty
`VERIFY REQUIRED` result for real mode; it does not fabricate graph edges.
The local Buildathon demo uses a **bundled graph fixture** and labels it
`PARTIAL` everywhere because it is not a live CLI result.

Databricks reads `impactlens_history` by default when
`USE_REAL_DATABRICKS=true` with `DATABRICKS_HOST`, `DATABRICKS_HTTP_PATH`, and
`DATABRICKS_TOKEN`. Connection/configuration failures fall back to bundled
demo history with an explicit provenance message.

## Verify

```powershell
cd backend
python -m pytest -q

cd ..\frontend
npm run build
```

See [BUILDATHON.md](BUILDATHON.md) for architecture, the Curveball response,
demo sequence, limitations, and checkpoint status.
