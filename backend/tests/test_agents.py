"""Schema and behavior tests for all 10 specialist agents. Each test
exercises the agent's real `run()` (not a mock) against the deterministic
fake provider path, and checks the typed output plus the `safe_run` failure
behavior where relevant.
"""

import uuid

from app.agents.assessment_agent import AssessmentAgent, AssessmentGradingInput
from app.agents.ats_benchmark_agent import ATSBenchmarkAgent, ATSBenchmarkInput
from app.agents.career_coach_agent import CareerCoachAgent, CareerCoachInput
from app.agents.consensus_agent import ConsensusAgent, ConsensusInput, ConsensusVote
from app.agents.critic_agent import CriticAgent, CriticClaim, CriticInput
from app.agents.graphrag_agent import GraphRAGAgent, GraphRAGInput
from app.agents.memory_agent import MemoryAgent, MemoryInput
from app.agents.resource_recommendation_agent import (
    ResourceRecommendationAgent,
    ResourceRecommendationInput,
)
from app.agents.resume_intelligence_agent import ResumeIntelligenceAgent, ResumeIntelligenceInput
from app.agents.supervisor_agent import SupervisorAgent, SupervisorInput


def test_supervisor_agent_dispatches_known_task_type():
    agent = SupervisorAgent()
    output = agent.run(SupervisorInput(task_type="root_cause_analysis"))
    assert output.selected_agents == ["graphrag"]
    assert output.inference_type == "deterministic_calculation"
    assert output.status == "completed"


def test_supervisor_agent_unknown_task_type_returns_zero_confidence():
    agent = SupervisorAgent()
    output = agent.run(SupervisorInput(task_type="not_a_real_task"))
    assert output.selected_agents == []
    assert output.confidence == 0.0


def test_resume_intelligence_agent_produces_strengths_and_gaps():
    agent = ResumeIntelligenceAgent()
    output = agent.run(
        ResumeIntelligenceInput(
            student_name="Ada",
            skills_found=["Python", "SQL", "FastAPI"],
            sections_found=["Skills", "Experience"],
            evidence_ids=["e1"],
        )
    )
    assert len(output.strengths) == 3
    assert any("projects" in g.lower() for g in output.gaps)
    assert output.confidence > 0
    assert output.inference_type == "deterministic_calculation"


def test_ats_benchmark_agent_computes_weighted_score():
    agent = ATSBenchmarkAgent()
    output = agent.run(
        ATSBenchmarkInput(matched_skills=["Python", "SQL"], partial_skills=["Docker"], missing_skills=["Kubernetes"])
    )
    # (2 + 0.5) / 4 = 0.625
    assert output.ats_score == 0.625
    assert output.missing_keywords == ["Kubernetes"]


def test_ats_benchmark_agent_handles_no_requirements():
    agent = ATSBenchmarkAgent()
    output = agent.run(ATSBenchmarkInput(matched_skills=[], partial_skills=[], missing_skills=[]))
    assert output.confidence == 0.0
    assert output.ats_score == 0.0


def test_assessment_agent_grades_free_form_answer_by_keyword_overlap():
    agent = AssessmentAgent()
    output = agent.run(
        AssessmentGradingInput(
            question_prompt="Explain INNER JOIN vs LEFT JOIN.",
            response_text="An inner join only returns matched rows, a left join keeps unmatched left rows with null.",
            keywords=["inner join", "left join", "unmatched", "null"],
            sample_answer="Inner join drops unmatched rows; left join keeps them with NULLs.",
        )
    )
    assert output.score > 0.5
    assert output.is_correct is True
    assert output.inference_type == "deterministic_calculation"


def test_assessment_agent_low_overlap_scores_low():
    agent = AssessmentAgent()
    output = agent.run(
        AssessmentGradingInput(
            question_prompt="Explain INNER JOIN vs LEFT JOIN.",
            response_text="I am not sure.",
            keywords=["inner join", "left join", "unmatched", "null"],
            sample_answer="Inner join drops unmatched rows; left join keeps them with NULLs.",
        )
    )
    assert output.score == 0.0
    assert output.is_correct is False


