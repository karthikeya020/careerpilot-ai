"""Confidence for keyword-rubric grading agents must be derived from real
signal (rubric richness, sub-score agreement) rather than a flat constant
tied only to which code path executed. See `app/agents/confidence.py`.
"""

from app.agents.assessment_agent import AssessmentAgent, AssessmentGradingInput
from app.agents.confidence import multi_score_confidence, rubric_confidence
from app.agents.hr_agent import HRAgent, HRInterviewInput
from app.agents.technical_agent import TechnicalAgent, TechnicalInterviewInput


def test_rubric_confidence_scales_with_keyword_richness():
    thin = rubric_confidence(keyword_count=1, is_fallback=True)
    rich = rubric_confidence(keyword_count=6, is_fallback=True)
    assert thin < rich


def test_rubric_confidence_no_keywords_is_low_regardless_of_path():
    assert rubric_confidence(keyword_count=0, is_fallback=True) == 0.3
    assert rubric_confidence(keyword_count=0, is_fallback=False) == 0.3


def test_rubric_confidence_live_path_never_below_fallback_path():
    for count in (0, 1, 3, 6, 10):
        assert rubric_confidence(keyword_count=count, is_fallback=False) >= rubric_confidence(
            keyword_count=count, is_fallback=True
        )


def test_multi_score_confidence_penalizes_disagreement():
    coherent = multi_score_confidence([0.8, 0.8, 0.8], keyword_count=6, is_fallback=False)
    scattered = multi_score_confidence([0.9, 0.1, 0.5], keyword_count=6, is_fallback=False)
    assert scattered < coherent


def test_assessment_agent_confidence_varies_with_rubric_richness_not_just_branch():
    agent = AssessmentAgent()
    thin = agent.run(
        AssessmentGradingInput(
            question_prompt="q",
            response_text="an answer",
            keywords=["answer"],
            sample_answer="ref",
        )
    )
    rich = agent.run(
        AssessmentGradingInput(
            question_prompt="q",
            response_text="an answer covering many things",
            keywords=["answer", "covering", "many", "things", "detail", "context"],
            sample_answer="ref",
        )
    )
    assert thin.confidence != rich.confidence


def test_technical_agent_confidence_penalizes_scattered_subscores():
    agent = TechnicalAgent()
    output = agent.run(
        TechnicalInterviewInput(
            question_prompt="Explain database indexing.",
            transcript="indexing because it helps, however trade-off exists",
            expected_keywords=["indexing", "trade-off", "b-tree", "query plan", "selectivity", "cardinality"],
            concept_name="Indexing",
        )
    )
    # Not a flat 0.55/0.85 -- computed from real keyword coverage + sub-score spread.
    assert output.confidence not in (0.55, 0.85)


def test_hr_agent_confidence_derived_from_prompt_richness():
    agent = HRAgent()
    output = agent.run(
        HRInterviewInput(
            question_prompt="Tell me about a time you resolved a conflict with a teammate under a tight deadline.",
            transcript="Situation was tense. I talked to them and we agreed on a plan and delivered on time.",
        )
    )
    assert output.confidence not in (0.55, 0.85)
