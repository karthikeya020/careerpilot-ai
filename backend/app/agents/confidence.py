"""Shared confidence helpers for keyword-rubric grading agents.

Confidence here is deliberately derived from measurable signal -- rubric
richness (how much evidence the grader had to check against) and, where a
grader returns several sub-scores, their internal agreement -- rather than
a flat constant selected only by which code path executed. A grade backed
by a thin rubric or a wildly inconsistent set of sub-scores is genuinely
less trustworthy than one backed by a rich rubric with sub-scores that
agree; this makes that real.
"""


def rubric_confidence(*, keyword_count: int, is_fallback: bool) -> float:
    """Confidence for a single keyword-overlap-graded score.

    A richer rubric (more terms to check the answer against) grounds a
    more trustworthy read, whether the grader is the deterministic
    keyword matcher or a live model. The deterministic path is capped
    lower since it is explicitly a proxy method, never claiming
    full-grading certainty (see each agent's fallback docstring).
    """
    if keyword_count <= 0:
        return 0.3
    richness = min(1.0, keyword_count / 6)
    if is_fallback:
        return round(0.4 + 0.2 * richness, 4)
    return round(0.65 + 0.2 * richness, 4)


def multi_score_confidence(scores: list[float], *, keyword_count: int, is_fallback: bool) -> float:
    """Confidence for a grader that returns several sub-scores.

    Starts from `rubric_confidence`, then applies a real penalty when the
    sub-scores disagree with each other -- a scattered read (e.g. high
    relevance but near-zero depth) is less trustworthy than a coherent
    one, and that disagreement is computed from the actual scores
    returned, not asserted.
    """
    base = rubric_confidence(keyword_count=keyword_count, is_fallback=is_fallback)
    if len(scores) < 2:
        return base
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    spread_penalty = min(0.15, variance)
    return round(max(0.15, base - spread_penalty), 4)
