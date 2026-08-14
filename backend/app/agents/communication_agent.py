"""Communication Agent -- responsibility: compute observable communication
indicators directly from a transcript (and, when available, audio duration):
word count, filler-word frequency, sentence completeness, speaking rate, and
STAR-structure presence for behavioral answers. Every number here is a real,
inspectable calculation over the text CareerPilot actually stored -- never an
inference about the student's honesty, personality, or emotional state
(Prompt 3's explicit "do not infer" list). Deterministic and cheap, so it
runs on every interview answer regardless of which CARE route is chosen for
the judgment-heavy dimensions.
"""

import re
from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput

# Conservative filler-word list: whole-word/phrase matches only, chosen to
# minimize false positives against normal technical vocabulary (e.g. "like"
# alone is excluded -- too common as a verb/preposition to be a reliable
# filler-word signal on its own).
_FILLER_PATTERNS = [
    r"\bum+\b",
    r"\buh+\b",
    r"\ber+\b",
    r"\bhmm+\b",
    r"\byou know\b",
    r"\bsort of\b",
    r"\bkind of\b",
    r"\bi mean\b",
    r"\bbasically\b",
]
_FILLER_RE = re.compile("|".join(_FILLER_PATTERNS), re.IGNORECASE)

_STAR_KEYWORDS = {
    "situation": ["when i", "at my", "during my", "while working", "in my role", "at the time"],
    "task": ["i needed to", "the goal was", "my task was", "i was responsible for", "we needed to"],
    "action": ["i decided", "i implemented", "so i", "i built", "i led", "i designed", "i created"],
    "result": ["as a result", "resulted in", "ultimately", "in the end", "improved", "increased", "reduced"],
}


class CommunicationInput(AgentInput):
    transcript: str
    audio_duration_seconds: float | None = None
    check_star_structure: bool = False
    # Fraction (0-1) of the recording where the webcam feed showed a real,
    # changing image rather than a blank/covered frame -- computed
    # client-side via simple canvas frame-brightness sampling (see
    # frontend/hooks/use-audio-recorder.ts). This agent does not compute it
    # and never turns it into a claim about attention, eye contact, or
    # confidence -- it's a pure passthrough of an observable presence ratio,
    # consistent with this module's "never infer emotional state" contract.
    camera_on_ratio: float | None = None


class CommunicationOutput(AgentOutput):
    word_count: int = 0
    filler_word_count: int = 0
    filler_ratio: float = 0.0
    sentence_count: int = 0
    sentence_completeness_ratio: float = 0.0
    speaking_rate_wpm: float | None = None
    star_components_found: list[str] = Field(default_factory=list)
    clarity_score: float = 0.0
    conciseness_score: float = 0.0
    professional_communication_score: float = 0.0
    camera_on_ratio: float | None = None


def _conciseness(word_count: int) -> float:
    if word_count == 0:
        return 0.0
    if 40 <= word_count <= 200:
        return 1.0
    if word_count < 40:
        return round(max(0.3, word_count / 40), 4)
    return round(max(0.3, 1 - (word_count - 200) / 400), 4)


class CommunicationAgent(Agent[CommunicationInput, CommunicationOutput]):
    name = "communication"
    prompt_version = "communication-v1"
    timeout_seconds = 2.0
    allowed_tools: ClassVar[list[str]] = []
    output_cls = CommunicationOutput

    def run(self, agent_input: CommunicationInput) -> CommunicationOutput:
        transcript = agent_input.transcript.strip()
        if not transcript:
            return CommunicationOutput(
                confidence=0.0,
                evidence_ids=[],
                reasoning_summary="Transcript is empty -- no communication metrics available.",
                inference_type="deterministic_calculation",
            )

        words = transcript.split()
        word_count = len(words)
        filler_matches = _FILLER_RE.findall(transcript)
        filler_word_count = len(filler_matches)
        filler_ratio = round(filler_word_count / word_count, 4) if word_count else 0.0

        raw_sentences = [s.strip() for s in re.split(r"[.!?]+", transcript) if s.strip()]
        sentences = raw_sentences or [transcript]
        complete = [s for s in sentences if len(s.split()) >= 3]
        sentence_completeness_ratio = round(len(complete) / len(sentences), 4)

        speaking_rate_wpm = None
        if agent_input.audio_duration_seconds and agent_input.audio_duration_seconds > 0:
            speaking_rate_wpm = round(word_count / (agent_input.audio_duration_seconds / 60), 1)

        star_found: list[str] = []
        if agent_input.check_star_structure:
            lower = transcript.lower()
            for component, phrases in _STAR_KEYWORDS.items():
                if any(phrase in lower for phrase in phrases):
                    star_found.append(component)

        conciseness_score = _conciseness(word_count)
        clarity_score = round(max(0.0, min(1.0, (1 - filler_ratio * 3) * (0.5 + 0.5 * sentence_completeness_ratio))), 4)
        professional_score = round(max(0.0, (clarity_score + conciseness_score) / 2 - (0.1 if filler_ratio > 0.08 else 0)), 4)

        summary = (
            f"{word_count} word(s), {filler_word_count} filler word(s) ({filler_ratio:.0%}), "
            f"{len(sentences)} sentence(s), {sentence_completeness_ratio:.0%} judged complete."
        )
        if speaking_rate_wpm is not None:
            summary += f" Estimated speaking rate {speaking_rate_wpm:.0f} wpm."
        if agent_input.camera_on_ratio is not None:
            summary += f" Camera was on for {agent_input.camera_on_ratio:.0%} of the recording."

        return CommunicationOutput(
            confidence=0.9,
            evidence_ids=[],
            reasoning_summary=summary,
            inference_type="deterministic_calculation",
            camera_on_ratio=agent_input.camera_on_ratio,
            word_count=word_count,
            filler_word_count=filler_word_count,
            filler_ratio=filler_ratio,
            sentence_count=len(sentences),
            sentence_completeness_ratio=sentence_completeness_ratio,
            speaking_rate_wpm=speaking_rate_wpm,
            star_components_found=star_found,
            clarity_score=clarity_score,
            conciseness_score=conciseness_score,
            professional_communication_score=professional_score,
        )
