"""GraphRAG tests. Root-cause analysis must produce the identical path
whether Neo4j is reachable or not -- these tests exercise both the real
Neo4j path (skipped if the dockerized instance from docker-compose.yml
isn't reachable at bolt://localhost:7687) and the always-available
relational fallback, matching PHASE_2_EXECUTION_PLAN §2.3.
"""

import uuid

import pytest
from sqlalchemy import select

import app.graphrag.service as graphrag_service
from app.graphrag.neo4j_client import is_graph_available
from app.graphrag.seed import seed_graph
from app.models.assessment import Question
from app.models.student import StudentProfile
from app.services import assessment_service
from app.services.auth_service import register_student


@pytest.fixture
def failed_question(db_session):
    question = db_session.scalar(
        select(Question).join(Question.concept).where(Question.concept.has(slug="inner_join"))
    )
    assert question is not None
    return question


def _make_student_profile(db_session, email: str) -> StudentProfile:
    user = register_student(db_session, email=email, password="Password1", full_name="Test Student")
    profile = db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    assert profile is not None
    return profile


def test_relational_fallback_root_cause_path_matches_spec_example(db_session, failed_question, monkeypatch):
    monkeypatch.setattr(graphrag_service, "is_graph_available", lambda: False)
    profile = _make_student_profile(db_session, "graphrag-fallback@example.com")

    result = graphrag_service.analyze_root_cause(db_session, profile, failed_question.id)

    assert result.graph_source == "relational_fallback"
    assert result.concept_slug == "inner_join"
    assert not result.missing_context_warning
    step_types = [s.step_type for s in result.path]
    assert step_types[:3] == ["student", "question", "concept"]
    dependency_labels = [s.label for s in result.path if s.step_type == "concept_dependency"]
    assert any("Joins" in label for label in dependency_labels)
    assert any("Table Relationships" in label for label in dependency_labels)
    assert any("Relational Model" in label for label in dependency_labels)
    assert "Backend Engineering Intern" in result.target_role_relevance or "Data Analyst" in result.target_role_relevance
    assert len(result.recommended_resource_ids) >= 1
    assert result.confidence > 0.5


def test_root_cause_unknown_question_returns_missing_context_warning(db_session, monkeypatch):
    monkeypatch.setattr(graphrag_service, "is_graph_available", lambda: False)
    profile = _make_student_profile(db_session, "graphrag-unknown@example.com")

    result = graphrag_service.analyze_root_cause(db_session, profile, uuid.uuid4())
    assert result.missing_context_warning is True
    assert result.path == []


@pytest.mark.skipif(not is_graph_available(), reason="Neo4j not reachable at bolt://localhost:7687")
def test_real_neo4j_root_cause_path(db_session, failed_question):
    seed_graph(db_session)
    profile = _make_student_profile(db_session, "graphrag-neo4j@example.com")

    result = graphrag_service.analyze_root_cause(db_session, profile, failed_question.id)
    assert result.graph_source == "neo4j"
    assert result.concept_slug == "inner_join"
    assert not result.missing_context_warning


# ============================================================================
# Whole-graph student overview: MVP section covering the full knowledge
# graph + evidence-derived mastery overlay + reasoning + embedded practice.
# ============================================================================


def test_student_overview_includes_the_whole_graph_with_no_evidence_yet(db_session, monkeypatch):
    monkeypatch.setattr(graphrag_service, "is_graph_available", lambda: False)
    profile = _make_student_profile(db_session, "overview-empty@example.com")

    overview = graphrag_service.get_student_graph_overview(db_session, profile)

    assert overview.graph_source == "relational_fallback"
    # All six domains' concepts should be present -- this is "one big graph",
    # not a fragment scoped to whatever the student happened to attempt.
    domain_slugs = {n.domain_slug for n in overview.nodes}
    assert {"sql", "python", "javascript", "dsa", "oop", "java"} <= domain_slugs
    assert overview.total_concepts >= 35
    assert len(overview.edges) > 0
    assert all(n.status == "unknown" for n in overview.nodes)
    assert overview.concepts_with_evidence == 0
    assert overview.overall_mastery is None
    assert overview.weaknesses == []  # nothing scored "weak" yet -- honestly empty, not fabricated


