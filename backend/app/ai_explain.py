"""
AI reasoning layer. Strict rule: this layer only ever receives already-
computed structured evidence (RiskResult, TestRecommendation[], graph
queries) and turns it into prose — summary, likely failure modes, a review
checklist, and "why run this test" answers. It never sets a risk score and
never invents a dependency; if a fact isn't in the structured evidence
passed in, it does not appear in the explanation.

Two modes:
  - Template engine (default, USE_REAL_LLM=false): fully deterministic,
    zero external calls, good enough for a demo and for reviewing exactly
    what the model is and isn't allowed to say.
  - Real LLM (USE_REAL_LLM=true, ANTHROPIC_API_KEY set): calls the
    Anthropic Messages API with the same structured evidence serialized
    into the prompt, and the system prompt below enforcing the same
    "explain only" constraint.
"""
import json
from typing import List

from .config import settings
from .schemas import RiskResult, TestRecommendation, GraphQueryResult, AIExplanation

SYSTEM_PROMPT = (
    "You are an engineering-risk explainer. You will be given structured "
    "risk factors, graph evidence, and test recommendations as JSON. "
    "Summarize them in plain language for a reviewer. You must NOT invent "
    "any dependency, file, symbol, or score that is not present in the "
    "JSON. You must NOT change the risk score or reorder test priority. "
    "Output strict JSON with keys: summary, likely_failure_modes (list), "
    "review_checklist (list), test_justifications (object keyed by test_name)."
)


def explain(
    risk: RiskResult,
    tests: List[TestRecommendation],
    impact_result: GraphQueryResult,
    changed_symbols: List[str],
) -> AIExplanation:
    if settings.USE_REAL_LLM and settings.ANTHROPIC_API_KEY:
        return _explain_with_llm(risk, tests, impact_result, changed_symbols)
    return _explain_with_template(risk, tests, impact_result, changed_symbols)


def _explain_with_template(risk, tests, impact_result, changed_symbols) -> AIExplanation:
    hidden = [t for t in tests if t.is_hidden_dependency]
    summary_parts = [
        f"This change touches {', '.join(changed_symbols)} and is classified "
        f"{risk.level.value} risk ({risk.score}/100)."
    ]
    if hidden:
        summary_parts.append(
            f"{len(hidden)} of the recommended tests exist only to cover a "
            f"dependency that isn't visible in the diff itself — run those first."
        )
    summary_parts.append(
        f"Entire Graph's confidence in this blast radius is {impact_result.confidence:.0%}; "
        f"treat the graph as a strong lead, not a guarantee."
    )

    failure_modes = []
    for f in sorted(risk.factors, key=lambda x: x.contribution, reverse=True)[:3]:
        if f.contribution > 0:
            failure_modes.append(f"{f.label}: {f.detail}")

    checklist = [
        "Confirm the changed function's contract (inputs/outputs/rounding "
        "or currency assumptions) is unchanged for existing callers.",
        "Run the recommended tests below before the full suite.",
    ]
    if hidden:
        checklist.append(
            "Specifically verify the hidden-dependency path called out above — "
            "it will not show up in a normal code review diff."
        )
    if risk.level.value in ("HIGH", "CRITICAL"):
        checklist.append("Request a second reviewer given the risk level.")

    justifications = {}
    for t in tests:
        justifications[t.test_name] = t.reason

    return AIExplanation(
        summary=" ".join(summary_parts),
        likely_failure_modes=failure_modes or ["No significant risk factors detected."],
        review_checklist=checklist,
        test_justifications=justifications,
        generated_by="template-engine (mock, deterministic)",
    )


def _explain_with_llm(risk, tests, impact_result, changed_symbols) -> AIExplanation:
    """Real-mode path. Requires `pip install anthropic` and ANTHROPIC_API_KEY.
    Left as a clearly-marked integration point rather than wired by default
    so this demo never makes an unexpected network call."""
    import httpx

    payload = {
        "risk": json.loads(risk.model_dump_json()),
        "tests": [json.loads(t.model_dump_json()) for t in tests],
        "impact": json.loads(impact_result.model_dump_json()),
        "changed_symbols": changed_symbols,
    }
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 1000,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": json.dumps(payload)}],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    parsed = json.loads(text)
    return AIExplanation(
        summary=parsed["summary"],
        likely_failure_modes=parsed["likely_failure_modes"],
        review_checklist=parsed["review_checklist"],
        test_justifications=parsed["test_justifications"],
        generated_by="claude-sonnet-4-6",
    )
