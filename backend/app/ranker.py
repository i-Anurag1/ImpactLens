"""
Ranks which tests to run, with a full evidence chain per recommendation
(e.g. PaymentService.processPayment -> CheckoutService.checkout ->
CheckoutServiceTest.test_checkout_success). Deterministic: relevance_score
is graph distance + historical failure signal, nothing invented.
"""
from typing import List

from . import demo_data as D
from . import databricks_adapter as db
from .schemas import EvidenceStatus, GraphQueryResult, EvidenceStep, SymbolRef, TestRecommendation


def _symbol_ref(name: str) -> SymbolRef:
    meta = D.SYMBOLS[name]
    return SymbolRef(symbol=name, file=meta["file"], line=meta["line"], kind=meta["kind"])


def _chain_to(symbol: str, impact_result: GraphQueryResult) -> List[EvidenceStep]:
    """Walk edges backward from `symbol` toward the changed root, building a
    human-readable evidence chain."""
    edge_by_target = {e.target.symbol: e for e in impact_result.edges}
    chain: List[EvidenceStep] = []
    current = symbol
    seen = set()
    while current in edge_by_target and current not in seen:
        seen.add(current)
        edge = edge_by_target[current]
        chain.append(EvidenceStep(symbol=edge.source, relation_to_next=edge.relation))
        current = edge.source.symbol
    chain.append(EvidenceStep(symbol=_symbol_ref(current), relation_to_next=None))
    chain.reverse()
    return chain


def recommend_tests(impact_result: GraphQueryResult, top_n: int = 4) -> List[TestRecommendation]:
    impacted_symbols = {n.symbol for n in impact_result.nodes}
    candidates = []

    for symbol in impacted_symbols:
        tests = D.TEST_COVERAGE.get(symbol, [])
        # distance: 0 for the changed symbol's own test, else hop count from impact edges
        hop_count = sum(
            1 for e in impact_result.edges
            if e.source.symbol == symbol or e.target.symbol == symbol
        )
        is_hidden = any(
            e.target.symbol == symbol and e.confidence < 0.85
            for e in impact_result.edges
        )
        for test_name in tests:
            meta = D.SYMBOLS[test_name]
            base_relevance = max(0.3, 1.0 - hop_count * 0.15)
            boost = db.rank_boost_from_history(test_name, symbol)
            relevance = min(1.0, round(base_relevance + boost, 2))
            if impact_result.evidence_status != EvidenceStatus.CONFIRMED:
                # Ranking stays useful, but partial graph evidence must never
                # masquerade as a fully certain recommendation.
                relevance = min(relevance, 0.85)
            fail_rate = db.get_test_failure_rate(symbol).get(test_name)

            reason = _build_reason(
                symbol, test_name, is_hidden, fail_rate, hop_count,
                impact_result.evidence_status,
            )

            candidates.append(TestRecommendation(
                test_name=test_name, file=meta["file"], line=meta["line"],
                priority_rank=0,  # assigned after sort
                relevance_score=relevance,
                reason=reason,
                evidence_chain=_chain_to(symbol, impact_result),
                historical_failure_rate=fail_rate,
                is_hidden_dependency=is_hidden,
                affected_symbol=symbol,
                evidence_source=impact_result.source,
                evidence_status=impact_result.evidence_status,
                verification_required=impact_result.evidence_status != EvidenceStatus.CONFIRMED,
            ))

    # de-dupe by test_name keeping the highest-relevance instance
    best_by_test = {}
    for c in candidates:
        if c.test_name not in best_by_test or c.relevance_score > best_by_test[c.test_name].relevance_score:
            best_by_test[c.test_name] = c

    ranked = sorted(best_by_test.values(), key=lambda c: c.relevance_score, reverse=True)[:top_n]
    for i, r in enumerate(ranked, start=1):
        r.priority_rank = i
    return ranked


def _build_reason(symbol, test_name, is_hidden, fail_rate, hop_count, evidence_status) -> str:
    parts = []
    if hop_count == 0:
        parts.append(f"Directly covers the changed symbol {symbol}.")
    else:
        parts.append(f"Covers {symbol}, reachable within {hop_count} hop(s) of the change.")
    if is_hidden:
        parts.append("Reaches the change only through a hidden/indirect dependency — "
                      "easy to miss without graph evidence.")
    if fail_rate:
        parts.append(f"Historically failed {fail_rate:.0%} of the time for this symbol.")
    if evidence_status != EvidenceStatus.CONFIRMED:
        parts.append("Graph evidence is partial; inspect the chain and verify this test against runtime behavior.")
    return " ".join(parts)
