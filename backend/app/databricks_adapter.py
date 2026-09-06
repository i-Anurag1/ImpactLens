"""
Adapter over the Databricks historical-engineering-intelligence layer.

Data model (as Delta tables in real mode, Unity-Catalog-governed):
  repositories(repo_id, full_name, default_branch)
  commits(commit_sha, repo_id, author, message, created_at)
  changed_symbols(commit_sha, symbol, file, line)
  graph_edges(commit_sha, source_symbol, target_symbol, relation, confidence)
  test_executions(commit_sha, test_name, symbol, outcome, duration_ms, ran_at)
  test_failures(commit_sha, test_name, symbol, failure_message, occurred_at)
  impact_reports(analysis_id, repo_id, commit_sha, risk_score, risk_level, created_at)
  recommendations(analysis_id, test_name, priority_rank, relevance_score)
  outcomes(analysis_id, test_name, predicted_relevant, actually_failed)

REAL MODE (USE_REAL_DATABRICKS=true): each function below issues Databricks
SQL against DATABRICKS_HOST/HTTP_PATH using the `databricks-sql-connector`,
e.g.
    SELECT test_name, COUNT_IF(outcome='fail') / COUNT(*) AS failure_rate
    FROM test_executions WHERE symbol = %(symbol)s
    GROUP BY test_name
and a lightweight ranking model (e.g. logistic regression over
[graph_confidence, historical_failure_rate, co_change_frequency, hops]
trained on the `outcomes` table) improves `relevance_score` over time.

MOCK MODE (default): seeded, clearly-labeled demo history from
demo_data.py, with the same query shapes a real warehouse would answer.
"""
from collections import defaultdict
from typing import Dict, List

from . import demo_data as D
from .schemas import HistoricalFailure


def get_historical_failures(symbol: str = None) -> List[HistoricalFailure]:
    rows = D.HISTORICAL_TEST_RUNS
    if symbol:
        rows = [r for r in rows if r["symbol"] == symbol]
    return [
        HistoricalFailure(
            commit_sha=r["commit_sha"], symbol=r["symbol"], test_name=r["test_name"],
            outcome=r["outcome"], failure_message=r.get("failure_message"),
            occurred_at=r["occurred_at"], seeded_demo_data=True,
        )
        for r in rows
    ]


def get_test_failure_rate(symbol: str) -> Dict[str, float]:
    """failure_rate per test_name for a given symbol, from seeded history."""
    runs = [r for r in D.HISTORICAL_TEST_RUNS if r["symbol"] == symbol]
    counts = defaultdict(lambda: [0, 0])  # test_name -> [fails, total]
    for r in runs:
        counts[r["test_name"]][1] += 1
        if r["outcome"] == "fail":
            counts[r["test_name"]][0] += 1
    return {name: (fails / total if total else 0.0) for name, (fails, total) in counts.items()}


def get_symbol_failure_rate(symbol: str) -> float:
    """Aggregate historical failure rate across all tests touching this symbol —
    one of the deterministic risk-engine inputs."""
    runs = [r for r in D.HISTORICAL_TEST_RUNS if r["symbol"] == symbol]
    if not runs:
        return 0.0
    fails = sum(1 for r in runs if r["outcome"] == "fail")
    return round(fails / len(runs), 2)


def rank_boost_from_history(test_name: str, symbol: str) -> float:
    """
    Stand-in for the 'lightweight ML/ranking layer from historical data'.
    In real mode this would be a trained model reading the `outcomes` table;
    here it's a transparent, auditable rule: tests that have actually failed
    for this symbol before get a visible relevance boost, tests with only
    passing history get a small boost, tests with zero history get none.
    """
    rates = get_test_failure_rate(symbol)
    rate = rates.get(test_name)
    if rate is None:
        return 0.0
    if rate > 0:
        return min(0.25, 0.15 + rate * 0.10)
    return 0.05


def seed_disclaimer() -> str:
    return (
        "Historical test-run data below is seeded demo data for this "
        "hackathon build, not real production history. In production this "
        "table is populated by ingesting CI test results into Delta tables "
        "on every run."
    )
