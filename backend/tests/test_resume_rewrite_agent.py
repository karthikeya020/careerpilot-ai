"""ResumeRewriteAgent: the "no evidence -> no rewrite" path is load-bearing
(Constitution rule 1 -- never invent experience), not an edge case."""

from app.agents.resume_rewrite_agent import ResumeRewriteAgent, ResumeRewriteInput


def test_no_evidence_snippets_returns_insufficient_evidence_and_no_bullet():
    agent = ResumeRewriteAgent()
    output, _latency = agent.safe_run(ResumeRewriteInput(skill_name="Kubernetes", evidence_snippets=[]))
    assert output.has_sufficient_evidence is False
    assert output.rewritten_bullet is None
    assert "no existing evidence" in output.note.lower()
    assert output.status == "completed"


def test_with_evidence_snippets_returns_a_rewrite_grounded_in_that_evidence():
    agent = ResumeRewriteAgent()
    snippet = "Built a data pipeline using Python for a university course project, processing 10k records/day."
    output, _latency = agent.safe_run(
        ResumeRewriteInput(skill_name="Python", evidence_snippets=[snippet, "Python"])
    )
    assert output.has_sufficient_evidence is True
    assert output.rewritten_bullet is not None
    # Deterministic fallback (no live provider key in tests) must never
    # introduce a fact absent from the supplied evidence -- the simplest
    # proof of that is that its output is drawn verbatim from the evidence.
    assert output.rewritten_bullet in (snippet, "Python")


def test_never_fabricates_a_number_or_tool_not_present_in_evidence():
    agent = ResumeRewriteAgent()
    snippet = "Worked on a project."
    output, _latency = agent.safe_run(ResumeRewriteInput(skill_name="Rust", evidence_snippets=[snippet]))
    assert output.has_sufficient_evidence is True
    # The deterministic fallback returns evidence verbatim -- proof it never
    # inserted "Rust" or any other fact the evidence didn't already contain.
    assert output.rewritten_bullet == snippet
