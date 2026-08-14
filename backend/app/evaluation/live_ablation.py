"""Live ablation, on stage: type one interview answer, see the Critic pass's
effect on confidence appear and disappear in real time -- the single-case,
interactive sibling of app/evaluation/ablations.py::run_reflection_ablation
(which runs a fixed 4-case batch). Nothing convinces a panel faster than
watching the architecture's value change live, against whatever they ask a
student to type.
"""

from statistics import mean

from app.agents.communication_agent import CommunicationAgent, CommunicationInput
from app.agents.critic_agent import CriticAgent, CriticClaim, CriticInput
from app.agents.technical_agent import TechnicalAgent, TechnicalInterviewInput

LIVE_ABLATION_VERSION = "live-ablation-v1"
_DEFAULT_QUESTION = "Explain the tradeoffs of adding a database index."
_DEFAULT_KEYWORDS = ["index", "trade-off", "overhead"]


def run_live_critic_toggle(transcript: str, question_prompt: str | None = None, expected_keywords: list[str] | None = None) -> dict:
    """Runs the exact same real council (TechnicalAgent + CommunicationAgent)
    over the given transcript, then reports the council's raw mean
    confidence (critic disabled) side-by-side with CriticAgent's real
    adjusted confidence (critic enabled) -- both for the identical input, so
    the only variable is whether the critic pass ran."""
    question_prompt = question_prompt or _DEFAULT_QUESTION
    expected_keywords = expected_keywords or _DEFAULT_KEYWORDS

    tech_out, _latency = TechnicalAgent().safe_run(
        TechnicalInterviewInput(question_prompt=question_prompt, transcript=transcript, expected_keywords=expected_keywords)
    )
    comm_out, _latency = CommunicationAgent().safe_run(CommunicationInput(transcript=transcript))

    claims = [
        CriticClaim(agent_name="technical", confidence=tech_out.confidence, evidence_ids=[]),
        CriticClaim(agent_name="communication", confidence=comm_out.professional_communication_score, evidence_ids=[]),
    ]
    raw_mean = round(mean(c.confidence for c in claims), 4)
    critic_out = CriticAgent().run(CriticInput(claims=claims))

    return {
        "engine_version": LIVE_ABLATION_VERSION,
        "transcript": transcript,
        "technical_confidence": tech_out.confidence,
        "communication_confidence": comm_out.professional_communication_score,
        "critic_off_confidence": raw_mean,
        "critic_on_confidence": critic_out.adjusted_confidence,
        "delta": round(critic_out.adjusted_confidence - raw_mean, 4),
        "issues_found": critic_out.issues,
        "verdict": critic_out.verdict,
    }
