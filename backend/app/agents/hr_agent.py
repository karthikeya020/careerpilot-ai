"""HR / Behavioral Interview Agent -- responsibility: score a behavioral
answer's relevance to the question and its STAR structure (Situation, Task,
Action, Result), and note whether it grounds itself in a specific, concrete
example. Provider-backed with a deterministic fallback that reuses the same
STAR-keyword heuristic as CommunicationAgent's `check_star_structure`, kept
as a separate, purpose-built pass here because it also has to judge
relevance to the specific question asked, not just structural shape.
"""

import json
import re
from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput
from app.ai.registry import get_chat_provider
from app.ai.schemas import ChatMessage, StructuredChatRequest

PROMPT_VERSION = "hr-interview-v1"
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "your", "you",
    "tell", "me", "about", "time", "when", "describe", "how", "did", "what", "was", "were",
    "have", "has", "that", "this", "would", "could", "can",
}
_SPECIFICITY_RE = re.compile(r"\b\d+(\.\d+)?%?\b")


def _significant_words(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    return {w for w in words if len(w) >= 4 and w not in _STOPWORDS}


class HRInterviewInput(AgentInput):
    question_prompt: str
    transcript: str


class HRInterviewOutput(AgentOutput):
    relevance_score: float = 0.0
    structure_score: float = 0.0
    evidence_score: float = 0.0
    star_components_found: list[str] = Field(default_factory=list)
    feedback: str = ""


def _deterministic_hr_grading(request: StructuredChatRequest) -> dict:
    from app.agents.communication_agent import _STAR_KEYWORDS

    data = json.loads(request.messages[-1].content)
    transcript_lower = data["transcript"].lower()

    prompt_terms = _significant_words(data["question_prompt"])
    transcript_terms = _significant_words(data["transcript"])
    relevance_score = round(len(prompt_terms & transcript_terms) / len(prompt_terms), 4) if prompt_terms else 0.6

    star_found = [c for c, phrases in _STAR_KEYWORDS.items() if any(p in transcript_lower for p in phrases)]
    structure_score = round(len(star_found) / 4, 4)

    has_specific_detail = bool(_SPECIFICITY_RE.search(data["transcript"]))
    evidence_score = 1.0 if has_specific_detail else 0.4

    feedback = (
        f"STAR components detected: {', '.join(star_found) or 'none'}. "
        f"{'Includes a specific, quantified detail.' if has_specific_detail else 'No specific numbers/timeframes detected -- a concrete detail would strengthen this answer.'}"
    )
    return {
        "relevance_score": relevance_score,
        "structure_score": structure_score,
        "evidence_score": evidence_score,
        "star_components_found": star_found,
        "feedback": feedback,
    }


class HRAgent(Agent[HRInterviewInput, HRInterviewOutput]):
    name = "hr"
    prompt_version = PROMPT_VERSION
    timeout_seconds = 10.0
    allowed_tools: ClassVar[list[str]] = []
    output_cls = HRInterviewOutput

    def run(self, agent_input: HRInterviewInput) -> HRInterviewOutput:
        provider = get_chat_provider()
        request = StructuredChatRequest(
            task_type="hr_interview_grading",
            prompt_version=self.prompt_version,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "Score the candidate's behavioral interview answer on relevance to the question "
                        "and STAR structure (Situation/Task/Action/Result), and whether it cites a specific example."
                    ),
                ),
                ChatMessage(role="user", content=json.dumps(agent_input.model_dump())),
            ],
            response_schema_name="HRInterviewOutput",
            deterministic_fn=_deterministic_hr_grading,
        )
        result = provider.complete_structured(request)
        parsed = result.parsed
        confidence = 0.55 if result.is_fallback else 0.85
        return HRInterviewOutput(
            confidence=confidence,
            evidence_ids=[],
            reasoning_summary=parsed["feedback"],
            inference_type=result.inference_type,
            relevance_score=parsed["relevance_score"],
            structure_score=parsed["structure_score"],
            evidence_score=parsed["evidence_score"],
            star_components_found=parsed["star_components_found"],
            feedback=parsed["feedback"],
        )
