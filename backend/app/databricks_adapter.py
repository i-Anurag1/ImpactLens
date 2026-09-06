"""Databricks historical-test evidence with an honest offline fallback.

The pipeline always calls this adapter. A configured warehouse is queried
from ``impactlens_history``; a failed or unavailable connection returns the
bundled fixture and records that fallback in response provenance.
"""
from collections import defaultdict
import os
from typing import Dict, List

from dotenv import load_dotenv

from . import demo_data as D
from .schemas import HistoricalFailure

load_dotenv()

_runtime = {
    "source": "Bundled demo history (fallback)",
    "live": False,
    "reason": "Databricks live mode is disabled.",
}


def _real_mode() -> bool:
    return os.getenv("USE_REAL_DATABRICKS", "false").lower() == "true"


def _history_table() -> str:
    # Kept configurable for catalog/schema-qualified production deployments.
    return os.getenv("DATABRICKS_HISTORY_TABLE", "impactlens_history")


def _connection():
    from databricks import sql

    host = os.getenv("DATABRICKS_HOST", "").replace("https://", "").rstrip("/")
    http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
    token = os.getenv("DATABRICKS_TOKEN", "")
    if not host or not http_path or not token:
        raise RuntimeError("Databricks configuration is incomplete")
    return sql.connect(server_hostname=host, http_path=http_path, access_token=token)


def _mark_live() -> None:
    _runtime.update({
        "source": f"Databricks: {_history_table()}",
        "live": True,
        "reason": "Live historical evidence queried from Databricks.",
    })


def _mark_fallback(reason: str) -> None:
    _runtime.update({
        "source": "Bundled demo history (fallback)",
        "live": False,
        "reason": reason,
    })


def evidence_metadata() -> dict:
    return dict(_runtime)


def _demo_failures(symbol: str | None = None) -> List[HistoricalFailure]:
    rows = D.HISTORICAL_TEST_RUNS
    if symbol:
        rows = [row for row in rows if row["symbol"] == symbol]
    return [
        HistoricalFailure(
            commit_sha=row["commit_sha"], symbol=row["symbol"],
            test_name=row["test_name"], outcome=row["outcome"],
            failure_message=row.get("failure_message"), occurred_at=row["occurred_at"],
            seeded_demo_data=True,
        )
        for row in rows
    ]


def _demo_test_rates(symbol: str | None) -> Dict[str, float]:
    rows = [row for row in D.HISTORICAL_TEST_RUNS if row["symbol"] == symbol]
    counts = defaultdict(lambda: [0, 0])
    for row in rows:
        counts[row["test_name"]][1] += 1
        if row["outcome"] == "fail":
            counts[row["test_name"]][0] += 1
    return {name: fails / total if total else 0.0 for name, (fails, total) in counts.items()}


def _fallback_reason() -> str:
    if not _real_mode():
        return "Databricks live mode is disabled; bundled demo history is in use."
    return "Databricks was unavailable; bundled demo history is in use."


def get_historical_failures(symbol: str | None = None) -> List[HistoricalFailure]:
    if not _real_mode():
        _mark_fallback(_fallback_reason())
        return _demo_failures(symbol)
    try:
        query = (
            f"SELECT symbol, test_name, runs, failures, failure_rate, last_result "
            f"FROM {_history_table()}"
        )
        params = ()
        if symbol:
            query += " WHERE symbol = ?"
            params = (symbol,)
        query += " ORDER BY failure_rate DESC"
        with _connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
        _mark_live()
        return [
            HistoricalFailure(
                commit_sha="databricks-history", symbol=row[0], test_name=row[1],
                outcome="fail" if str(row[5]).upper() == "FAILED" else "pass",
                failure_message=None, occurred_at=None, seeded_demo_data=False,
            )
            for row in rows
        ]
    except Exception:
        _mark_fallback(_fallback_reason())
        return _demo_failures(symbol)


def get_test_failure_rate(symbol: str | None = None) -> Dict[str, float]:
    if not _real_mode():
        _mark_fallback(_fallback_reason())
        return _demo_test_rates(symbol)
    try:
        with _connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT test_name, failure_rate FROM {_history_table()} "
                    "WHERE symbol = ? ORDER BY failure_rate DESC",
                    (symbol,),
                )
                rows = cursor.fetchall()
        _mark_live()
        return {test_name: float(rate or 0.0) for test_name, rate in rows}
    except Exception:
        _mark_fallback(_fallback_reason())
        return _demo_test_rates(symbol)


def get_symbol_failure_rate(symbol: str) -> float:
    if not _real_mode():
        _mark_fallback(_fallback_reason())
        runs = [row for row in D.HISTORICAL_TEST_RUNS if row["symbol"] == symbol]
        return round(sum(row["outcome"] == "fail" for row in runs) / len(runs), 2) if runs else 0.0
    try:
        with _connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT COALESCE(SUM(failures), 0), COALESCE(SUM(runs), 0) "
                    f"FROM {_history_table()} WHERE symbol = ?", (symbol,),
                )
                failures, runs = cursor.fetchone()
        _mark_live()
        return round(float(failures) / float(runs), 2) if runs else 0.0
    except Exception:
        _mark_fallback(_fallback_reason())
        runs = [row for row in D.HISTORICAL_TEST_RUNS if row["symbol"] == symbol]
        return round(sum(row["outcome"] == "fail" for row in runs) / len(runs), 2) if runs else 0.0


def rank_boost_from_history(test_name: str, symbol: str) -> float:
    rate = get_test_failure_rate(symbol).get(test_name)
    if rate is None:
        return 0.0
    return min(0.25, 0.15 + rate * 0.10) if rate > 0 else 0.05


def seed_disclaimer() -> str:
    return evidence_metadata()["reason"]
