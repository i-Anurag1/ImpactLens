import json
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db, Analysis, User, Membership, AuditLog, gen_id
from ..auth import get_current_user, require_role
from .. import entire_adapter, risk_engine, ranker, ai_explain, databricks_adapter as dbx
from .. import demo_data as D
from ..schemas import (
    ChangedFile, EvidenceStatus, AnalysisResult, HistoricalFailure,
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
    membership: Membership = Depends(require_role("developer", "admin")),
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

    is_demo = repo_full_name == D.REPO_FULL_NAME
    diff_result = entire_adapter.diff(base_sha, head_sha, use_demo_fixture=is_demo)

    # Union impact across every changed symbol into one graph query result
    impact_nodes, impact_edges, confidences, impact_results = {}, [], [], []
    for sym in changed_symbols:
        r = entire_adapter.impact(sym, use_demo_fixture=is_demo)
        for n in r.nodes:
            impact_nodes[n.symbol] = n
        impact_edges.extend(r.edges)
        confidences.append(r.confidence)
        impact_results.append(r)
    from ..schemas import GraphQueryResult
    has_unavailable = any(r.evidence_status == EvidenceStatus.VERIFY_REQUIRED for r in impact_results)
    has_partial = any(r.evidence_status == EvidenceStatus.PARTIAL for r in impact_results)
    evidence_status = (
        EvidenceStatus.VERIFY_REQUIRED if has_unavailable
        else EvidenceStatus.PARTIAL if has_partial
        else EvidenceStatus.CONFIRMED
    )
    limitations = list(dict.fromkeys(
        limitation for result in impact_results for limitation in result.limitations
    ))
    verification_steps = list(dict.fromkeys(
        step for result in impact_results for step in result.verification_steps
    ))
    impact_result = GraphQueryResult(
        query_type="impact", query=",".join(changed_symbols),
        nodes=list(impact_nodes.values()), edges=impact_edges,
        confidence=round(sum(confidences) / len(confidences), 2) if confidences else 0.5,
        heuristic=any(result.heuristic for result in impact_results),
        source="; ".join(sorted({result.source for result in impact_results})),
        limitations=limitations,
        evidence_status=evidence_status,
        is_complete=bool(impact_results) and all(result.is_complete for result in impact_results),
        verification_steps=verification_steps,
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
            "entire_graph_status": impact_result.evidence_status.value,
            "entire_graph_complete": impact_result.is_complete,
            "databricks_source": dbx.evidence_metadata()["source"],
            "databricks_note": dbx.evidence_metadata()["reason"],
            "risk_engine": "deterministic, see risk_engine.py",
            "ai_layer": explanation.generated_by,
            "checkpoint_status": entire_adapter.checkpoint_status()["note"],
        },
        verification_plan=impact_result.verification_steps,
    )
