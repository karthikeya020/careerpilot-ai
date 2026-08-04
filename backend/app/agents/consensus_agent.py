"""Consensus & Self-Auditor Agent -- responsibility: given multiple
specialist outputs answering the same question (a multi-agent council),
compute a consensus confidence and a disagreement score. High disagreement
is exactly what CARE's `agent_disagreement` routing factor consumes to
decide whether to escalate to the critic/reflection route (see
app/care_engine/policy.py). Deterministic statistics -- disagreement is the
population standard deviation of the input confidences, which is a real
measure of spread, not an invented number.
"""

import statistics
from typing import ClassVar

from app.agents.base import Agent, AgentInput, AgentOutput


class ConsensusVote(AgentInput):
    agent_name: str
    confidence: float


class ConsensusInput(AgentInput):
    votes: list[ConsensusVote]


class ConsensusOutput(AgentOutput):
    consensus_confidence: float = 0.0
    disagreement: float = 0.0
    flagged: bool = False


_DISAGREEMENT_FLAG_THRESHOLD = 0.20


class ConsensusAgent(Agent[ConsensusInput, ConsensusOutput]):
    name = "consensus"
    prompt_version = "consensus-v1"
    timeout_seconds = 1.0
    allowed_tools: ClassVar[list[str]] = []
    output_cls = ConsensusOutput

    def run(self, agent_input: ConsensusInput) -> ConsensusOutput:
        if not agent_input.votes:
            return ConsensusOutput(
                confidence=0.0,
                evidence_ids=[],
                reasoning_summary="No votes to reach consensus over.",
                inference_type="deterministic_calculation",
                flagged=True,
            )

        confidences = [v.confidence for v in agent_input.votes]
        mean_confidence = statistics.mean(confidences)
        disagreement = statistics.pstdev(confidences) if len(confidences) > 1 else 0.0
        flagged = disagreement > _DISAGREEMENT_FLAG_THRESHOLD
        consensus_confidence = round(mean_confidence * (1 - disagreement), 4)

        return ConsensusOutput(
            confidence=consensus_confidence,
            evidence_ids=[],
            reasoning_summary=(
                f"{len(agent_input.votes)} agent(s) voted with mean confidence {mean_confidence:.2f} "
                f"and disagreement {disagreement:.2f}."
            ),
            inference_type="deterministic_calculation",
            consensus_confidence=consensus_confidence,
            disagreement=round(disagreement, 4),
            flagged=flagged,
        )
