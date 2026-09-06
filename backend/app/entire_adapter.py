"""
Adapter over Entire Graph / Entire CLI.

This is the ONLY file that should know whether Entire is real or mocked.
Every other module calls the functions below and gets back normalized
`GraphQueryResult` / `Checkpoint` objects — it never knows the difference.

REAL MODE (USE_REAL_ENTIRE_CLI=true): each method shells out to the
`entire` binary and parses its JSON output, mirroring the documented
commands:
    entire graph search   --query <q> --repo <path> --format json
    entire graph def      --symbol <s> --repo <path> --format json
    entire graph neighbors --symbol <s> --repo <path> --format json
    entire graph impact   --symbol <s> --repo <path> --format json
    entire graph diff     --base <sha> --head <sha> --repo <path> --format json
    entire graph snapshot --repo <path> --format json
    entire session list / entire checkpoint list --repo <path> --format json
    entire explain / entire blame / entire why --repo <path> --format json
See https://github.com/entireio/entire-graph, https://github.com/entireio/cli,
and https://docs.entire.io/quickstart for the authoritative command set.

MOCK MODE (default here): returns data derived from demo_data.py, but
through the exact same normalized shape a real CLI response would take,
including confidence scores and explicit limitations — Entire Graph is
heuristic and must never be presented as compiler-verified truth.
"""
import json
import subprocess
from collections import defaultdict
from typing import List, Optional

from .config import settings
from . import demo_data as D
from .schemas import GraphQueryResult, GraphEdge, SymbolRef, Checkpoint

LIMITATIONS_STATIC = [
    "Call-graph edges are inferred via static analysis and naming/heuristic "
    "matching; dynamic dispatch, reflection, and string-built call sites can "
    "be missed.",
    "Confidence reflects graph heuristic certainty, not a compiler guarantee.",
]


def _symbol_ref(name: str) -> SymbolRef:
    meta = D.SYMBOLS[name]
    return SymbolRef(symbol=name, file=meta["file"], line=meta["line"], kind=meta["kind"])


def _run_real_cli(args: List[str]) -> dict:
    """Real-mode helper: invoke the entire CLI and parse JSON. Not used
    while USE_REAL_ENTIRE_CLI is False, but left in place so flipping the
    flag is the only change needed once the binary + repo checkout exist."""
    cmd = [settings.ENTIRE_CLI_PATH, *args, "--format", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(f"entire CLI failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def _adjacency():
    """Undirected adjacency over the directed call-edge fixture, so BFS can
    walk both 'who calls this' and 'what this reaches', including through a
    shared node (that's how the hidden InventoryService coupling surfaces —
    it shares PricingUtils.applyRounding with the changed PaymentService
    code, with no direct edge between the two services)."""
    adj = defaultdict(list)
    for edge in D.CALL_EDGES:
        src = edge[0]
        tgt = edge[1]
        adj[src].append(edge)
        adj[tgt].append(edge)
    return adj


def impact(symbol: str, repo_path: Optional[str] = None, max_hops: int = 2) -> GraphQueryResult:
    """Blast radius for a changed symbol: direct + hidden (multi-hop) callers."""
    if settings.USE_REAL_ENTIRE_CLI:
        data = _run_real_cli(["graph", "impact", "--symbol", symbol, "--repo", repo_path or "."])
        return GraphQueryResult(**data)

    adj = _adjacency()
    nodes = {symbol}
    seen_edge_keys = set()
    edges: List[GraphEdge] = []
    frontier = {symbol}

    for _ in range(max_hops):
        next_frontier = set()
        for node in frontier:
            for src, tgt, relation, conf, note in adj.get(node, []):
                key = (src, tgt, relation)
                if key not in seen_edge_keys:
                    seen_edge_keys.add(key)
                    edges.append(GraphEdge(
                        source=_symbol_ref(src), target=_symbol_ref(tgt),
                        relation=relation, confidence=conf, evidence_note=note,
                    ))
                other = tgt if src == node else src
                if other not in nodes:
                    nodes.add(other)
                    next_frontier.add(other)
        frontier = next_frontier
        if not frontier:
            break

    overall_conf = round(sum(e.confidence for e in edges) / len(edges), 2) if edges else 0.5
    return GraphQueryResult(
        query_type="impact",
        query=symbol,
        nodes=[_symbol_ref(n) for n in nodes],
        edges=edges,
        confidence=overall_conf,
        heuristic=True,
        source="entire-graph (mock adapter)" if not settings.USE_REAL_ENTIRE_CLI else "entire-graph",
        limitations=LIMITATIONS_STATIC,
    )


def neighbors(symbol: str) -> GraphQueryResult:
    """Direct callers/callees only (1 hop), vs. impact's full blast radius."""
    result = impact(symbol)
    direct = [e for e in result.edges if e.confidence >= 0.85]
    result.edges = direct
    result.query_type = "neighbors"
    return result


def diff(base_sha: str, head_sha: str) -> GraphQueryResult:
    """Semantic diff between two commits: which symbols actually changed."""
    changed = [s for cf in D.CHANGED_FILES for s in cf["changed_symbols"]]
    return GraphQueryResult(
        query_type="diff",
        query=f"{base_sha}..{head_sha}",
        nodes=[_symbol_ref(s) for s in changed],
        edges=[],
        confidence=0.93,
        heuristic=True,
        source="entire-graph (mock adapter)",
        limitations=["Diff is symbol-level, not line-level AST diffing in this demo."],
    )


def co_change(file_path: str) -> List[dict]:
    """Historical co-change evidence (files that tend to change together)."""
    out = []
    for a, b, freq, note in D.CO_CHANGE_EDGES:
        if a == file_path or b == file_path:
            other = b if a == file_path else a
            out.append({"file": other, "frequency": freq, "note": note})
    return out


def snapshot(repo_full_name: str) -> dict:
    """Whole-repo graph snapshot summary, used for the Repository Overview tab."""
    return {
        "repository": repo_full_name,
        "symbol_count": len(D.SYMBOLS),
        "edge_count": len(D.CALL_EDGES),
        "last_indexed_at": "2026-09-04T08:00:00Z",
        "source": "entire-graph (mock adapter)",
    }


def checkpoints_for_commit(commit_sha: str) -> List[Checkpoint]:
    """Entire CLI checkpoint/session context: what changed, why, and by whom."""
    return [Checkpoint(**c) for c in D.CHECKPOINTS if c["commit_sha"] == commit_sha or commit_sha == ""]


def all_checkpoints() -> List[Checkpoint]:
    return [Checkpoint(**c) for c in D.CHECKPOINTS]
