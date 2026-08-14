"""CARE efficiency frontier: real latency and cost-proxy vs. accuracy for
always-single-agent, always-multi-agent-council, and CARE-adaptive routing,
over a small curated interview-answer case set -- using the real
TechnicalAgent/CommunicationAgent/ConsensusAgent code paths and real
`decide_route`, never a zero-filled placeholder (contrast with
app/evaluation/run.py's routing-decision-only comparison, which never
invokes an agent and so never measures real latency).

Cost is reported honestly: this environment runs on the deterministic
fallback provider by default (no live API key configured), so real dollar
cost is $0 across all three conditions here. The number of agent/LLM calls
invoked is used as the real, meaningful cost proxy instead -- it is exactly
what would scale to real dollars the moment a live provider key is set
(Constitution rule 1: never invent a number; report what's actually true in
this environment).
"""

import time
import uuid
from dataclasses import dataclass
from statistics import mean

from sqlalchemy.orm import Session

from app.agents.communication_agent import CommunicationAgent, CommunicationInput
from app.agents.consensus_agent import ConsensusAgent, ConsensusInput, ConsensusVote
from app.agents.technical_agent import TechnicalAgent, TechnicalInterviewInput
from app.care_engine.policy import decide_route
from app.care_engine.schemas import RoutingFactors
from app.models.evaluation import EvaluationResult, EvaluationRun

EFFICIENCY_FRONTIER_VERSION = "efficiency-frontier-v1"
_MIN_SAMPLE_FOR_NON_PRELIMINARY = 30

_CASES = [
    {
        "case_id": "strong-index-tradeoffs",
        "question_prompt": "Explain the tradeoffs of adding a database index.",
        "transcript": (
            "An index speeds up lookups, however it adds write overhead and storage cost -- for example a "
            "heavily-indexed table slows down inserts because every write has to update each index too."
        ),
        "expected_keywords": ["index", "trade-off", "overhead"],
        "expected_quality": "strong",
    },
    {
        "case_id": "thin-index-answer",
        "question_prompt": "Explain the tradeoffs of adding a database index.",
        "transcript": "Indexes are good for speed.",
        "expected_keywords": ["index", "trade-off", "overhead"],
        "expected_quality": "weak",
    },
    {
        "case_id": "off-topic-answer",
        "question_prompt": "Explain the tradeoffs of adding a database index.",
        "transcript": "I really enjoy hiking on weekends and playing guitar with friends.",
        "expected_keywords": ["index", "trade-off", "overhead"],
        "expected_quality": "weak",
    },
    {
        "case_id": "strong-normalization",
        "question_prompt": "What is database normalization?",
        "transcript": (
            "Normalization structures tables to reduce redundancy -- for example splitting a table into "
            "smaller related tables linked by foreign keys, however over-normalizing can hurt read performance."
        ),
        "expected_keywords": ["redundancy", "foreign key", "normalization"],
        "expected_quality": "strong",
    },
]


@dataclass
class ConditionResult:
    condition: str
    accuracy: float
    mean_latency_ms: float
    mean_llm_calls: float
    cost_usd: float


def _is_accurate(confidence: float, expected_quality: str) -> bool:
    return (confidence >= 0.5) == (expected_quality == "strong")


def _result_row(run_id: uuid.UUID, case_id: str, variant: str, route_selected: str, confidence: float, latency_ms: float) -> EvaluationResult:
    return EvaluationResult(
        run_id=run_id,
        case_id=case_id,
        route_variant=variant,
        route_selected=route_selected,
        agents_invoked=[],
        confidence=confidence,
        agreement=None,
        latency_ms=round(latency_ms, 3),
        token_usage={},
        cost_usd=0.0,
        accuracy_label=None,
        failure=False,
        retry_count=0,
        human_review=route_selected == "human_review",
    )