def test_student_overview_reflects_real_assessment_answers(db_session, monkeypatch):
    monkeypatch.setattr(graphrag_service, "is_graph_available", lambda: False)
    profile = _make_student_profile(db_session, "overview-real@example.com")

    attempt = assessment_service.start_attempt(db_session, profile, "oop")
    question = assessment_service.select_next_question(db_session, attempt, concept_slug="oop_basics")
    assert question is not None
    correct_payload = (
        {"selected_option_ids": question.correct_answer.get("correct_option_ids", [])}
        if question.question_type in ("multiple_choice", "multiple_selection")
        else {"response_text": question.correct_answer.get("sample_answer", "")}
    )
    assessment_service.submit_response(db_session, attempt, question, correct_payload)
    db_session.refresh(attempt)
    assessment_service.complete_attempt(db_session, profile, attempt)

    overview = graphrag_service.get_student_graph_overview(db_session, profile)
    node = next(n for n in overview.nodes if n.slug == "oop_basics")
    assert node.status != "unknown"
    assert node.evidence_count >= 1
    assert node.mastery is not None
    assert overview.concepts_with_evidence >= 1
    assert overview.overall_mastery is not None


def test_weakness_reasoning_cites_real_evidence_and_prerequisite_chain(db_session, monkeypatch):
    monkeypatch.setattr(graphrag_service, "is_graph_available", lambda: False)
    profile = _make_student_profile(db_session, "overview-weak@example.com")

    # Answer every "polymorphism" question incorrectly so it scores weak, and
    # its prerequisite "inheritance" is left untouched (status "unknown").
    attempt = assessment_service.start_attempt(db_session, profile, "oop")
    guard = 0
    while True:
        guard += 1
        assert guard < 10
        question = assessment_service.select_next_question(db_session, attempt, concept_slug="polymorphism")
        if question is None:
            break
        if question.question_type in ("multiple_choice", "multiple_selection"):
            correct = set(question.correct_answer.get("correct_option_ids", []))
            wrong_option = next(o["id"] for o in question.options if o["id"] not in correct)
            payload = {"selected_option_ids": [wrong_option]}
        else:
            payload = {"response_text": "I don't know"}
        assessment_service.submit_response(db_session, attempt, question, payload)
        db_session.refresh(attempt)
    assessment_service.complete_attempt(db_session, profile, attempt)

    overview = graphrag_service.get_student_graph_overview(db_session, profile)
    weak_slugs = {w.concept_slug for w in overview.weaknesses}
    assert "polymorphism" in weak_slugs
    insight = next(w for w in overview.weaknesses if w.concept_slug == "polymorphism")
    assert insight.evidence_count >= 1
    assert str(insight.evidence_count) in insight.reasoning
    assert "Inheritance" in insight.depends_on
    assert insight.questions_total >= 3
    # The loop above answered every polymorphism question, so the pool is
    # genuinely exhausted -- practice_available must honestly reflect that.
    assert insight.questions_answered == insight.questions_total
    assert insight.practice_available is False


def test_concept_insight_works_on_demand_for_an_uncurated_node(db_session, monkeypatch):
    monkeypatch.setattr(graphrag_service, "is_graph_available", lambda: False)
    profile = _make_student_profile(db_session, "insight-ondemand@example.com")

    insight = graphrag_service.get_concept_insight(db_session, profile, "abstraction")
    assert insight is not None
    assert insight.concept_slug == "abstraction"
    assert insight.status == "unknown"
    assert insight.evidence_count == 0
    assert "haven't" in insight.reasoning.lower()

    assert graphrag_service.get_concept_insight(db_session, profile, "not-a-real-concept") is None
