from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db, User
from ..auth import get_current_user
from .. import entire_adapter
from .repos import _authorized_repo

router = APIRouter(prefix="/api/repos", tags=["checkpoints"])


@router.get("/{repo_id}/checkpoints")
def list_checkpoints(repo_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Entire CLI checkpoint/session timeline: what changed, why, and which
    (human or AI agent) session produced it. Real mode: `entire checkpoint
    list --repo <path> --format json`, joined with `entire session
    explain`/`entire blame`/`entire why` for the prompt/session context.
    """
    _authorized_repo(repo_id, user, db)
    return entire_adapter.all_checkpoints()
