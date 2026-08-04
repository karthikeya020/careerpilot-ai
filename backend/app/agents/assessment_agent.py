"""Assessment Agent -- responsibility: grade free-form assessment responses
(short_answer, code_reading, concept_explanation) against a keyword rubric.
MCQ/multiple-selection questions never reach this agent -- those are scored
by exact-match arithmetic in app/services/assessment_service.py. This is
the AI evaluator required for free-form answers, behind the provider
abstraction (Prompt 2: "Use an AI evaluator only for free-form answers");
the fake provider's fallback is a real keyword-overlap grader, not a
placeholder.
"""

import json
from typing import ClassVar

from app.agents.base import Agent, AgentInput, AgentOutput
from app.ai.registry import get_chat_provider
from app.ai.schemas import ChatMessage, StructuredChatRequest

PROMPT_VERSION = "assessment-grading-v1"


class AssessmentGradingInput(AgentInput):
    question_prompt: str
    response_text: str
    keywords: list[str]
    sample_answer: str


class AssessmentGradingOutput(AgentOutput):
    score: float = 0.0
    is_correct: bool = False
    feedback: str = ""


def _deterministic_keyword_grading(request: StructuredChatRequest) -> dict:
    data = json.loads(request.messages[-1].content)
    response_lower = data["response_text"].lower()
    keywords = [k.lower() for k in data["keywords"]]
    if not keywords:
        return {"score": 0.5, "is_correct": False, "feedback": "No rubric keywords available to grade against."}
    matched = [k for k in keywords if k in response_lower]
    score = round(len(matched) / len(keywords), 4)
    is_correct = score >= 0.5
    feedback = (
        f"Matched {len(matched)}/{len(keywords)} expected concept(s): {', '.join(matched) or 'none'}. "
        f"Reference answer: {data['sample_answer']}"
    )
    return {"score": score, "is_correct": is_correct, "feedback": feedback}


class AssessmentAgent(Agent[AssessmentGradingInput, AssessmentGradingOutput]):
    name = "assessment"
    prompt_version = PROMPT_VERSION
    timeout_seconds = 10.0
    allowed_tools: ClassVar[list[str]] = ["question_rubric"]
    output_cls = AssessmentGradingOutput

    def run(self, agent_input: AssessmentGradingInput) -> AssessmentGradingOutput:
        provider = get_chat_provider()
        request = StructuredChatRequest(
            task_type="assessment_grading",
            prompt_version=self.prompt_version,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "Grade the student's free-form answer against the rubric keywords and sample answer. "
                        "Return a score from 0 to 1, whether it's correct (score >= 0.5), and brief feedback."
                    ),
                ),
                ChatMessage(role="user", content=json.dumps(agent_input.model_dump())),
            ],
            response_schema_name="AssessmentGradingOutput",
            deterministic_fn=_deterministic_keyword_grading,
        )
        result = provider.complete_structured(request)
        confidence = 0.55 if result.is_fallback else 0.8
        return AssessmentGradingOutput(
            confidence=confidence,
            evidence_ids=[],
            reasoning_summary=result.parsed["feedback"],
            inference_type=result.inference_type,
            score=result.parsed["score"],
            is_correct=result.parsed["is_correct"],
            feedback=result.parsed["feedback"],
        )
