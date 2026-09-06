import json
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db, Analysis, User, AuditLog, gen_id
from ..auth import get_current_user
from .. import entire_adapter, risk_engine, ranker, ai_explain, databricks_adapter as dbx
from .. import demo_data as D
from ..schemas import (
    ChangedFile, AnalysisResult, HistoricalFailure,
)
from .repos import _authorized_repo

router = APIRouter(prefix="/api/repos", tags=["analyze"])

# --- naive in-memory rate limiter (per user) -----------------------------
_rate_bucket = defaultdict(list)
RATE_LIMIT_PER_MIN = 30


def _check_rate_limit(user_id: str):
    now = time.time()
    bucket = _rate_bucket[user_id]
    _rate_bucket[user_id] = [t for t in bucket if now - t < 60]
    if len(_rate_bucket[user_id]) >= RATE_LIMIT_PER_MIN:
        raise HTTPException(status_code=429, detail="Rate limit exceeded, try again shortly")
    _rate_bucket[user_id].append(now)


# --- simple in-memory analysis cache, keyed by (repo_id, base, head) -----
_analysis_cache = {}


@router.post("/{repo_id}/analyze")
def analyze_change(
    repo_id: str,
    ref_label: str = "PR: Fix currency rounding in processPayment",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_rate_limit(user.id)
    repo = _authorized_repo(repo_id, user, db)

    if not repo.is_demo:
        raise HTTPException(
            status_code=400,
            detail="Only the bundled demo repository is analyzable in this build. "
                   "Real-repo analysis needs GITHUB_CLIENT_ID/SECRET and a checked-out "
                   "repo path for the Entire CLI (see config.py).",
        )

    base_sha, head_sha = D.DEMO_COMMIT["base_sha"], D.DEMO_COMMIT["head_sha"]
    cache_key = (repo_id, base_sha, head_sha)
    if cache_key in _analysis_cache:
        result = _analysis_cache[cache_key]
        db.add(AuditLog(id=gen_id(), user_id=user.id, action="analyze_cache_hit",
                         detail=f"repo={repo.full_name} {base_sha}..{head_sha}"))
        db.commit()
        return result

    result = _run_pipeline(repo.full_name, ref_label, base_sha, head_sha)
    _analysis_cache[cache_key] = result

    record = Analysis(
        id=result.analysis_id, repository_id=repo_id, requested_by=user.id,
        ref_label=ref_label, base_sha=base_sha, head_sha=head_sha,
        status="completed", risk_level=result.risk.level.value, risk_score=result.risk.score,
        result_json=result.model_dump_json(),
    )
    db.add(record)
    db.add(AuditLog(id=gen_id(), user_id=user.id, action="analyze_run",
                     detail=f"repo={repo.full_name} {base_sha}..{head_sha} risk={result.risk.level.value}"))
    db.commit()

    return result


@router.get("/{repo_id}/analyses")
def list_analyses(repo_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _authorized_repo(repo_id, user, db)
    rows = db.query(Analysis).filter(Analysis.repository_id == repo_id) \
        .order_by(Analysis.created_at.desc()).all()
    return [
        {
            "id": r.id, "ref_label": r.ref_label, "risk_level": r.risk_level,
            "risk_score": r.risk_score, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get("/{repo_id}/analyses/{analysis_id}")
def get_analysis(repo_id: str, analysis_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _authorized_repo(repo_id, user, db)
    row = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.repository_id == repo_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return json.loads(row.result_json)


def _run_pipeline(repo_full_name: str, ref_label: str, base_sha: str, head_sha: str) -> AnalysisResult:
    """The core 'What will this change break?' pipeline. Pure orchestration —
    all real logic lives in entire_adapter / risk_engine / ranker /
    databricks_adapter / ai_explain."""
    changed_files = [ChangedFile(**cf) for cf in D.CHANGED_FILES]
    changed_symbols = [s for cf in changed_files for s in cf.changed_symbols]

    diff_result = entire_adapter.diff(base_sha, head_sha)

    # Union impact across every changed symbol into one graph query result
    impact_nodes, impact_edges, confidences = {}, [], []
    for sym in changed_symbols:
        r = entire_adapter.impact(sym)
        for n in r.nodes:
            impact_nodes[n.symbol] = n
        impact_edges.extend(r.edges)
        confidences.append(r.confidence)
    from ..schemas import GraphQueryResult
    impact_result = GraphQueryResult(
        query_type="impact", query=",".join(changed_symbols),
        nodes=list(impact_nodes.values()), edges=impact_edges,
        confidence=round(sum(confidences) / len(confidences), 2) if confidences else 0.5,
        heuristic=True, source="entire-graph (mock adapter)",
        limitations=entire_adapter.LIMITATIONS_STATIC,
    )

    risk = risk_engine.compute_risk(changed_files, impact_result)
    tests = ranker.recommend_tests(impact_result, top_n=4)

    historical: list[HistoricalFailure] = []
    for sym in impact_result.nodes:
        historical.extend(dbx.get_historical_failures(sym.symbol))

    checkpoints = entire_adapter.checkpoints_for_commit(head_sha)
    explanation = ai_explain.explain(risk, tests, impact_result, changed_symbols)

    return AnalysisResult(
        analysis_id=gen_id(),
        repository=repo_full_name,
        ref_label=ref_label,
        base_sha=base_sha, head_sha=head_sha,
        changed_files=changed_files,
        graph_queries=[diff_result, impact_result],
        risk=risk,
        test_recommendations=tests,
        historical_failures=historical,
        checkpoints=checkpoints,
        ai_explanation=explanation,
        provenance={
            "entire_graph_source": impact_result.source,
            "entire_graph_heuristic": impact_result.heuristic,
            "databricks_note": dbx.seed_disclaimer(),
            "risk_engine": "deterministic, see risk_engine.py",
            "ai_layer": explanation.generated_by,
        },
    )
