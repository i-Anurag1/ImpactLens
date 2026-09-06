from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db, User, Membership, AuditLog, gen_id
from ..auth import get_current_user, get_repository_membership, github_oauth_configured
from ..config import settings
from .. import databricks_adapter, entire_adapter
from .repos import _authorized_repo

router = APIRouter(prefix="/api/repos", tags=["settings"])

VALID_ROLES = {"viewer", "developer", "admin"}


@router.get("/{repo_id}/settings")
def get_settings(repo_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = _authorized_repo(repo_id, user, db)
    members = db.query(Membership).filter(Membership.repository_id == repo_id).all()
    member_rows = []
    for m in members:
        u = db.query(User).filter(User.id == m.user_id).first()
        member_rows.append({"user_id": u.id, "github_login": u.github_login, "role": m.role})

    return {
        "repository": {"id": repo.id, "full_name": repo.full_name},
        "members": member_rows,
        "integrations": {
            "github_oauth_configured": github_oauth_configured(),
            "entire_graph": entire_adapter.graph_status()["source"],
            "databricks": databricks_adapter.evidence_metadata()["source"],
            "ai_explanation_mode": "claude-sonnet-4-6" if settings.USE_REAL_LLM else "local deterministic fallback",
        },
        "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
    }


@router.put("/{repo_id}/members/{target_user_id}/role")
def update_role(
    repo_id: str, target_user_id: str, role: str,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    if role not in VALID_ROLES:
        raise HTTPException(status_code=422, detail=f"role must be one of {VALID_ROLES}")

    requester_membership = get_repository_membership(repo_id, user, db)
    if requester_membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only an admin can change member roles")

    target = db.query(Membership).filter(
        Membership.user_id == target_user_id, Membership.repository_id == repo_id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found on this repository")

    target.role = role
    db.add(AuditLog(id=gen_id(), user_id=user.id, action="role_change",
                     detail=f"set {target_user_id} to {role} on repo {repo_id}"))
    db.commit()
    return {"ok": True, "user_id": target_user_id, "role": role}


@router.get("/{repo_id}/audit-log")
def audit_log(repo_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    requester_membership = get_repository_membership(repo_id, user, db)
    if requester_membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only an admin can view the audit log")

    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    return [
        {"id": r.id, "user_id": r.user_id, "action": r.action,
         "detail": r.detail, "created_at": r.created_at.isoformat()}
        for r in rows
    ]
