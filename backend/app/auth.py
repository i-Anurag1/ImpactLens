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
import base64
import datetime
import hashlib
import secrets
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

# The public product vocabulary.  The legacy aliases keep existing local
# databases usable without granting a privilege that the new model would not.
ROLE_ALIASES = {"owner": "admin", "member": "developer", "reviewer": "viewer"}
VALID_ROLES = {"viewer", "developer", "admin"}


def normalized_role(role: str) -> str:
    return ROLE_ALIASES.get(role, role)


def github_oauth_configured() -> bool:
    return bool(
        settings.GITHUB_CLIENT_ID
        and settings.GITHUB_CLIENT_SECRET
        and settings.GITHUB_OAUTH_REDIRECT_URI
    )


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


def create_oauth_state() -> str:
    """A short-lived signed state token.  It carries no GitHub secret."""
    payload = {
        "kind": "github_oauth_state",
        "nonce": secrets.token_urlsafe(24),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def validate_oauth_state(state: str) -> None:
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("kind") != "github_oauth_state":
            raise JWTError("Unexpected OAuth state")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")


def encrypt_github_token(token: str) -> str:
    """Encrypt a provider token before storage; the raw token never leaves
    the backend or appears in a response/log."""
    from cryptography.fernet import Fernet

    key = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
    return Fernet(key).encrypt(token.encode()).decode()


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

    provision_demo_repository(user, db, role="admin")
    return user


def provision_demo_repository(user: User, db: Session, role: str = "developer") -> Repository:
    """Provision the explicitly-labelled bundled repository for a signed-in
    user.  It is a local fallback, never represented as a GitHub repository
    connected on the user's behalf."""
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
        db.add(Membership(id=gen_id(), user_id=user.id, repository_id=repo.id, role=role))
        db.commit()
    elif normalized_role(membership.role) != role and role == "admin":
        membership.role = role
        db.commit()
    return repo


def get_repository_membership(repo_id: str, user: User, db: Session) -> Membership:
    membership = db.query(Membership).filter(
        Membership.user_id == user.id, Membership.repository_id == repo_id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="No access to this repository")
    role = normalized_role(membership.role)
    if role not in VALID_ROLES:
        raise HTTPException(status_code=403, detail="Repository role is invalid")
    # Persist a transparent, one-time legacy migration when an existing DB is
    # encountered.  New writes always use the required three-role model.
    if membership.role != role:
        membership.role = role
        db.commit()
        db.refresh(membership)
    return membership


def require_role(*allowed_roles: str):
    """Backend-enforced repository RBAC dependency factory."""
    allowed = {normalized_role(role) for role in allowed_roles}

    def _dep(
        repo_id: str,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> Membership:
        membership = get_repository_membership(repo_id, user, db)
        if membership.role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{membership.role}' cannot perform this action "
                       f"(requires one of {sorted(allowed)})",
            )
        return membership
    return _dep


def upsert_github_user(profile: dict, github_token: str, db: Session) -> User:
    """Create/update the OAuth identity without returning or exposing its
    GitHub access token.  Repository connection remains a separate, scoped
    action; this build continues to offer the local demo repository."""
    login = profile.get("login")
    if not login:
        raise HTTPException(status_code=502, detail="GitHub did not return a login")
    user = db.query(User).filter(User.github_login == login).first()
    attrs = {
        "display_name": profile.get("name") or login,
        "avatar_url": profile.get("avatar_url") or "",
        "github_access_token_encrypted": encrypt_github_token(github_token),
    }
    if not user:
        user = User(id=gen_id(), github_login=login, **attrs)
        db.add(user)
    else:
        for key, value in attrs.items():
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    provision_demo_repository(user, db, role="developer")
    return user
