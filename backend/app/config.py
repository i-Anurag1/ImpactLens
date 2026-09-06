"""
Central configuration.

Every external integration point (GitHub OAuth, the real Entire CLI/Graph
binary, and a real Databricks SQL warehouse) is read from environment
variables here. In this demo build none of those env vars are required —
everything falls back to a safe mocked mode so the app runs with zero
external accounts. Flip DEMO_MODE=false and fill in the rest once you have
real credentials.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # --- App / DB ---
    APP_NAME = "ImpactLens AI"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-change-me")
    # Swap DATABASE_URL to a real Postgres DSN in production, e.g.
    # postgresql+psycopg2://user:pass@host:5432/impactlens
    # SQLAlchemy makes this a one-line change; the schema is identical.
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./impactlens.db")

    # --- Demo / mock toggles ---
    DEMO_MODE = _bool("DEMO_MODE", True)

    # --- GitHub OAuth (unused while DEMO_MODE=True) ---
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_OAUTH_REDIRECT_URI = os.getenv(
        "GITHUB_OAUTH_REDIRECT_URI", "http://localhost:8000/api/auth/github/callback"
    )
    GITHUB_OAUTH_SCOPES = "read:user repo"

    # --- Entire CLI / Entire Graph ---
    # In real mode the adapter shells out to the `entire` binary, e.g.
    #   entire graph impact --symbol <sym> --repo <path> --format json
    # See https://github.com/entireio/entire-graph and
    # https://github.com/entireio/cli for the documented commands this
    # adapter mirrors (search, def, neighbors, impact, diff, snapshot).
    ENTIRE_CLI_PATH = os.getenv("ENTIRE_CLI_PATH", "entire")
    ENTIRE_REPOS_ROOT = os.getenv("ENTIRE_REPOS_ROOT", "./repos")
    USE_REAL_ENTIRE_CLI = _bool("USE_REAL_ENTIRE_CLI", False)

    # --- Databricks ---
    # Real mode would use the Databricks SQL connector against a
    # Unity-Catalog-governed warehouse. See
    # https://docs.databricks.com/aws/en/dev-tools/databricks-apps
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "")
    DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH", "")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
    USE_REAL_DATABRICKS = _bool("USE_REAL_DATABRICKS", False)

    # --- LLM (explanation layer only — never scores or invents evidence) ---
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    USE_REAL_LLM = _bool("USE_REAL_LLM", False)

    # --- Misc ---
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")


settings = Settings()
