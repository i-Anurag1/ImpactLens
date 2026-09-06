"""
Deterministic risk engine.

This is the product's source of truth for "how risky is this change" — it
is pure arithmetic over graph + historical evidence. No LLM call happens
anywhere in this file. The AI layer (ai_explain.py) is only ever handed
this module's output to summarize in prose; it cannot change the score.
"""
from typing import List

from . import demo_data as D
from . import databricks_adapter as db
from .schemas import (
    ChangedFile, EvidenceStatus, GraphQueryResult, RiskFactor, RiskResult, RiskLevel,
)

# Weights sum to 100 -> score is directly in points out of 100.
WEIGHTS = {
    "change_size": 10,
    "dependency_depth": 20,
    "consumer_count": 20,
    "public_api_exposure": 15,
    "test_coverage_gap": 15,
    "historical_failure_rate": 15,
    "graph_confidence_penalty": 5,
}

THRESHOLDS = [
    (25, RiskLevel.LOW),
    (50, RiskLevel.MEDIUM),
    (75, RiskLevel.HIGH),
    (101, RiskLevel.CRITICAL),
]


def _level_for(score: int) -> RiskLevel:
    for ceiling, level in THRESHOLDS:
        if score < ceiling:
            return level
    return RiskLevel.CRITICAL


def compute_risk(
    changed_files: List[ChangedFile],
    impact_result: GraphQueryResult,
) -> RiskResult:
    factors: List[RiskFactor] = []
    changed_symbols = [s for cf in changed_files for s in cf.changed_symbols]

    # 1. Change size: normalized total diff size (caps out around 150 lines)
    total_lines = sum(cf.additions + cf.deletions for cf in changed_files)
    change_size_norm = min(1.0, total_lines / 150)
    factors.append(_factor(
        "change_size", "Change size", change_size_norm, WEIGHTS["change_size"],
        f"{total_lines} lines changed across {len(changed_files)} file(s).",
    ))

    partial = impact_result.evidence_status != EvidenceStatus.CONFIRMED or not impact_result.is_complete

    # 2. Dependency depth: longest hop distance from any changed symbol to
    # anything else reachable in the traced graph (BFS over the union of
    # edges), which is what actually catches multi-hop hidden dependencies
    # rather than just counting edges that touch the changed symbol.
    max_depth = _max_hop_distance(changed_symbols, impact_result.edges)
    depth_norm = min(1.0, max_depth / 3)
    factors.append(_factor(
        "dependency_depth", "Dependency depth", depth_norm, WEIGHTS["dependency_depth"],
        f"{'Possible' if partial else 'Confirmed'} deepest traced call chain from a changed symbol spans {max_depth} edge(s), "
        f"including at least one indirect (multi-hop) dependency."
        if max_depth >= 3 else f"Call chain depth: {max_depth} edge(s).",
    ))

    # 3. Consumer count: distinct callers/consumers touched, direct + hidden
    consumers = {e.source.symbol for e in impact_result.edges if e.source.symbol not in changed_symbols}
    confirmed_consumers = {
        e.source.symbol for e in impact_result.edges
        if e.source.symbol not in changed_symbols and e.confidence >= 0.85
    }
    consumer_norm = min(1.0, len(consumers) / 4)
    factors.append(_factor(
        "consumer_count", "Affected consumers", consumer_norm, WEIGHTS["consumer_count"],
        f"{len(confirmed_consumers)} confirmed and {len(consumers) - len(confirmed_consumers)} "
        f"partial/potential consumer(s) reach the changed code. "
        f"Potential consumers increase caution but require verification.",
    ))

    # 4. Public API exposure
    touches_public = any(
        e.source.symbol in D.PUBLIC_API_SYMBOLS or e.target.symbol in D.PUBLIC_API_SYMBOLS
        for e in impact_result.edges
    ) or any(s in D.PUBLIC_API_SYMBOLS for s in changed_symbols)
    factors.append(_factor(
        "public_api_exposure", "Public API exposure", 1.0 if touches_public else 0.0,
        WEIGHTS["public_api_exposure"],
        "Change reaches a public-facing route/API." if touches_public
        else "No public API route reached in the traced blast radius.",
    ))

    # 5. Test coverage gap: fraction of impacted symbols with NO direct test
    impacted_symbols = set(changed_symbols) | consumers
    covered = sum(1 for s in impacted_symbols if D.TEST_COVERAGE.get(s))
    coverage_gap = 1.0 - (covered / len(impacted_symbols)) if impacted_symbols else 0.0
    factors.append(_factor(
        "test_coverage_gap", "Test coverage gap", coverage_gap, WEIGHTS["test_coverage_gap"],
        f"{covered}/{len(impacted_symbols)} impacted symbol(s) have a direct test.",
    ))

    # 6. Historical failure rate across impacted symbols (Databricks)
    fail_rates = [db.get_symbol_failure_rate(s) for s in impacted_symbols] or [0.0]
    avg_fail_rate = sum(fail_rates) / len(fail_rates)
    factors.append(_factor(
        "historical_failure_rate", "Historical failure rate", avg_fail_rate,
        WEIGHTS["historical_failure_rate"],
        f"Average historical failure rate across impacted symbols: {avg_fail_rate:.0%}. "
        f"Source: {db.seed_disclaimer()}",
    ))

    # 7. Graph confidence penalty: lower confidence => added uncertainty risk
    conf_penalty_norm = 1.0 - impact_result.confidence
    factors.append(_factor(
        "graph_confidence_penalty", "Graph uncertainty", conf_penalty_norm,
        WEIGHTS["graph_confidence_penalty"],
        f"Graph confidence for this impact query: {impact_result.confidence:.0%}. "
        f"Status: {impact_result.evidence_status.value}. Lower confidence adds an uncertainty margin, "
        f"not a claim of confirmed impact.",
    ))

    score = round(sum(f.contribution for f in factors))
    score = max(0, min(100, score))
    level = _level_for(score)

    rationale = _build_rationale(level, factors, max_depth, touches_public, len(consumers))

    return RiskResult(
        score=score, level=level, factors=factors, rationale=rationale,
        graph_confidence=impact_result.confidence,
        evidence_status=(EvidenceStatus.VERIFY_REQUIRED if impact_result.evidence_status == EvidenceStatus.VERIFY_REQUIRED else (EvidenceStatus.PARTIAL if partial else EvidenceStatus.CONFIRMED)),
        verification_required=partial,
    )


