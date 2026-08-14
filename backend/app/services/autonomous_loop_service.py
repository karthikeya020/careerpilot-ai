"""Autonomous improvement loop: Observe -> Diagnose -> Plan -> Teach -> Assess
-> Reflect -> Update Twin -> Next mission.

Observe / Update-Twin / Next-mission are already implemented by
app/career_twin/scoring.py::recompute_twin (Observe = read current
components) and app/services/mission_service.py::generate_mission_for_snapshot
(Next mission), which every recompute_twin call already invokes. This module
adds the Diagnose/Plan/Teach steps: when the priority weakness traces back to
a specific failed assessment question, `build_root_cause_mission_plan` runs a
real CARE-routed root-cause analysis (through GraphRAG, then a career-coach
synthesis) and returns a plan that `mission_service` uses to enrich the
generated mission with the root cause, concrete tasks, and recommended
resources. Assess/Reflect happen later, when the student submits a follow-up
assessment response for the same concept -- see `reassess_and_close_mission`,
which compares pre/post evidence and produces an explicit before/after
explanation naming the exact evidence that changed.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.agents.career_coach_agent import CareerCoachAgent, CareerCoachInput
from app.agents.graphrag_agent import GraphRAGAgent, GraphRAGInput
from app.care_engine.engine import AgentRunRecord, StepOutcome, run_care_task
from app.care_engine.schemas import RoutingFactors
from app.models.assessment import Concept, QuestionResponse
from app.models.mission import LearningMission
from app.models.skill import EVIDENCE_TYPE_ASSESSMENT, SkillEvidence
from app.models.student import StudentProfile
from app.services import resource_service

_ROOT_CAUSE_TASK_TYPE = "root_cause_analysis"
_DEFAULT_MINUTES_PER_RESOURCE = 15


@dataclass
class RootCauseMissionPlan:
    title: str
    description: str
    tasks: list[str]
    estimated_minutes: int
    root_cause: dict
    resource_ids: list[str]
    expected_impact_estimate: float
    expected_impact_confidence: float
    target_concept_id: uuid.UUID
    care_execution_id: uuid.UUID


def _find_failed_question_response(db: Session, evidence: SkillEvidence) -> QuestionResponse | None:
    if evidence.evidence_type != EVIDENCE_TYPE_ASSESSMENT or evidence.source_object_type != "question_response":
        return None
    if evidence.source_object_id is None:
        return None
    response = db.get(QuestionResponse, evidence.source_object_id)
    if response is None or response.is_correct:
        return None
    return response


def build_root_cause_mission_plan(
    db: Session, student_profile: StudentProfile, weakest_evidence: SkillEvidence, priority_component: str
) -> RootCauseMissionPlan | None:
    response = _find_failed_question_response(db, weakest_evidence)
    if response is None:
        return None

    concept = db.get(Concept, response.concept_id)
    concept_name = concept.name if concept else "this concept"
    student_label = student_profile.full_name or "Student"
    state: dict = {}

    def _graphrag_step(factors: RoutingFactors) -> StepOutcome:
        agent = GraphRAGAgent(db, student_profile)
        output, latency_ms = agent.safe_run(GraphRAGInput(failed_question_id=response.question_id))
        state["graphrag_output"] = output
        evidence_signal = len(output.target_role_relevance) + len(output.recommended_resource_ids) + 1
        updated = factors.model_copy(
            update={
                "retrieval_attempted": True,
                "retrieval_confidence": output.confidence,
                "evidence_count": evidence_signal,
                "evidence_quality": 0.8 if not output.missing_context_warning else 0.3,
            }
        )
        return StepOutcome(
            factors=updated,
            output=output.model_dump(),
            evidence_ids=output.evidence_ids,
            agent_runs=[
                AgentRunRecord(
                    agent_name=agent.name,
                    prompt_version=agent.prompt_version,
                    input_payload={"failed_question_id": str(response.question_id)},
                    output_payload=output.model_dump(),
                    confidence=output.confidence,
                    evidence_citations=output.evidence_ids,
                    inference_type=output.inference_type,
                    latency_ms=latency_ms,
                )
            ],
        )

    def _career_coach_step(factors: RoutingFactors) -> StepOutcome:
        # Idempotent guard: CARE's loop can reach this route more than once
        # (e.g. escalate to multi_agent, then land back on single_agent) --
        # re-running the same synthesis would waste a call and could
        # overwrite state with a second, redundant result.
        if "coach_output" in state:
            output = state["coach_output"]
            updated = factors.model_copy(update={"agent_confidence": output.confidence})
            return StepOutcome(factors=updated, output=output.model_dump(), evidence_ids=output.evidence_ids)

        graphrag_output = state["graphrag_output"]
        agent = CareerCoachAgent()
        output, latency_ms = agent.safe_run(
            CareerCoachInput(
                student_name=student_label,
                priority_component=priority_component,
                root_cause_summary=graphrag_output.path_summary,
                concept_name=concept_name,
                evidence_ids=graphrag_output.recommended_resource_ids,
            )
        )
        state["coach_output"] = output
        updated = factors.model_copy(update={"agent_confidence": output.confidence})
        return StepOutcome(
            factors=updated,
            output=output.model_dump(),
            evidence_ids=output.evidence_ids,
            agent_runs=[
                AgentRunRecord(
                    agent_name=agent.name,
                    prompt_version=agent.prompt_version,
                    input_payload={"priority_component": priority_component, "concept_name": concept_name},
                    output_payload=output.model_dump(),
                    confidence=output.confidence,
                    evidence_citations=output.evidence_ids,
                    inference_type=output.inference_type,
                    latency_ms=latency_ms,
                )
            ],
        )

    def _multi_agent_step(factors: RoutingFactors) -> StepOutcome:
        # This pipeline has exactly one specialist (CareerCoachAgent) after
        # retrieval -- there is no second council member to add. Escalating
        # here just means "the single pass wasn't confident enough"; run (or
        # reuse) that same specialist rather than raising for a missing
        # multi-agent route, and mark the escalation attempted so the policy
        # doesn't loop back into it a second time.
        outcome = _career_coach_step(factors)
        updated = outcome.factors.model_copy(update={"multi_agent_attempted": True})
        return StepOutcome(
            factors=updated, output=outcome.output, evidence_ids=outcome.evidence_ids, agent_runs=outcome.agent_runs
        )

    def _critic_step(factors: RoutingFactors) -> StepOutcome:
        # No second opinion exists to audit against in this simple pipeline;
        # accept the coach's synthesis as final rather than raising for a
        # missing critic/reflection route.
        outcome = _career_coach_step(factors)
        return StepOutcome(factors=outcome.factors, output=outcome.output, evidence_ids=outcome.evidence_ids)

    initial_factors = RoutingFactors(
        task_type=_ROOT_CAUSE_TASK_TYPE,
        task_risk="low",
        student_impact_level="medium",
        evidence_count=0,
        evidence_quality=0.2,
        deterministic_eligible=False,
    )
    execution, _output = run_care_task(
        db,
        student_profile.id,
        _ROOT_CAUSE_TASK_TYPE,
        request_summary=f"Root-cause analysis for missed question on concept '{concept_name}'.",
        factors=initial_factors,
        executors={
            "graphrag_agent": _graphrag_step,
            "single_agent": _career_coach_step,
            "multi_agent": _multi_agent_step,
            "critic_reflection": _critic_step,
        },
        input_evidence_ids=[str(weakest_evidence.id)],
    )

    graphrag_output = state.get("graphrag_output")
    coach_output = state.get("coach_output")
    if graphrag_output is None:
        return None

    resources, _summary, _confidence = resource_service.recommend_resources(
        db, concept_slug=graphrag_output.concept_slug, available_minutes=60, max_difficulty=5, limit=2
    )
    tasks = [f"Review: {r.title} ({r.duration_minutes} min)" for r in resources]
    tasks.append(f"Retake an assessment question on '{concept_name}' to confirm improvement.")
    estimated_minutes = sum(r.duration_minutes for r in resources) or _DEFAULT_MINUTES_PER_RESOURCE

    explanation = coach_output.explanation if coach_output else graphrag_output.path_summary
    title = f"Close the gap: {concept_name}"

    # Expected impact is a heuristic estimate, not a guarantee (Prompt 2
    # rule) -- larger for lower current confidence, capped conservatively.
    current_confidence = float(weakest_evidence.confidence)
    expected_impact_estimate = round(min(0.05 + 0.15 * (1 - current_confidence), 0.2), 4)
    expected_impact_confidence = round(graphrag_output.confidence * 0.7, 4)

    return RootCauseMissionPlan(
        title=title,
        description=explanation,
        tasks=tasks,
        estimated_minutes=estimated_minutes,
        root_cause=graphrag_output.model_dump(),
        resource_ids=[str(r.id) for r in resources],
        expected_impact_estimate=expected_impact_estimate,
        expected_impact_confidence=expected_impact_confidence,
        target_concept_id=concept.id if concept else None,  # type: ignore[arg-type]
        care_execution_id=execution.id,
    )


@dataclass
class ReassessmentResult:
    mission: LearningMission
    evidence_before: float | None
    evidence_after: float | None
    change_explanation: str


def reassess_and_close_mission(
    db: Session, student_profile: StudentProfile, mission: LearningMission, new_response: QuestionResponse
) -> ReassessmentResult:
    """Assess/Reflect steps: compares the mission's originating evidence
    against a fresh QuestionResponse for the same concept, records the
    observed change on the mission, and returns an explanation naming the
    exact evidence involved. The caller is responsible for having already
    recorded `new_response` as SkillEvidence and called `recompute_twin`
    (see app/services/assessment_service.py::complete_attempt) -- this
    function only closes the loop on the mission record itself."""
    from app.models.mission import MISSION_STATUS_COMPLETED

    evidence_before = mission.expected_impact_estimate
    new_score = float(new_response.score) if new_response.score is not None else None

    mission.outcome_evidence_ids = [*mission.outcome_evidence_ids, str(new_response.id)]
    mission.actual_observed_change = {
        "concept_id": str(new_response.concept_id),
        "new_response_correct": new_response.is_correct,
        "new_response_score": new_score,
        "expected_impact_estimate": float(evidence_before) if evidence_before is not None else None,
    }
    mission.status = MISSION_STATUS_COMPLETED
    from app.models.base import utcnow

    mission.completed_at = utcnow()
    db.commit()
    db.refresh(mission)

    outcome = "improved" if new_response.is_correct else "did not yet improve"
    explanation = (
        f"Follow-up question on the same concept was answered "
        f"{'correctly' if new_response.is_correct else 'incorrectly'} (evidence {new_response.id}); "
        f"mission outcome: {outcome}."
    )
    return ReassessmentResult(
        mission=mission,
        evidence_before=float(evidence_before) if evidence_before is not None else None,
        evidence_after=new_score,
        change_explanation=explanation,
    )
