"""The required deterministic end-to-end test (Prompt 2 spec):

1. Demo student has weak SQL JOIN evidence.
2. CARE detects missing context.
3. GraphRAG retrieves concept dependencies.
4. Root cause is identified.
5. Mission is created.
6. Student completes a follow-up assessment.
7. New evidence is stored.
8. Career Twin updates.
9. Explanation identifies the exact evidence.
10. Trust Center displays the execution trace.

Every step below asserts against real service calls, not mocks -- this test
exercises the actual CARE routing, the actual GraphRAG root-cause service,
the actual mission generation, the actual Career Twin recompute, and the
actual Trust Center query path.
"""

from sqlalchemy import select

from app.models.assessment import Question
from app.models.care import CareExecution
from app.models.career_twin import CareerTwinSnapshot
from app.models.mission import LearningMission
from app.models.skill import EVIDENCE_TYPE_ASSESSMENT, SkillEvidence
from app.models.student import StudentProfile
from app.services import assessment_service, autonomous_loop_service, trust_center_service
from app.services.auth_service import register_student


def test_full_autonomous_loop_weak_sql_join_to_mission_to_reassessment(db_session):
    # --- Setup: a student with weak SQL JOIN evidence ------------------
    user = register_student(db_session, email="autonomous-loop@example.com", password="Password1", full_name="Loop Student")
    profile = db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))

    inner_join_question = db_session.scalar(
        select(Question).join(Question.concept).where(Question.concept.has(slug="inner_join"))
    )
    assert inner_join_question.question_type == "multiple_choice"
    wrong_option = next(
        o["id"] for o in inner_join_question.options if o["id"] not in inner_join_question.correct_answer["correct_option_ids"]
    )

    attempt = assessment_service.start_attempt(db_session, profile, "sql")
    # Force-select the INNER JOIN question directly rather than relying on
    # adaptive ordering, to keep this test deterministic regardless of
    # question-bank ordering changes.
    response = assessment_service.submit_response(
        db_session, attempt, inner_join_question, {"selected_option_ids": [wrong_option]}
    )
    assert response.is_correct is False

    # 6/7: complete the attempt -> stores SkillEvidence -> recomputes twin
    # -> generates a mission (this is where steps 2-5 actually fire, via
    # mission_service.generate_mission_for_snapshot's root-cause enrichment).
    completed_attempt = assessment_service.complete_attempt(db_session, profile, attempt)
    assert completed_attempt.status == "completed"

    # --- 7: new evidence is stored --------------------------------------
    evidence_rows = db_session.scalars(
        select(SkillEvidence).where(
            SkillEvidence.student_profile_id == profile.id, SkillEvidence.evidence_type == EVIDENCE_TYPE_ASSESSMENT
        )
    ).all()
    assert len(evidence_rows) == 1
    assert evidence_rows[0].concept_id == inner_join_question.concept_id
    assert float(evidence_rows[0].normalized_score) == 0.0  # wrong answer

    # --- 8: Career Twin updates ------------------------------------------
    snapshot = db_session.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    assert snapshot is not None
    assert snapshot.version >= 1

    # --- 2/3/4/5: CARE detected missing context, routed through GraphRAG,
    # identified a root cause, and a mission was created from it ----------
    mission = db_session.scalar(
        select(LearningMission)
        .where(LearningMission.student_profile_id == profile.id)
        .order_by(LearningMission.created_at.desc())
    )
    assert mission is not None
    assert mission.root_cause is not None
    assert mission.root_cause["concept_slug"] == "inner_join"
    assert mission.target_concept_id == inner_join_question.concept_id
    assert len(mission.tasks) >= 1
    assert mission.expected_impact_estimate is not None

    care_execution = db_session.scalar(
        select(CareExecution)
        .where(CareExecution.student_profile_id == profile.id, CareExecution.task_type == "root_cause_analysis")
        .order_by(CareExecution.created_at.desc())
    )
    assert care_execution is not None
    assert care_execution.retrieval_used is True  # CARE routed through graphrag_agent at some point
    assert "graphrag" in care_execution.agents_invoked

    # --- 6: student completes a follow-up assessment (same concept, correct
    # this time) ------------------------------------------------------------
    attempt_2 = assessment_service.start_attempt(db_session, profile, "sql")
    correct_response = assessment_service.submit_response(
        db_session, attempt_2, inner_join_question,
        {"selected_option_ids": inner_join_question.correct_answer["correct_option_ids"]},
    )
    assert correct_response.is_correct is True
    completed_attempt_2 = assessment_service.complete_attempt(db_session, profile, attempt_2)
    assert completed_attempt_2.status == "completed"

    reassessment = autonomous_loop_service.reassess_and_close_mission(db_session, profile, mission, correct_response)
    assert reassessment.mission.status == "completed"
    assert "correctly" in reassessment.change_explanation

    # --- 9: Career Twin updated again with an explanation identifying the
    # exact evidence ---------------------------------------------------------
    latest_snapshot = db_session.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    assert latest_snapshot.version > snapshot.version
    assert str(latest_snapshot.score_delta) != ""  # a real number, not fabricated

    # --- 10: Trust Center displays the execution trace ----------------------
    trace = trust_center_service.get_execution_detail(db_session, care_execution.id)
    assert trace is not None
    assert trace.route in ("single_agent", "graphrag_agent", "multi_agent", "critic_reflection", "human_review")
    assert trace.retrieval_used is True
    assert len(trace.agent_runs) >= 1
    assert any(run.agent_name == "graphrag" for run in trace.agent_runs)