def _max_hop_distance(sources: List[str], edges) -> int:
    """BFS multi-source shortest-hop distance from `sources` to every other
    node reachable through `edges` (treated as undirected for reachability),
    returning the max distance found."""
    from collections import deque
    adj = {}
    for e in edges:
        adj.setdefault(e.source.symbol, set()).add(e.target.symbol)
        adj.setdefault(e.target.symbol, set()).add(e.source.symbol)

    visited = {s: 0 for s in sources}
    q = deque(sources)
    max_dist = 0
    while q:
        node = q.popleft()
        for nxt in adj.get(node, ()):
            if nxt not in visited:
                visited[nxt] = visited[node] + 1
                max_dist = max(max_dist, visited[nxt])
                q.append(nxt)
    return max_dist


def _factor(key, label, value, weight, detail) -> RiskFactor:
    return RiskFactor(
        key=key, label=label, value=round(value, 2), weight=weight,
        contribution=round(value * weight, 1), detail=detail,
    )


def _build_rationale(level, factors, max_depth, touches_public, consumer_count) -> List[str]:
    lines = [f"Overall risk classified as {level.value}."]
    top = sorted(factors, key=lambda f: f.contribution, reverse=True)[:3]
    for f in top:
        if f.contribution > 0:
            lines.append(f"{f.label} contributed {f.contribution} points — {f.detail}")
    if max_depth >= 3:
        lines.append(
            "A multi-hop, low-visibility dependency was found that a line-diff "
            "review would not surface — see Dependency Graph for the exact path."
        )
    if touches_public:
        lines.append("This change is reachable from a public API route.")
    return lines
