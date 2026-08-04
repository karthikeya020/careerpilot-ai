"""Technical Interview Agent -- responsibility: score a technical interview
answer's relevance, correctness, and depth against the question's expected
keywords/concept. Provider-backed, same pattern as AssessmentAgent: with a
live key configured, a real model judges the answer; the fake-provider
fallback is a real (if less nuanced) keyword-overlap grader, not a
placeholder -- its `correctness` dimension is explicitly labeled a proxy in
the fallback's reasoning summary, never presented as verified grading.
"""

import json
from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput
from app.ai.registry import get_chat_provider
from app.ai.schemas import ChatMessage, StructuredChatRequest

PROMPT_VERSION = "technical-interview-v1"
_DEPTH_CUES = ["because", "trade-off", "tradeoff", "however", "for example", "specifically", "in contrast"]


class TechnicalInterviewInput(AgentInput):
    question_prompt: str
    transcript: str
    expected_keywords: list[str] = Field(default_factory=list)
    concept_name: str = ""


class TechnicalInterviewOutput(AgentOutput):
    relevance_score: float = 0.0
    correctness_score: float = 0.0
    depth_score: float = 0.0
    matched_keywords: list[str] = Field(default_factory=list)
    feedback: str = ""


def _deterministic_technical_grading(request: StructuredChatRequest) -> dict:
    data = json.loads(request.messages[-1].content)
    transcript_lower = data["transcript"].lower()
    keywords = [k.lower() for k in data["expected_keywords"]]

    if not keywords:
        return {
            "relevance_score": 0.5,
            "correctness_score": 0.5,
            "depth_score": 0.3,
            "matched_keywords": [],
            "feedback": "No expected-keyword rubric available for this question; scores are a rough default.",
        }

    matched = [k for k in keywords if k in transcript_lower]
    keyword_ratio = round(len(matched) / len(keywords), 4)
    has_depth_cue = any(cue in transcript_lower for cue in _DEPTH_CUES)
    depth_score = round(min(1.0, 0.5 * keyword_ratio + (0.5 if has_depth_cue else 0.2)), 4)

    return {
        "relevance_score": keyword_ratio,
        "correctness_score": keyword_ratio,
        "depth_score": depth_score,
        "matched_keywords": matched,
        "feedback": (
            f"Matched {len(matched)}/{len(keywords)} expected concept(s): {', '.join(matched) or 'none'}. "
            "Correctness here is a keyword-overlap proxy, not verified technical grading -- "
            "configure a live provider for deeper evaluation."
        ),
    }


class TechnicalAgent(Agent[TechnicalInterviewInput, TechnicalInterviewOutput]):
    name = "technical"
    prompt_version = PROMPT_VERSION
    timeout_seconds = 10.0
    allowed_tools: ClassVar[list[str]] = ["question_rubric"]
    output_cls = TechnicalInterviewOutput

    def run(self, agent_input: TechnicalInterviewInput) -> TechnicalInterviewOutput:
        provider = get_chat_provider()
        request = StructuredChatRequest(
            task_type="technical_interview_grading",
            prompt_version=self.prompt_version,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "Score the candidate's technical interview answer on relevance, correctness, "
                        "and depth (each 0-1) against the expected keywords/concept. Be evidence-based."
                    ),
                ),
                ChatMessage(role="user", content=json.dumps(agent_input.model_dump())),
            ],
            response_schema_name="TechnicalInterviewOutput",
            deterministic_fn=_deterministic_technical_grading,
        )
        result = provider.complete_structured(request)
        parsed = result.parsed
        confidence = 0.55 if result.is_fallback else 0.85
        return TechnicalInterviewOutput(
            confidence=confidence,
            evidence_ids=[],
            reasoning_summary=parsed["feedback"],
            inference_type=result.inference_type,
            relevance_score=parsed["relevance_score"],
            correctness_score=parsed["correctness_score"],
            depth_score=parsed["depth_score"],
            matched_keywords=parsed["matched_keywords"],
            feedback=parsed["feedback"],
        )
