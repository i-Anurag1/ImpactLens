from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db, AuditLog, gen_id
from ..auth import demo_login, create_session_token, get_current_user, DEMO_USER
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
