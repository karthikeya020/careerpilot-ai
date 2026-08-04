"""Unit tests for the Interview Arena's specialist agents. Each test drives
the real `run()` against the deterministic fake provider path, following the
same pattern as test_agents.py.
"""

from app.agents.communication_agent import CommunicationAgent, CommunicationInput
from app.agents.hr_agent import HRAgent, HRInterviewInput
from app.agents.jd_alignment_agent import JDAlignmentAgent, JDAlignmentInput
from app.agents.resume_evidence_agent import ResumeEvidenceAgent, ResumeEvidenceCheckInput
from app.agents.supervisor_agent import SupervisorAgent, SupervisorInput
from app.agents.technical_agent import TechnicalAgent, TechnicalInterviewInput
from app.models.interview import (
    EVIDENCE_CHECK_INSUFFICIENT,
    EVIDENCE_CHECK_NOT_SUPPORTED,
    EVIDENCE_CHECK_PARTIAL,
    EVIDENCE_CHECK_SUPPORTED,
)


def test_communication_agent_counts_words_and_filler():
    agent = CommunicationAgent()
    transcript = "Um, so I basically led the project. You know, it went well and, um, we shipped on time."
    output = agent.run(CommunicationInput(transcript=transcript))
    assert output.word_count > 0
    assert output.filler_word_count >= 2
    assert 0.0 <= output.filler_ratio <= 1.0
    assert output.inference_type == "deterministic_calculation"


def test_communication_agent_empty_transcript_is_zero_confidence():
    agent = CommunicationAgent()
    output = agent.run(CommunicationInput(transcript="   "))
    assert output.confidence == 0.0
    assert output.word_count == 0


def test_communication_agent_detects_star_structure():
    agent = CommunicationAgent()
    transcript = (
        "When I was working on my capstone project, I needed to fix a failing pipeline. "
        "So I decided to rewrite the ETL job. As a result, the failure rate dropped to zero."
    )
    output = agent.run(CommunicationInput(transcript=transcript, check_star_structure=True))
    assert "situation" in output.star_components_found
    assert "action" in output.star_components_found
    assert "result" in output.star_components_found


def test_communication_agent_speaking_rate_from_duration():
    agent = CommunicationAgent()
    output = agent.run(CommunicationInput(transcript=" ".join(["word"] * 60), audio_duration_seconds=30.0))
    assert output.speaking_rate_wpm == 120.0


def test_technical_agent_scores_keyword_overlap():
    agent = TechnicalAgent()
    output = agent.run(
        TechnicalInterviewInput(
            question_prompt="Explain INNER JOIN vs LEFT JOIN.",
            transcript="An inner join returns only matched rows, a left join keeps unmatched rows from the left table as null.",
            expected_keywords=["inner join", "left join", "match", "unmatched", "null"],
            concept_name="Inner Join",
        )
    )
    assert output.relevance_score > 0.5
    assert output.matched_keywords
    assert output.inference_type == "deterministic_calculation"


def test_technical_agent_low_score_for_off_topic_answer():
    agent = TechnicalAgent()
    output = agent.run(
        TechnicalInterviewInput(
            question_prompt="Explain INNER JOIN vs LEFT JOIN.",
            transcript="I really enjoy hiking on weekends.",
            expected_keywords=["inner join", "left join", "match", "unmatched", "null"],
        )
    )
    assert output.relevance_score == 0.0
    assert output.correctness_score == 0.0


def test_hr_agent_detects_star_structure_and_specificity():
    agent = HRAgent()
    output = agent.run(
        HRInterviewInput(
            question_prompt="Tell me about a time you led a project under a tight deadline.",
            transcript=(
                "When I was leading a project, I needed to ship a feature in two weeks. "
                "So I decided to split the work and pair-program with a teammate. "
                "As a result, we shipped 3 days early and reduced bugs by 40%."
            ),
        )
    )
    assert len(output.star_components_found) >= 2
    assert output.evidence_score == 1.0


def test_resume_evidence_agent_no_resume_is_insufficient():
    agent = ResumeEvidenceAgent()
    output = agent.run(ResumeEvidenceCheckInput(claim_text="I led the backend rewrite project.", resume_text=""))
    assert output.classification == EVIDENCE_CHECK_INSUFFICIENT


def test_resume_evidence_agent_supported_claim():
    agent = ResumeEvidenceAgent()
    resume_text = "Led the backend rewrite project using Python and PostgreSQL, improving latency by 30%."
    output = agent.run(ResumeEvidenceCheckInput(claim_text="I led the backend rewrite project.", resume_text=resume_text))
    assert output.classification == EVIDENCE_CHECK_SUPPORTED
    assert "backend" in output.matched_terms or "rewrite" in output.matched_terms


def test_resume_evidence_agent_not_supported_claim():
    agent = ResumeEvidenceAgent()
    resume_text = "Worked on a mobile app using Swift and built onboarding flows."
    output = agent.run(
        ResumeEvidenceCheckInput(claim_text="I managed a distributed Kubernetes cluster deployment.", resume_text=resume_text)
    )
    assert output.classification in (EVIDENCE_CHECK_NOT_SUPPORTED, EVIDENCE_CHECK_PARTIAL)


def test_jd_alignment_agent_no_jd_warns_missing_context():
    agent = JDAlignmentAgent()
    output = agent.run(JDAlignmentInput(transcript="I have experience with SQL and Python.", job_description_text=""))
    assert output.missing_context_warning is True
    assert output.role_alignment_score == 0.0


def test_jd_alignment_agent_scores_overlap():
    agent = JDAlignmentAgent()
    jd_text = "We are looking for a Data Analyst with strong SQL skills and experience with dashboards and reporting."
    output = agent.run(
        JDAlignmentInput(transcript="I have built dashboards and reporting pipelines using SQL extensively.", job_description_text=jd_text)
    )
    assert output.role_alignment_score > 0
    assert output.missing_context_warning is False


def test_supervisor_agent_dispatches_interview_evaluation_roster():
    agent = SupervisorAgent()
    output = agent.run(SupervisorInput(task_type="interview_evaluation"))
    assert "hr" in output.selected_agents
    assert "technical" in output.selected_agents
    assert "resume_evidence" in output.selected_agents
    assert "critic" in output.selected_agents
    assert "consensus" in output.selected_agents