def test_critic_agent_flags_unsupported_high_confidence_claim():
    agent = CriticAgent()
    output = agent.run(
        CriticInput(
            claims=[
                CriticClaim(agent_name="resume_intelligence", confidence=0.9, evidence_ids=[]),
                CriticClaim(agent_name="ats_benchmark", confidence=0.8, evidence_ids=["e1", "e2"]),
            ]
        )
    )
    assert output.verdict == "flag"
    assert len(output.issues) == 1
    assert "resume_intelligence" in output.issues[0]
    assert output.adjusted_confidence < 0.85


def test_critic_agent_passes_when_all_claims_have_evidence():
    agent = CriticAgent()
    output = agent.run(
        CriticInput(claims=[CriticClaim(agent_name="ats_benchmark", confidence=0.8, evidence_ids=["e1"])])
    )
    assert output.verdict == "pass"
    assert output.issues == []


def test_consensus_agent_flags_high_disagreement():
    agent = ConsensusAgent()
    output = agent.run(
        ConsensusInput(
            votes=[
                ConsensusVote(agent_name="a", confidence=0.9),
                ConsensusVote(agent_name="b", confidence=0.2),
            ]
        )
    )
    assert output.flagged is True
    assert output.disagreement > 0.20


def test_consensus_agent_no_disagreement_when_votes_agree():
    agent = ConsensusAgent()
    output = agent.run(
        ConsensusInput(
            votes=[
                ConsensusVote(agent_name="a", confidence=0.85),
                ConsensusVote(agent_name="b", confidence=0.86),
            ]
        )
    )
    assert output.flagged is False


def test_career_coach_agent_produces_explanation_referencing_inputs():
    agent = CareerCoachAgent()
    output = agent.run(
        CareerCoachInput(
            student_name="Aanya",
            priority_component="technical_readiness",
            root_cause_summary="Weak INNER JOIN evidence traced to missing table-relationships understanding.",
            concept_name="Inner Join",
        )
    )
    assert "Aanya" in output.explanation
    assert output.recommended_focus == "Inner Join"


def test_memory_agent_returns_empty_history_for_new_student(db_session):
    agent = MemoryAgent(db_session)
    output = agent.run(MemoryInput(student_profile_id=uuid.uuid4()))
    assert output.recent_mission_titles == []
    assert output.recent_evidence_types == []
    assert output.confidence == 1.0


def test_resource_recommendation_agent_ranks_by_quality(db_session):
    agent = ResourceRecommendationAgent(db_session)
    output = agent.run(ResourceRecommendationInput(concept_slug="inner_join", available_minutes=60, max_difficulty=5))
    assert len(output.resource_ids) >= 1
    assert output.inference_type == "deterministic_calculation"


def test_resource_recommendation_agent_unknown_concept_returns_zero_confidence(db_session):
    agent = ResourceRecommendationAgent(db_session)
    output = agent.run(ResourceRecommendationInput(concept_slug="not_a_real_concept"))
    assert output.confidence == 0.0
    assert output.resource_ids == []


def test_graphrag_agent_wraps_root_cause_analysis(db_session):
    from sqlalchemy import select

    from app.models.assessment import Question
    from app.models.student import StudentProfile
    from app.services.auth_service import register_student

    user = register_student(db_session, email="agent-graphrag@example.com", password="Password1", full_name="Test")
    profile = db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    question = db_session.scalar(
        select(Question).join(Question.concept).where(Question.concept.has(slug="inner_join"))
    )

    agent = GraphRAGAgent(db_session, profile)
    output = agent.run(GraphRAGInput(failed_question_id=question.id))
    assert output.concept_slug == "inner_join"
    assert output.inference_type == "extracted_fact"
    assert output.missing_context_warning is False


def test_safe_run_never_raises_on_agent_failure():
    agent = ResourceRecommendationAgent(db=None)  # will raise inside run() when querying
    output, latency_ms = agent.safe_run(ResourceRecommendationInput(concept_slug="inner_join"))
    assert output.status == "failed"
    assert output.confidence == 0.0
    assert latency_ms >= 0
