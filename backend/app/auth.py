"""
Auth layer.

Real mode would run the standard GitHub OAuth web flow:
  1. GET  /api/auth/github/login       -> 302 to github.com/login/oauth/authorize
  2. GET  /api/auth/github/callback    -> exchange `code` for an access token,
     fetch /user, upsert User row, encrypt+store the token server-side,
     issue our own signed session JWT to the browser (never the raw GitHub token).

DEMO_MODE (default) skips the redirect dance and issues the same session
JWT for a fixed demo GitHub identity, so the rest of the app — RBAC,
audit logging, repo scoping — is exercised exactly as it would be in
production.
"""
import datetime
from typing import Optional

from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db, User, Membership, Repository, gen_id
from . import demo_data as D

ALGORITHM = "HS256"
DEMO_USER = {
    "github_login": "priya-dev",
    "display_name": "Priya Sharma",
    "avatar_url": "https://avatars.githubusercontent.com/u/0000001?v=4",
}


def create_session_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def _decode(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired session")


def get_current_user(
    authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    user_id = _decode(token)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def demo_login(db: Session) -> User:
    """Issues (or reuses) the fixed demo identity + seeds the demo repo and
    an owner membership, mirroring what a real OAuth callback would set up
    on first login."""
    user = db.query(User).filter(User.github_login == DEMO_USER["github_login"]).first()
    if not user:
        user = User(id=gen_id(), **DEMO_USER)
        db.add(user)
        db.commit()
        db.refresh(user)

    repo = db.query(Repository).filter(Repository.full_name == D.REPO_FULL_NAME).first()
    if not repo:
        repo = Repository(
            id=gen_id(), full_name=D.REPO_FULL_NAME,
            default_branch=D.DEFAULT_BRANCH, is_demo=True,
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)

    membership = db.query(Membership).filter(
        Membership.user_id == user.id, Membership.repository_id == repo.id
    ).first()
    if not membership:
        db.add(Membership(id=gen_id(), user_id=user.id, repository_id=repo.id, role="owner"))
        db.commit()

    return user


def require_role(*allowed_roles: str):
    """RBAC dependency factory: use as
    `repo=Depends(require_role("owner","member"))` on a route that takes
    repo_id as a path/query param — wired per-route in routers/*.py."""
    def _dep(
        repo_id: str,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Membership:
        membership = db.query(Membership).filter(
            Membership.user_id == user.id, Membership.repository_id == repo_id
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="No access to this repository")
        if membership.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{membership.role}' cannot perform this action "
                       f"(requires one of {allowed_roles})",
            )
        return membership
    return _dep
