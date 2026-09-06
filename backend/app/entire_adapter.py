"""The boundary between ImpactLens and Entire Graph.

Entire is evidence, not an oracle.  When the local CLI is unavailable the
bundled demo relationship fixture remains usable, but it is explicitly marked
PARTIAL and is never represented as a live Entire result.
"""
from collections import defaultdict
import json
import shutil
import subprocess
from typing import List, Optional

from . import demo_data as D
from .config import settings
from .schemas import Checkpoint, EvidenceStatus, GraphEdge, GraphQueryResult, SymbolRef

LIMITATIONS_STATIC = [
    "Bundled demo relationship fixture is active because no live Entire Graph result was returned.",
    "Static relationships can miss dynamic dispatch, reflection, generated code, and string-built call sites.",
    "The unresolved dynamic-pricing fixture below must be checked in source and at runtime.",
]

VERIFICATION_STEPS = [
    "Inspect the changed source and the shown file:line callers/callees.",
    "Run the ranked tests, including the indirect inventory test.",
    "Exercise currency rounding and the dynamic pricing path in a runtime environment.",
]


def _symbol_ref(name: str) -> SymbolRef:
    meta = D.SYMBOLS[name]
    return SymbolRef(symbol=name, file=meta["file"], line=meta["line"], kind=meta["kind"])


def is_real_cli_available() -> bool:
    return bool(settings.USE_REAL_ENTIRE_CLI and shutil.which(settings.ENTIRE_CLI_PATH))


def graph_status() -> dict:
    if is_real_cli_available():
        return {"mode": "live", "available": True, "source": "Entire Graph CLI"}
    if settings.USE_REAL_ENTIRE_CLI:
        return {"mode": "unavailable", "available": False, "source": "Entire Graph CLI not found"}
    return {"mode": "demo_fixture", "available": False, "source": "Bundled demo graph fixture"}


def checkpoint_status() -> dict:
    if is_real_cli_available():
        return {"available": True, "note": "Live Entire checkpoint retrieval is enabled."}
    return {
        "available": False,
        "note": "No valid Entire checkpoint can be shown because the Entire CLI is unavailable in this environment.",
    }


def _run_real_cli(args: List[str]) -> dict:
    cmd = [settings.ENTIRE_CLI_PATH, *args, "--format", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "Entire CLI returned a non-zero status")
    return json.loads(proc.stdout)


def _from_real(data: dict, query_type: str, query: str) -> GraphQueryResult:
    # Entire's JSON response must already carry the returned nodes/edges.  We
    # add only safety metadata; we do not invent missing relationships.
    result = GraphQueryResult(**data)
    result.query_type = result.query_type or query_type
    result.query = result.query or query
    if not result.is_complete or result.confidence < 0.85 or result.limitations:
        result.evidence_status = EvidenceStatus.PARTIAL
        result.verification_steps = result.verification_steps or VERIFICATION_STEPS
    else:
        result.evidence_status = EvidenceStatus.CONFIRMED
    result.source = result.source or "Entire Graph CLI"
    return result


def _unavailable(query_type: str, query: str, reason: str) -> GraphQueryResult:
    return GraphQueryResult(
        query_type=query_type, query=query, nodes=[], edges=[], confidence=0.0,
        heuristic=False, source="Entire Graph unavailable", limitations=[reason],
        evidence_status=EvidenceStatus.VERIFY_REQUIRED, is_complete=False,
        verification_steps=VERIFICATION_STEPS,
    )


def _adjacency():
    adj = defaultdict(list)
    for edge in D.CALL_EDGES:
        adj[edge[0]].append(edge)
        adj[edge[1]].append(edge)
    return adj


