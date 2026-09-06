from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db, Repository, Membership, User
from ..auth import get_current_user, get_repository_membership
from .. import entire_adapter
from .. import demo_data as D

router = APIRouter(prefix="/api/repos", tags=["repos"])


@router.get("")
def list_repos(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    out = []
    for m in memberships:
        repo = db.query(Repository).filter(Repository.id == m.repository_id).first()
        out.append({
            "id": repo.id, "full_name": repo.full_name,
            "default_branch": repo.default_branch, "is_demo": repo.is_demo,
            "role": get_repository_membership(repo.id, user, db).role,
        })
    return out


@router.get("/{repo_id}/overview")
def repo_overview(repo_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    repo = _authorized_repo(repo_id, user, db)
    snap = entire_adapter.snapshot(repo.full_name)
    return {
        "repository": {
            "id": repo.id, "full_name": repo.full_name,
            "default_branch": repo.default_branch, "is_demo": repo.is_demo,
        },
        "graph_snapshot": snap,
        "demo_commit": D.DEMO_COMMIT if repo.is_demo else None,
        "changed_files_available": D.CHANGED_FILES if repo.is_demo else [],
    }


def _authorized_repo(repo_id: str, user: User, db: Session) -> Repository:
    get_repository_membership(repo_id, user, db)
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo
