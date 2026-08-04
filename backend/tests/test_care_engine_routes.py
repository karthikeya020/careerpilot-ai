"""Integration coverage for the *persisting* CARE engine (`run_care_task`),
as distinct from `tests/test_care_policy.py` (which only exercises the pure
`decide_route` function). Every one of the six `CareRoute` values is driven
through `run_care_task` here with deterministic, hand-authored step
executors, and each assertion reads the row back from the database rather
than trusting the in-memory return value -- proving `CareExecution`/
`AgentRun` are actually persisted with routing factors, confidence, evidence
citations, and a final status.

`graphrag_agent` and `multi_agent` are transitional steps by design (see
`engine._TERMINAL_ROUTES`): the loop always continues past them toward a
terminal route (`deterministic`, `single_agent`, `critic_reflection`, or
`human_review`). Proving they were "exercised" therefore means proving their
executor ran and left a durable trace (`retrieval_used`/`reflection_used`
flags, an `AgentRun` row, evidence citations) -- not that `CareExecution.route`
literally equals that value, which the design never produces for a
successful run within `MAX_STEPS`.
"""

import uuid

from app.care_engine.engine import AgentRunRecord, StepOutcome, run_care_task
from app.care_engine.schemas import RoutingFactors
from app.models.care import AgentRun, CareExecution


def _load_execution(db_session, execution_id):
    db_session.expire_all()
    return db_session.get(CareExecution, execution_id)


def test_deterministic_route_persists_with_no_agent_run(db_session):
    factors = RoutingFactors(task_type="score_aggregation", deterministic_eligible=True, task_risk="low")

    def _deterministic_step(f: RoutingFactors) -> StepOutcome:
        return StepOutcome(factors=f, output={"aggregated_score": 0.82}, evidence_ids=["evid-det-1"])

    execution, output = run_care_task(
        db_session,
        student_profile_id=None,
        task_type="score_aggregation",
        request_summary="Aggregate readiness components into an overall score.",
        factors=factors,
        executors={"deterministic": _deterministic_step},
    )

    assert execution.route == "deterministic"
    assert execution.final_status == "completed"
    assert execution.agent_runs == []  # a pure calculation never invokes an agent
    assert execution.confidence is not None
    assert execution.routing_factors["task_type"] == "score_aggregation"
    assert output["aggregated_score"] == 0.82

    persisted = _load_execution(db_session, execution.id)
    assert persisted is not None
    assert persisted.route == "deterministic"
    assert list(persisted.input_evidence_ids) == ["evid-det-1"]
    assert db_session.query(AgentRun).filter_by(care_execution_id=persisted.id).count() == 0


def test_single_agent_route_persists_execution_and_agent_run(db_session):
    factors = RoutingFactors(
        task_type="resume_insight", evidence_count=5, evidence_quality=0.9, agent_confidence=0.9
    )

    def _single_agent_step(f: RoutingFactors) -> StepOutcome:
        return StepOutcome(
            factors=f,
            output={"summary": "Strong resume evidence for Python and SQL."},
            evidence_ids=["evid-resume-1", "evid-resume-2"],
            agent_runs=[
                AgentRunRecord(
                    agent_name="resume_intelligence",
                    prompt_version="v1",
                    input_payload={"resume_id": "r-1"},
                    output_payload={"summary": "Strong resume evidence."},
                    confidence=0.9,
                    evidence_citations=["evid-resume-1", "evid-resume-2"],
                    inference_type="model_inference",
                )
            ],
        )

    execution, _ = run_care_task(
        db_session,
        student_profile_id=None,
        task_type="resume_insight",
        request_summary="Summarize resume strengths.",
        factors=factors,
        executors={"single_agent": _single_agent_step},
    )

    assert execution.route == "single_agent"
    assert execution.final_status == "completed"
    assert float(execution.confidence) == 0.9
    assert execution.routing_factors["evidence_count"] == 5

    persisted = _load_execution(db_session, execution.id)
    runs = db_session.query(AgentRun).filter_by(care_execution_id=persisted.id).all()
    assert len(runs) == 1
    assert runs[0].agent_name == "resume_intelligence"
    assert float(runs[0].confidence) == 0.9
    assert runs[0].evidence_citations == ["evid-resume-1", "evid-resume-2"]
    assert runs[0].inference_type == "model_inference"


def test_graphrag_agent_step_persists_retrieval_trace_before_terminal_route(db_session):
    factors = RoutingFactors(task_type="root_cause_analysis", evidence_count=0, evidence_quality=0.2)

    def _graphrag_step(f: RoutingFactors) -> StepOutcome:
        updated = f.model_copy(update={"retrieval_attempted": True, "retrieval_confidence": 0.85})
        return StepOutcome(
            factors=updated,
            output={"root_cause_path": ["Inner Join", "Joins", "Table Relationships", "Relational Model"]},
            evidence_ids=["evid-graph-question-14"],
            agent_runs=[
                AgentRunRecord(
                    agent_name="graphrag",
                    prompt_version="v1",
                    input_payload={"failed_question_id": "q-14"},
                    output_payload={"path_length": 4},
                    confidence=0.85,
                    evidence_citations=["evid-graph-question-14"],
                    inference_type="extracted_fact",
                )
            ],
        )

    def _single_agent_finalize(f: RoutingFactors) -> StepOutcome:
        return StepOutcome(factors=f, output={"mission": "Close the gap: Inner Join"})

    execution, output = run_care_task(
        db_session,
        student_profile_id=None,
        task_type="root_cause_analysis",
        request_summary="Diagnose why the student failed the INNER JOIN question.",
        factors=factors,
        executors={"graphrag_agent": _graphrag_step, "single_agent": _single_agent_finalize},
    )

    # Retrieval ran (evidence started insufficient, so graphrag_agent fired first);
    # confidence after retrieval (0.85) then clears the single-agent threshold,
    # so the terminal stored route is single_agent -- by design, not a bug.
    assert execution.retrieval_used is True
    assert execution.route == "single_agent"
    assert "graphrag" in execution.agents_invoked
    assert "evid-graph-question-14" in execution.input_evidence_ids
    assert output["mission"] == "Close the gap: Inner Join"

    persisted = _load_execution(db_session, execution.id)
    runs = db_session.query(AgentRun).filter_by(care_execution_id=persisted.id).all()
    assert any(r.agent_name == "graphrag" for r in runs)
    graphrag_run = next(r for r in runs if r.agent_name == "graphrag")
    assert float(graphrag_run.confidence) == 0.85
    assert graphrag_run.inference_type == "extracted_fact"


def test_multi_agent_step_persists_council_votes_before_terminal_route(db_session):
    factors = RoutingFactors(
        task_type="jd_match_review",
        evidence_count=5,
        evidence_quality=0.8,
        evidence_conflict=True,
        agent_confidence=0.6,
    )

    def _multi_agent_step(f: RoutingFactors) -> StepOutcome:
        updated = f.model_copy(update={"multi_agent_attempted": True, "agent_confidence": 0.85, "evidence_conflict": False})
        return StepOutcome(
            factors=updated,
            output={"consensus": "Role alignment is strong."},
            evidence_ids=["evid-jd-1"],
            agent_runs=[
                AgentRunRecord(
                    agent_name="resume_intelligence",
                    prompt_version="v1",
                    input_payload={},
                    output_payload={"vote": "aligned"},
                    confidence=0.8,
                    evidence_citations=["evid-jd-1"],
                    inference_type="model_inference",
                ),
                AgentRunRecord(
                    agent_name="ats_benchmark",
                    prompt_version="v1",
                    input_payload={},
                    output_payload={"vote": "aligned"},
                    confidence=0.9,
                    evidence_citations=["evid-jd-1"],
                    inference_type="deterministic_calculation",
                ),
                AgentRunRecord(
                    agent_name="consensus",
                    prompt_version="v1",
                    input_payload={},
                    output_payload={"agreement": 0.95},
                    confidence=0.85,
                    evidence_citations=["evid-jd-1"],
                    inference_type="model_inference",
                ),
            ],
        )

    def _single_agent_finalize(f: RoutingFactors) -> StepOutcome:
        return StepOutcome(factors=f, output={"finalized": True})

    execution, _ = run_care_task(
        db_session,
        student_profile_id=None,
        task_type="jd_match_review",
        request_summary="Resolve conflicting JD-match signals.",
        factors=factors,
        executors={"multi_agent": _multi_agent_step, "single_agent": _single_agent_finalize},
    )

    assert execution.route == "single_agent"  # council resolved the conflict; single_agent finalizes
    assert {"resume_intelligence", "ats_benchmark", "consensus"}.issubset(set(execution.agents_invoked))

    persisted = _load_execution(db_session, execution.id)
    runs = db_session.query(AgentRun).filter_by(care_execution_id=persisted.id).all()
    assert len(runs) == 3
    assert {r.agent_name for r in runs} == {"resume_intelligence", "ats_benchmark", "consensus"}


def test_critic_reflection_route_persists_as_terminal_status(db_session):
    factors = RoutingFactors(
        task_type="career_coach_synthesis",
        evidence_count=5,
        evidence_quality=0.8,
        agent_confidence=0.6,
        agent_disagreement=0.35,
    )

    def _critic_step(f: RoutingFactors) -> StepOutcome:
        return StepOutcome(
            factors=f,
            output={"flagged_claims": ["Overstated Python proficiency"]},
            evidence_ids=["evid-critic-1"],
            agent_runs=[
                AgentRunRecord(
                    agent_name="critic",
                    prompt_version="v1",
                    input_payload={},
                    output_payload={"issues_found": 1},
                    confidence=0.5,
                    evidence_citations=["evid-critic-1"],
                    inference_type="model_inference",
                )
            ],
        )

    execution, _ = run_care_task(
        db_session,
        student_profile_id=None,
        task_type="career_coach_synthesis",
        request_summary="Two agents disagree on career-coach synthesis; run critic pass.",
        factors=factors,
        executors={"critic_reflection": _critic_step},
    )

    assert execution.route == "critic_reflection"
    assert execution.reflection_used is True
    assert execution.final_status == "completed"
    assert execution.agreement is not None

    persisted = _load_execution(db_session, execution.id)
    runs = db_session.query(AgentRun).filter_by(care_execution_id=persisted.id).all()
    assert len(runs) == 1
    assert runs[0].agent_name == "critic"


def test_human_review_route_persists_with_default_executor(db_session):
    factors = RoutingFactors(
        task_type="ambiguous_case",
        evidence_count=5,
        evidence_quality=0.8,
        agent_confidence=0.3,
        retrieval_attempted=True,
        multi_agent_attempted=True,
    )

    execution, output = run_care_task(
        db_session,
        student_profile_id=None,
        task_type="ambiguous_case",
        request_summary="Confidence stayed low even after retrieval and a multi-agent pass.",
        factors=factors,
        executors={},  # no explicit executor -- must fall back to the built-in default
    )

    assert execution.route == "human_review"
    assert execution.requires_human_review is True
    assert execution.final_status == "completed"
    assert output["message"] == "Escalated for human review."

    persisted = _load_execution(db_session, execution.id)
    assert persisted.requires_human_review is True
    # A human-review escalation is not itself an agent call.
    assert db_session.query(AgentRun).filter_by(care_execution_id=persisted.id).count() == 0


def test_missing_executor_for_a_reachable_route_raises_instead_of_silently_skipping(db_session):
    import pytest

    factors = RoutingFactors(task_type="resume_insight", evidence_count=5, evidence_quality=0.9, agent_confidence=0.9)
    with pytest.raises(ValueError, match="No executor registered"):
        run_care_task(
            db_session,
            student_profile_id=None,
            task_type="resume_insight",
            request_summary="Missing executor should fail loudly, not silently no-op.",
            factors=factors,
            executors={},
        )


def test_care_execution_id_is_a_real_uuid(db_session):
    factors = RoutingFactors(task_type="score_aggregation", deterministic_eligible=True, task_risk="low")

    def _deterministic_step(f: RoutingFactors) -> StepOutcome:
        return StepOutcome(factors=f, output={})

    execution, _ = run_care_task(
        db_session,
        student_profile_id=None,
        task_type="score_aggregation",
        request_summary="id sanity check",
        factors=factors,
        executors={"deterministic": _deterministic_step},
    )
    assert isinstance(execution.id, uuid.UUID)
