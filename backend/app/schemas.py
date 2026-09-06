"""
The shared evidence/risk vocabulary used across the Entire Graph adapter,
the risk engine, the Databricks adapter, and the API layer. Keeping this in
one place is what lets the risk engine stay deterministic and auditable:
every score traces back to typed fields here, never to free text.
"""
from __future__ import annotations
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceStatus(str, Enum):
    """How safely the system can rely on an evidence set."""
    CONFIRMED = "CONFIRMED"
    PARTIAL = "PARTIAL"
    VERIFY_REQUIRED = "VERIFY REQUIRED"


class SymbolRef(BaseModel):
    """A precise, evidence-grade pointer into the codebase."""
    symbol: str
    file: str
    line: int
    kind: str = "function"  # function|class|route|module


class GraphEdge(BaseModel):
    """One relationship returned by Entire Graph (caller/callee/co-change/etc)."""
    source: SymbolRef
    target: SymbolRef
    relation: str  # calls|called_by|co_change|imports|route_handler
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_note: str = ""


class GraphQueryResult(BaseModel):
    """
    Normalized output of an Entire Graph query (search/def/neighbors/impact/
    diff/snapshot). `source` and `heuristic` are always surfaced to the UI so
    Entire Graph's results are never presented as compiler-verified truth.
    """
    query_type: str
    query: str
    nodes: List[SymbolRef] = []
    edges: List[GraphEdge] = []
    confidence: float = Field(ge=0.0, le=1.0)
    heuristic: bool = True
    source: str = "entire-graph"
    limitations: List[str] = []
    evidence_status: EvidenceStatus = EvidenceStatus.PARTIAL
    is_complete: bool = False
    verification_steps: List[str] = []


class ChangedFile(BaseModel):
    path: str
    additions: int
    deletions: int
    changed_symbols: List[str] = []


class RiskFactor(BaseModel):
    key: str
    label: str
    value: float           # normalized 0-1 contribution input
    weight: float           # weight applied in the weighted sum
    contribution: float     # value * weight, i.e. points added to the 0-100 score
    detail: str = ""


class RiskResult(BaseModel):
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    factors: List[RiskFactor]
    rationale: List[str]
    graph_confidence: float
    evidence_status: EvidenceStatus = EvidenceStatus.PARTIAL
    verification_required: bool = True


class EvidenceStep(BaseModel):
    """One hop in an evidence chain, e.g. PaymentService.processPayment ->
    CheckoutService.checkout."""
    symbol: SymbolRef
    relation_to_next: Optional[str] = None


class TestRecommendation(BaseModel):
    test_name: str
    file: str
    line: int
    priority_rank: int
    relevance_score: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence_chain: List[EvidenceStep]
    historical_failure_rate: Optional[float] = None
    is_hidden_dependency: bool = False
    affected_symbol: str = ""
    evidence_source: str = ""
    evidence_status: EvidenceStatus = EvidenceStatus.PARTIAL
    verification_required: bool = True


class HistoricalFailure(BaseModel):
    commit_sha: str
    symbol: str
    test_name: str
    outcome: str  # pass|fail
    failure_message: Optional[str] = None
    occurred_at: str
    seeded_demo_data: bool = True


class Checkpoint(BaseModel):
    id: str
    title: str
    summary: str
    author_type: str  # human|ai_agent
    author_name: str
    session_id: Optional[str] = None
    prompt_excerpt: Optional[str] = None
    files_changed: List[str] = []
    commit_sha: Optional[str] = None
    created_at: str


class AIExplanation(BaseModel):
    summary: str
    likely_failure_modes: List[str]
    review_checklist: List[str]
    test_justifications: dict
    generated_by: str  # "template-engine (mock)" | "claude-sonnet-4-6"
    disclaimer: str = (
        "Generated from structured risk/evidence data below. "
        "The model explains and summarizes only — it does not set the risk "
        "score or invent dependencies."
    )


class AnalysisResult(BaseModel):
    analysis_id: str
    repository: str
    ref_label: str
    base_sha: str
    head_sha: str
    changed_files: List[ChangedFile]
    graph_queries: List[GraphQueryResult]
    risk: RiskResult
    test_recommendations: List[TestRecommendation]
    historical_failures: List[HistoricalFailure]
    checkpoints: List[Checkpoint]
    ai_explanation: AIExplanation
    provenance: dict
    verification_plan: List[str] = []
