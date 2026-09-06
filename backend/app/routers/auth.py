from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..db import get_db, AuditLog, gen_id
from ..auth import (
    demo_login, create_oauth_state, create_session_token, get_current_user,
    github_oauth_configured, upsert_github_user, validate_oauth_state,
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/status")
def auth_status():
    """Safe, public integration status used only to choose the login UI."""
    return {
        "github_oauth_configured": github_oauth_configured(),
        "local_demo_available": True,
    }


@router.get("/github/login")
def github_login():
    if not github_oauth_configured():
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth is not configured. Use the clearly labelled local demo sign-in.",
        )
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
        "scope": settings.GITHUB_OAUTH_SCOPES,
        "state": create_oauth_state(),
    }
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{urlencode(params)}")


@router.get("/github/callback")
async def github_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    db: Session = Depends(get_db),
):
    if error:
        return RedirectResponse(f"{settings.FRONTEND_URL}/?oauth_error={error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="GitHub OAuth callback is missing code or state")
    if not github_oauth_configured():
        raise HTTPException(status_code=503, detail="GitHub OAuth is not configured")
    validate_oauth_state(state)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_OAUTH_REDIRECT_URI,
                },
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            github_token = token_data.get("access_token")
            if not github_token:
                raise HTTPException(status_code=502, detail="GitHub did not issue an access token")
            profile_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {github_token}", "Accept": "application/vnd.github+json"},
            )
            profile_response.raise_for_status()
    except HTTPException:
        raise
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="GitHub OAuth exchange failed")

    user = upsert_github_user(profile_response.json(), github_token, db)
    session_token = create_session_token(user.id)
    db.add(AuditLog(id=gen_id(), user_id=user.id, action="github_oauth_login", detail="GitHub OAuth callback completed"))
    db.commit()
    # This is ImpactLens' short-lived session JWT, not the provider token.
    return RedirectResponse(f"{settings.FRONTEND_URL}/?oauth_token={session_token}")


@router.post("/demo-login")
def login_demo(db: Session = Depends(get_db)):
    """
    Stands in for the GitHub OAuth callback. In real mode this endpoint
    would instead be `/api/auth/github/callback`, exchanging an OAuth
    `code` for a token and fetching the real GitHub identity — see
    auth.py's module docstring for the exact flow this replaces.
    """
    user = demo_login(db)
    token = create_session_token(user.id)
    db.add(AuditLog(id=gen_id(), user_id=user.id, action="login",
                     detail="demo GitHub OAuth login"))
    db.commit()
    return {
        "token": token,
        "user": {
            "id": user.id, "github_login": user.github_login,
            "display_name": user.display_name, "avatar_url": user.avatar_url,
        },
        "demo_mode": settings.DEMO_MODE,
    }


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {
        "id": user.id, "github_login": user.github_login,
        "display_name": user.display_name, "avatar_url": user.avatar_url,
    }
