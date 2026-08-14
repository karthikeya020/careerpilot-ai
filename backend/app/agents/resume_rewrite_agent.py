"""Resume Rewrite Agent -- responsibility: suggest a stronger phrasing for a
weak or missing-skill resume bullet, constrained to only rephrase evidence
the student already has (a project snippet, an assessment explanation, a
resume line) -- never invent a tool, number, or outcome that isn't already
present in the supplied evidence. This is a direct, explicit application of
Constitution rule 1 (never invent evidence) to a generative task, so the
"no evidence supplied -> no rewrite" path is load-bearing, not an edge case.

Follows the same provider-abstraction + deterministic-fallback shape as
ResumeIntelligenceAgent: a live LLM key produces an actual rewrite; with no
key configured, the deterministic fallback never fabricates language either
-- it returns the student's own evidence verbatim rather than a synthesized
sentence, since paraphrasing safely without a model is not something a
template can guarantee.
"""

import json
from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput
from app.ai.registry import get_chat_provider
from app.ai.schemas import ChatMessage, StructuredChatRequest

PROMPT_VERSION = "resume-rewrite-v1"

_NO_EVIDENCE_NOTE = (
    "No existing evidence for this skill was found on your resume, in a project, or in an assessment "
    "result. Add a project or complete an assessment for it first -- a rewrite can only rephrase evidence "
    "you actually have, never invent experience you don't."
)


class ResumeRewriteInput(AgentInput):
    skill_name: str
    evidence_snippets: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class ResumeRewriteOutput(AgentOutput):
    has_sufficient_evidence: bool = False
    rewritten_bullet: str | None = None
    note: str = ""


def _deterministic_rewrite(request: StructuredChatRequest) -> dict:
    payload = json.loads(request.messages[-1].content)
    snippets: list[str] = payload["evidence_snippets"]
    if not snippets:
        return {"has_sufficient_evidence": False, "rewritten_bullet": None, "note": _NO_EVIDENCE_NOTE}
    best = max(snippets, key=len).strip()
    return {
        "has_sufficient_evidence": True,
        "rewritten_bullet": best,
        "note": (
            "Deterministic fallback (no AI provider configured): showing your existing evidence verbatim "
            "rather than risk paraphrasing it inaccurately. Connect a provider for an actual rewrite."
        ),
    }


class ResumeRewriteAgent(Agent[ResumeRewriteInput, ResumeRewriteOutput]):
    name = "resume_rewrite"
    prompt_version = PROMPT_VERSION
    timeout_seconds = 8.0
    allowed_tools: ClassVar[list[str]] = ["resume_evidence_snippets"]
    output_cls = ResumeRewriteOutput

    def run(self, agent_input: ResumeRewriteInput) -> ResumeRewriteOutput:
        if not agent_input.evidence_snippets:
            return ResumeRewriteOutput(
                confidence=0.9,
                evidence_ids=[],
                reasoning_summary=_NO_EVIDENCE_NOTE,
                inference_type="deterministic_calculation",
                has_sufficient_evidence=False,
                rewritten_bullet=None,
                note=_NO_EVIDENCE_NOTE,
            )

        provider = get_chat_provider()
        request = StructuredChatRequest(
            task_type="resume_rewrite",
            prompt_version=self.prompt_version,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "Rewrite the resume bullet using ONLY facts present in the evidence snippets given. "
                        "Use a strong action verb and, if a metric already appears in the evidence, keep it. "
                        "Do not add any tool, number, outcome, or claim that is not already in the evidence. "
                        "If the evidence is too thin to responsibly rewrite, say so instead of guessing."
                    ),
                ),
                ChatMessage(role="user", content=json.dumps(agent_input.model_dump())),
            ],
            response_schema_name="ResumeRewriteOutput",
            deterministic_fn=_deterministic_rewrite,
        )
        result = provider.complete_structured(request)
        parsed = result.parsed
        return ResumeRewriteOutput(
            confidence=0.75 if parsed["has_sufficient_evidence"] else 0.9,
            evidence_ids=agent_input.evidence_ids,
            reasoning_summary=parsed["note"],
            inference_type=result.inference_type,
            has_sufficient_evidence=parsed["has_sufficient_evidence"],
            rewritten_bullet=parsed["rewritten_bullet"],
            note=parsed["note"],
        )
