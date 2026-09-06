from dotenv import load_dotenv
load_dotenv()
import os
from collections import defaultdict
from typing import Dict, List

from . import demo_data as D
from .schemas import HistoricalFailure


def _real_mode() -> bool:
    return os.getenv("USE_REAL_DATABRICKS", "false").lower() == "true"


def _connection():
    from databricks import sql

    host = os.getenv("DATABRICKS_HOST", "").replace("https://", "").rstrip("/")
    http_path = os.getenv("DATABRICKS_HTTP_PATH", "")
    token = os.getenv("DATABRICKS_TOKEN", "")

    if not host or not http_path or not token:
        raise RuntimeError(
            "Databricks configuration missing: "
            "DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN"
        )

    return sql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token,
    )


def _history_table() -> str:
    # Change this only if your table is in another catalog/schema.
    return os.getenv(
        "DATABRICKS_HISTORY_TABLE",
        "workspace.default.impactlens_history",
    )


def get_historical_failures(symbol: str = None) -> List[HistoricalFailure]:
    if not _real_mode():
        rows = D.HISTORICAL_TEST_RUNS
        if symbol:
            rows = [r for r in rows if r["symbol"] == symbol]

        return [
            HistoricalFailure(
                commit_sha=r["commit_sha"],
                symbol=r["symbol"],
                test_name=r["test_name"],
                outcome=r["outcome"],
                failure_message=r.get("failure_message"),
                occurred_at=r["occurred_at"],
                seeded_demo_data=True,
            )
            for r in rows
        ]

    query = f"""
        SELECT symbol, test_name, runs, failures, failure_rate, last_result
        FROM {_history_table()}
    """

    params = ()
    if symbol:
        query += " WHERE symbol = ?"
        params = (symbol,)

    query += " ORDER BY failure_rate DESC"

    results = []

    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)

            for row in cursor.fetchall():
                db_symbol, test_name, runs, failures, failure_rate, last_result = row

                results.append(
                    HistoricalFailure(
                        commit_sha="databricks-history",
                        symbol=db_symbol,
                        test_name=test_name,
                        outcome=(
                            "fail"
                            if str(last_result).upper() == "FAILED"
                            else "pass"
                        ),
                        failure_message=None,
                        occurred_at=None,
                        seeded_demo_data=False,
                    )
                )

    return results


def get_test_failure_rate(symbol: str = None) -> Dict[str, float]:
    if not _real_mode():
        runs = [
            r for r in D.HISTORICAL_TEST_RUNS
            if r["symbol"] == symbol
        ]

        counts = defaultdict(lambda: [0, 0])

        for r in runs:
            counts[r["test_name"]][1] += 1
            if r["outcome"] == "fail":
                counts[r["test_name"]][0] += 1

        return {
            name: (fails / total if total else 0.0)
            for name, (fails, total) in counts.items()
        }

    query = f"""
        SELECT test_name, failure_rate
        FROM {_history_table()}
        WHERE symbol = ?
        ORDER BY failure_rate DESC
    """

    rates = {}

    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (symbol,))

            for test_name, failure_rate in cursor.fetchall():
                rates[test_name] = float(failure_rate or 0.0)

    return rates


def get_symbol_failure_rate(symbol: str) -> float:
    if not _real_mode():
        runs = [
            r for r in D.HISTORICAL_TEST_RUNS
            if r["symbol"] == symbol
        ]

        if not runs:
            return 0.0

        fails = sum(
            1 for r in runs
            if r["outcome"] == "fail"
        )

        return round(fails / len(runs), 2)

    query = f"""
        SELECT
            COALESCE(SUM(failures), 0),
            COALESCE(SUM(runs), 0)
        FROM {_history_table()}
        WHERE symbol = ?
    """

    with _connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (symbol,))
            failures, runs = cursor.fetchone()

    if not runs:
        return 0.0

    return round(float(failures) / float(runs), 2)


def rank_boost_from_history(test_name: str, symbol: str) -> float:
    rates = get_test_failure_rate(symbol)
    rate = rates.get(test_name)

    if rate is None:
        return 0.0

    if rate > 0:
        return min(0.25, 0.15 + rate * 0.10)

    return 0.05


def seed_disclaimer() -> str:
    if _real_mode():
        return (
            "Historical test-run data is queried from the configured "
            "Databricks Delta table."
        )

    return (
        "Historical test-run data below is seeded demo data for this "
        "hackathon build, not real production history."
    )