def impact(
    symbol: str, repo_path: Optional[str] = None, max_hops: int = 2,
    use_demo_fixture: bool = False,
) -> GraphQueryResult:
    if settings.USE_REAL_ENTIRE_CLI and not use_demo_fixture:
        if not is_real_cli_available():
            return _unavailable("impact", symbol, "Entire CLI executable was not found on PATH.")
        try:
            return _from_real(
                _run_real_cli(["graph", "impact", "--symbol", symbol, "--repo", repo_path or "."]),
                "impact", symbol,
            )
        except Exception as exc:
            return _unavailable("impact", symbol, f"Entire Graph impact query failed: {type(exc).__name__}.")

    adj = _adjacency()
    nodes, seen_edges, edges, frontier = {symbol}, set(), [], {symbol}
    for _ in range(max_hops):
        next_frontier = set()
        for node in frontier:
            for src, tgt, relation, confidence, note in adj.get(node, []):
                key = (src, tgt, relation)
                if key not in seen_edges:
                    seen_edges.add(key)
                    edges.append(GraphEdge(
                        source=_symbol_ref(src), target=_symbol_ref(tgt), relation=relation,
                        confidence=confidence, evidence_note=note,
                    ))
                other = tgt if src == node else src
                if other not in nodes:
                    nodes.add(other)
                    next_frontier.add(other)
        frontier = next_frontier
        if not frontier:
            break
    confidence = round(sum(edge.confidence for edge in edges) / len(edges), 2) if edges else 0.0
    return GraphQueryResult(
        query_type="impact", query=symbol, nodes=[_symbol_ref(node) for node in nodes], edges=edges,
        confidence=confidence, heuristic=True, source="Bundled demo graph fixture (not live Entire CLI)",
        limitations=LIMITATIONS_STATIC, evidence_status=EvidenceStatus.PARTIAL,
        is_complete=False, verification_steps=VERIFICATION_STEPS,
    )


def neighbors(symbol: str) -> GraphQueryResult:
    result = impact(symbol, max_hops=1)
    result.query_type = "neighbors"
    return result


def diff(base_sha: str, head_sha: str, use_demo_fixture: bool = False) -> GraphQueryResult:
    query = f"{base_sha}..{head_sha}"
    if settings.USE_REAL_ENTIRE_CLI and not use_demo_fixture:
        if not is_real_cli_available():
            return _unavailable("diff", query, "Entire CLI executable was not found on PATH.")
        try:
            return _from_real(_run_real_cli(["graph", "diff", "--base", base_sha, "--head", head_sha, "--repo", "."]), "diff", query)
        except Exception as exc:
            return _unavailable("diff", query, f"Entire Graph diff query failed: {type(exc).__name__}.")
    changed = [symbol for file_change in D.CHANGED_FILES for symbol in file_change["changed_symbols"]]
    return GraphQueryResult(
        query_type="diff", query=query, nodes=[_symbol_ref(symbol) for symbol in changed], edges=[],
        confidence=0.0, heuristic=True, source="Bundled demo diff fixture (not live Entire CLI)",
        limitations=["Changed-symbol data is bundled demo input, not an Entire semantic diff result."],
        evidence_status=EvidenceStatus.PARTIAL, is_complete=False, verification_steps=VERIFICATION_STEPS,
    )


def co_change(file_path: str) -> List[dict]:
    return [
        {"file": b if a == file_path else a, "frequency": frequency, "note": note}
        for a, b, frequency, note in D.CO_CHANGE_EDGES if a == file_path or b == file_path
    ]


def snapshot(repo_full_name: str) -> dict:
    status = graph_status()
    return {
        "repository": repo_full_name, "symbol_count": len(D.SYMBOLS), "edge_count": len(D.CALL_EDGES),
        "last_indexed_at": "Not live-indexed", "source": status["source"],
        "evidence_status": "PARTIAL" if not status["available"] else "CONFIRMED",
    }


def checkpoints_for_commit(commit_sha: str) -> List[Checkpoint]:
    # Do not surface fabricated IDs.  A compatible real parser can be added
    # after the installed CLI's checkpoint JSON contract is verified.
    return []


def all_checkpoints() -> List[Checkpoint]:
    return []
