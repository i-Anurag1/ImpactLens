from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .db import init_db
from .routers import auth, repos, analyze, checkpoints, settings_router

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak stack traces / internals to the client.
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal error. This has been logged.", "error_type": type(exc).__name__},
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "demo_mode": settings.DEMO_MODE,
        "entire_cli_mode": "real" if settings.USE_REAL_ENTIRE_CLI else "mock",
        "databricks_mode": "real" if settings.USE_REAL_DATABRICKS else "mock",
    }


app.include_router(auth.router)
app.include_router(repos.router)
app.include_router(analyze.router)
app.include_router(checkpoints.router)
app.include_router(settings_router.router)
