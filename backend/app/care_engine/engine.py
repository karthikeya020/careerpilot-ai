"""CARE orchestration: runs the decide_route loop against caller-supplied
step executors and persists the full decision as a `CareExecution` row (plus
one `AgentRun` row per agent invocation) -- this is the Trust Center's data
source. See app/care_engine/policy.py for the routing rules themselves.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast

from sqlalchemy.orm import Session

from app.care_engine.policy import POLICY_VERSION, decide_route, reasoning_summary_for_route
from app.care_engine.schemas import CareResult, CareRoute, RoutingFactors
from app.models.care import CARE_STATUS_COMPLETED, AgentRun, CareExecution

MAX_STEPS = 5
_TERMINAL_ROUTES: set[CareRoute] = {"deterministic", "single_agent", "critic_reflection", "human_review"}


@dataclass
class AgentRunRecord:
    agent_name: str
    prompt_version: str
    input_payload: dict
    output_payload: dict
    confidence: float
    evidence_citations: list[str]
    inference_type: str
    latency_ms: float = 0.0


@dataclass
class StepOutcome:
    factors: RoutingFactors
    output: dict = field(default_factory=dict)
    evidence_ids: list[str] = field(default_factory=list)
    agent_runs: list[AgentRunRecord] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: float = 0.0


StepExecutor = Callable[[RoutingFactors], StepOutcome]


def _default_human_review_step(factors: RoutingFactors) -> StepOutcome:
    return StepOutcome(factors=factors, output={"message": "Escalated for human review."})


def run_care_task(
    db: Session,
    student_profile_id: uuid.UUID | None,
    task_type: str,
    request_summary: str,
    factors: RoutingFactors,
    executors: dict[CareRoute, StepExecutor],
    input_evidence_ids: list[str] | None = None,
) -> tuple[CareExecution, dict]:
    """Returns the persisted CareExecution row plus the final step's raw
    output dict (e.g. a root-cause path, a mission draft) for the immediate
    caller -- per-agent outputs are also durably stored on
    `execution.agent_runs[i].output_payload` for the Trust Center."""
    route_path: list[CareRoute] = []
    agents_invoked: list[str] = []
    all_evidence_ids = list(input_evidence_ids or [])
    all_agent_runs: list[AgentRunRecord] = []
    total_cost = 0.0
    total_latency = 0.0
    retrieval_used = False
    reflection_used = False
    final_output: dict = {}

    current_factors = factors
    route: CareRoute = "single_agent"
    for _ in range(MAX_STEPS):
        route = decide_route(current_factors)
        route_path.append(route)

        executor = executors.get(route, _default_human_review_step if route == "human_review" else None)
        if executor is None:
            raise ValueError(f"No executor registered for CARE route {route!r} (task_type={task_type!r})")

        outcome = executor(current_factors)
        current_factors = outcome.factors
        all_evidence_ids.extend(outcome.evidence_ids)
        all_agent_runs.extend(outcome.agent_runs)
        agents_invoked.extend(r.agent_name for r in outcome.agent_runs)
        total_cost += outcome.cost_usd
        total_latency += outcome.latency_ms
        final_output = outcome.output

        if route == "graphrag_agent":
            retrieval_used = True
            continue
        if route == "multi_agent":
            continue
        if route == "critic_reflection":
            reflection_used = True
            break
        break

    final_confidence = current_factors.agent_confidence
    if final_confidence is None:
        final_confidence = current_factors.retrieval_confidence or 0.0

    agreement = None
    if current_factors.agent_disagreement is not None:
        agreement = round(1.0 - current_factors.agent_disagreement, 4)

    requires_human_review = route == "human_review"
    reasoning_summary = reasoning_summary_for_route(route, current_factors)

    execution = CareExecution(
        student_profile_id=student_profile_id,
        task_type=task_type,
        request_summary=request_summary,
        input_evidence_ids=list(dict.fromkeys(all_evidence_ids)),
        routing_factors=factors.model_dump(),
        route=route,
        agents_invoked=list(dict.fromkeys(agents_invoked)),
        retrieval_used=retrieval_used,
        reflection_used=reflection_used,
        confidence=round(final_confidence, 4),
        agreement=agreement,
        reasoning_summary=reasoning_summary,
        cost_usd=round(total_cost, 6),
        latency_ms=round(total_latency, 3),
        final_status=CARE_STATUS_COMPLETED,
        requires_human_review=requires_human_review,
        policy_version=POLICY_VERSION,
    )
    for run in all_agent_runs:
        execution.agent_runs.append(
            AgentRun(
                agent_name=run.agent_name,
                prompt_version=run.prompt_version,
                input_payload=run.input_payload,
                output_payload=run.output_payload,
                confidence=round(run.confidence, 4),
                evidence_citations=run.evidence_citations,
                inference_type=run.inference_type,
                latency_ms=round(run.latency_ms, 3),
            )
        )

    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution, final_output


def to_care_result(execution: CareExecution, output: dict | None = None) -> CareResult:
    return CareResult(
        route=cast(CareRoute, execution.route),
        confidence=float(execution.confidence),
        evidence_ids=[str(e) for e in execution.input_evidence_ids],
        agents_invoked=execution.agents_invoked,
        agreement=float(execution.agreement) if execution.agreement is not None else None,
        reasoning_summary=execution.reasoning_summary,
        requires_human_review=execution.requires_human_review,
        retrieval_used=execution.retrieval_used,
        reflection_used=execution.reflection_used,
        cost_usd=float(execution.cost_usd),
        latency_ms=float(execution.latency_ms),
        output=output or {},
    )