def run_efficiency_frontier_evaluation(db: Session) -> dict:
    run = EvaluationRun(
        name="CARE efficiency frontier",
        dataset_name=EFFICIENCY_FRONTIER_VERSION,
        notes="Real latency and LLM-call cost proxy vs accuracy for single-agent, multi-agent, and CARE-adaptive routing.",
    )
    db.add(run)
    db.flush()

    accuracies: dict[str, list[bool]] = {"single_agent_fixed": [], "multi_agent_fixed": [], "care_adaptive": []}
    latencies: dict[str, list[float]] = {"single_agent_fixed": [], "multi_agent_fixed": [], "care_adaptive": []}
    calls: dict[str, list[int]] = {"single_agent_fixed": [], "multi_agent_fixed": [], "care_adaptive": []}
    rows: list[dict] = []

    for case in _CASES:
        tech_input = TechnicalInterviewInput(
            question_prompt=case["question_prompt"], transcript=case["transcript"], expected_keywords=case["expected_keywords"]
        )

        start = time.perf_counter()
        single_out, _latency = TechnicalAgent().safe_run(tech_input)
        latency_single = (time.perf_counter() - start) * 1000
        accuracies["single_agent_fixed"].append(_is_accurate(single_out.confidence, case["expected_quality"]))
        latencies["single_agent_fixed"].append(latency_single)
        calls["single_agent_fixed"].append(1)
        db.add(_result_row(run.id, case["case_id"], "single_agent_fixed", "single_agent", single_out.confidence, latency_single))

        start = time.perf_counter()
        multi_tech_out, _latency = TechnicalAgent().safe_run(tech_input)
        comm_out, _latency = CommunicationAgent().safe_run(CommunicationInput(transcript=case["transcript"]))
        multi_consensus = ConsensusAgent().run(
            ConsensusInput(
                votes=[
                    ConsensusVote(agent_name="technical", confidence=multi_tech_out.confidence),
                    ConsensusVote(agent_name="communication", confidence=comm_out.professional_communication_score),
                ]
            )
        )
        latency_multi = (time.perf_counter() - start) * 1000
        accuracies["multi_agent_fixed"].append(_is_accurate(multi_consensus.consensus_confidence, case["expected_quality"]))
        latencies["multi_agent_fixed"].append(latency_multi)
        calls["multi_agent_fixed"].append(3)
        db.add(
            _result_row(
                run.id, case["case_id"], "multi_agent_fixed", "multi_agent", multi_consensus.consensus_confidence, latency_multi
            )
        )

        start = time.perf_counter()
        care_tech_out, _latency = TechnicalAgent().safe_run(tech_input)
        factors = RoutingFactors(
            task_type="interview_evaluation",
            agent_confidence=care_tech_out.confidence,
            evidence_count=len(care_tech_out.matched_keywords),
            evidence_quality=0.7 if care_tech_out.matched_keywords else 0.3,
        )
        route = decide_route(factors)
        care_llm_calls = 1
        if route == "multi_agent":
            care_comm_out, _latency = CommunicationAgent().safe_run(CommunicationInput(transcript=case["transcript"]))
            care_consensus = ConsensusAgent().run(
                ConsensusInput(
                    votes=[
                        ConsensusVote(agent_name="technical", confidence=care_tech_out.confidence),
                        ConsensusVote(agent_name="communication", confidence=care_comm_out.professional_communication_score),
                    ]
                )
            )
            care_confidence = care_consensus.consensus_confidence
            care_llm_calls = 3
        else:
            care_confidence = care_tech_out.confidence
        latency_care = (time.perf_counter() - start) * 1000
        accuracies["care_adaptive"].append(_is_accurate(care_confidence, case["expected_quality"]))
        latencies["care_adaptive"].append(latency_care)
        calls["care_adaptive"].append(care_llm_calls)
        db.add(_result_row(run.id, case["case_id"], "care_adaptive", route, care_confidence, latency_care))

        rows.append(
            {
                "case_id": case["case_id"],
                "expected_quality": case["expected_quality"],
                "single_agent_confidence": single_out.confidence,
                "multi_agent_confidence": multi_consensus.consensus_confidence,
                "care_route": route,
                "care_confidence": care_confidence,
                "care_llm_calls": care_llm_calls,
            }
        )

    db.commit()

    frontier = [
        ConditionResult(
            condition=condition,
            accuracy=round(mean(1.0 if a else 0.0 for a in accuracies[condition]), 4),
            mean_latency_ms=round(mean(latencies[condition]), 3),
            mean_llm_calls=round(mean(calls[condition]), 2),
            cost_usd=0.0,
        )
        for condition in ("single_agent_fixed", "multi_agent_fixed", "care_adaptive")
    ]

    return {
        "run_id": str(run.id),
        "engine_version": EFFICIENCY_FRONTIER_VERSION,
        "case_count": len(_CASES),
        "frontier": [f.__dict__ for f in frontier],
        "rows": rows,
        "cost_note": (
            "Running on the deterministic fallback provider (no live API key configured in this environment) -- "
            "real dollar cost is $0 for all three conditions here. LLM/agent-call count is used as the honest "
            "cost proxy: it is exactly what would scale to real dollars the moment a live provider key is set."
        ),
        "preliminary": len(_CASES) < _MIN_SAMPLE_FOR_NON_PRELIMINARY,
    }
