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
