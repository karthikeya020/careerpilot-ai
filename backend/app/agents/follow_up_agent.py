"""Follow-Up Question Agent -- responsibility: decide whether an interview
answer just graded by TechnicalAgent/HRAgent left a real, specific gap worth
probing with one natural spoken follow-up, and if so, phrase it. This is what
turns the Interview Arena from a fixed question bank into an actual
back-and-forth: interview_service.maybe_insert_follow_up calls this agent
right after grading, and only inserts a follow-up question when
`should_follow_up` is true. Provider-backed with the same
deterministic-fallback pattern as TechnicalAgent/HRAgent: with a live key
configured, a real model phrases a grounded follow-up; the fake-provider
fallback picks the concrete gap (a missing expected keyword, or a missing
measurable STAR result) directly from the grading output already computed --
never a placeholder, never an invented question unrelated to what was said.
"""

import json
from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput
from app.agents.confidence import rubric_confidence
from app.ai.registry import get_chat_provider
from app.ai.schemas import ChatMessage, StructuredChatRequest

PROMPT_VERSION = "follow-up-v1"
_DEPTH_CUES = ["because", "trade-off", "tradeoff", "however", "for example", "specifically", "in contrast"]


class FollowUpInput(AgentInput):
    question_prompt: str
    transcript: str
    mode: str
    expected_keywords: list[str] = Field(default_factory=list)
    dimension_scores: dict[str, float] = Field(default_factory=dict)


class FollowUpOutput(AgentOutput):
    should_follow_up: bool = False
    follow_up_prompt: str = ""
    gap_description: str = ""


def _deterministic_follow_up(request: StructuredChatRequest) -> dict:
    data = json.loads(request.messages[-1].content)
    mode = data.get("mode", "")
    transcript_lower = data.get("transcript", "").lower()
    dimension_scores = data.get("dimension_scores", {})

    if mode in ("technical", "dsa"):
        expected = [k.lower() for k in data.get("expected_keywords", [])]
        missing = [k for k in expected if k not in transcript_lower]

        if missing:
            gap = missing[0]
            return {
                "should_follow_up": True,
                "follow_up_prompt": (
                    f"You didn't mention {gap} -- can you walk me through how {gap} applies here, "
                    "and why it matters for this problem?"
                ),
                "gap_description": f"Expected concept '{gap}' was not addressed in the answer.",
            }

        has_depth_cue = any(cue in transcript_lower for cue in _DEPTH_CUES)
        if dimension_scores.get("depth", 1.0) < 0.5 and not has_depth_cue:
            return {
                "should_follow_up": True,
                "follow_up_prompt": (
                    "Can you go one level deeper -- what's a trade-off or edge case that makes this harder "
                    "in practice?"
                ),
                "gap_description": "Answer covered the expected concepts but stayed shallow -- no trade-off/edge-case reasoning detected.",
            }

        return {
            "should_follow_up": False,
            "follow_up_prompt": "",
            "gap_description": "Answer covered the expected concepts with sufficient depth -- no follow-up needed.",
        }

    structure_score = dimension_scores.get("structure", 1.0)
    evidence_score = dimension_scores.get("evidence", 1.0)
    if structure_score < 0.5 or evidence_score < 0.5:
        return {
            "should_follow_up": True,
            "follow_up_prompt": "What was the concrete, measurable result or outcome of that situation?",
            "gap_description": "No clear measurable result/outcome was detected in the answer's structure.",
        }

    return {
        "should_follow_up": False,
        "follow_up_prompt": "",
        "gap_description": "Answer already included a clear structure and a concrete outcome -- no follow-up needed.",
    }


class FollowUpAgent(Agent[FollowUpInput, FollowUpOutput]):
    name = "follow_up"
    prompt_version = PROMPT_VERSION
    timeout_seconds = 10.0
    allowed_tools: ClassVar[list[str]] = []
    output_cls = FollowUpOutput

    def run(self, agent_input: FollowUpInput) -> FollowUpOutput:
        provider = get_chat_provider()
        request = StructuredChatRequest(
            task_type="interview_follow_up",
            prompt_version=self.prompt_version,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "Decide whether the candidate's interview answer left a real, specific gap worth "
                        "probing with exactly one natural spoken follow-up question. Only follow up when "
                        "there is a genuine gap -- a missing expected concept, a shallow/unsupported claim, "
                        "or a missing measurable outcome. Never invent a question unrelated to what was said, "
                        "and never fabricate facts about the candidate. If the answer is already solid, set "
                        "should_follow_up to false and leave follow_up_prompt empty."
                    ),
                ),
                ChatMessage(role="user", content=json.dumps(agent_input.model_dump())),
            ],
            response_schema_name="FollowUpOutput",
            deterministic_fn=_deterministic_follow_up,
        )
        result = provider.complete_structured(request)
        parsed = result.parsed
        confidence = rubric_confidence(
            keyword_count=len(agent_input.expected_keywords) or 4,
            is_fallback=result.is_fallback,
        )
        return FollowUpOutput(
            confidence=confidence,
            evidence_ids=[],
            reasoning_summary=parsed["gap_description"],
            inference_type=result.inference_type,
            should_follow_up=parsed["should_follow_up"],
            follow_up_prompt=parsed["follow_up_prompt"],
            gap_description=parsed["gap_description"],
        )
