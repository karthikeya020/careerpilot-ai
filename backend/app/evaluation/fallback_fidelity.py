"""Fallback fidelity: quantifies how closely the deterministic fake
provider's structured output tracks a live LLM's output on the same input --
converts "the demo is safe without an API key" from a design decision into a
validated one. Requires a live provider key; when none is configured (this
environment's default -- see app/ai/registry.py), reports that honestly
instead of inventing a number (Constitution rule 1).
"""

import json

from app.ai.providers.fake import FakeChatProvider
from app.ai.schemas import ChatMessage, StructuredChatRequest
from app.core.config import get_settings

FALLBACK_FIDELITY_VERSION = "fallback-fidelity-v1"

_SAMPLE_INPUT = {
    "student_name": "Fidelity Check Student",
    "skills_found": ["Python", "SQL", "FastAPI"],
    "sections_found": ["skills", "experience", "projects"],
}

_METHODOLOGY_NOTE = (
    "Runs the identical structured request through FakeChatProvider and the live provider and compares the "
    "resulting strengths/gaps lists (set overlap) and summary length as a proxy for how closely the deterministic "
    "fallback's content tracks a real model's on the same input."
)


def run_fallback_fidelity_check() -> dict:
    settings = get_settings()
    if not settings.primary_llm_api_key:
        return {
            "engine_version": FALLBACK_FIDELITY_VERSION,
            "measurable": False,
            "message": (
                "No live provider key is configured in this environment (Settings.primary_llm_api_key is empty), "
                "so fallback fidelity cannot be measured here -- this demo intentionally runs entirely on the "
                "deterministic fallback provider (see app/ai/registry.py::get_chat_provider). "
            )
            + _METHODOLOGY_NOTE,
            "methodology_note": _METHODOLOGY_NOTE,
        }

    from app.ai.providers.anthropic_provider import AnthropicChatProvider
    from app.agents.resume_intelligence_agent import _deterministic_resume_insight

    fake = FakeChatProvider()
    live = AnthropicChatProvider(api_key=settings.primary_llm_api_key, model=settings.primary_llm_model)

    request = StructuredChatRequest(
        task_type="resume_insight",
        prompt_version="fallback-fidelity-check",
        messages=[
            ChatMessage(role="system", content="Summarize resume strengths and gaps concisely and factually."),
            ChatMessage(role="user", content=json.dumps(_SAMPLE_INPUT)),
        ],
        response_schema_name="ResumeIntelligenceOutput",
        deterministic_fn=_deterministic_resume_insight,
    )

    fake_result = fake.complete_structured(request)
    live_result = live.complete_structured(request)

    fake_strengths = set(fake_result.parsed.get("strengths", []))
    live_strengths = set(live_result.parsed.get("strengths", []))
    strength_overlap = (
        round(len(fake_strengths & live_strengths) / len(fake_strengths | live_strengths), 4)
        if (fake_strengths | live_strengths)
        else None
    )

    return {
        "engine_version": FALLBACK_FIDELITY_VERSION,
        "measurable": True,
        "fake_provider": fake.name,
        "live_provider": live.name,
        "fake_summary": fake_result.parsed.get("summary", ""),
        "live_summary": live_result.parsed.get("summary", ""),
        "strength_set_overlap": strength_overlap,
        "fake_gap_count": len(fake_result.parsed.get("gaps", [])),
        "live_gap_count": len(live_result.parsed.get("gaps", [])),
        "methodology_note": _METHODOLOGY_NOTE,
    }
