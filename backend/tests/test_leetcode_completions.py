"""LeetCode completions + the 'explain how you solved' code review.

Covers marking / unmarking, the immediate how-to-think + similar-problems
payload, and the heuristic code review (no API key in tests -> deterministic
fallback) reporting complexity for a quadratic vs a linear solution.
"""

NESTED_LOOP_TWO_SUM = """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
""".strip()

HASH_TWO_SUM = """
def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
""".strip()


def _register(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "LC Completions Student"},
    )
    assert response.status_code in (200, 201)
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _mark(client, headers, slug="two-sum", concept="arrays_strings"):
    return client.post(
        "/api/v1/assessments/leetcode-completions",
        headers=headers,
        json={"slug": slug, "title": "Two Sum", "difficulty": "Easy", "concept_slug": concept, "domain_slug": "dsa"},
    )


def test_mark_then_list_then_unmark(client) -> None:
    headers = _register(client, "lc-mark@example.com")

    marked = _mark(client, headers)
    assert marked.status_code == 200
    assert marked.json()["slug"] == "two-sum"
    assert marked.json()["has_analysis"] is False

    listed = client.get("/api/v1/assessments/leetcode-completions", headers=headers).json()
    assert [c["slug"] for c in listed] == ["two-sum"]

    deleted = client.delete("/api/v1/assessments/leetcode-completions/two-sum", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/api/v1/assessments/leetcode-completions", headers=headers).json() == []


def test_analysis_payload_before_any_code(client) -> None:
    headers = _register(client, "lc-analysis-pre@example.com")
    _mark(client, headers)

    body = client.get("/api/v1/assessments/leetcode-completions/two-sum/analysis", headers=headers).json()
    assert body["how_to_think"]  # concept approach shown immediately
    assert len(body["similar_problems"]) >= 1
    assert all(p["url"].startswith("https://leetcode.com/problems/") for p in body["similar_problems"])
    assert "two-sum" not in [p["slug"] for p in body["similar_problems"]]
    assert body["review"] is None


def test_analyze_reports_quadratic_for_nested_loops(client) -> None:
    headers = _register(client, "lc-analyze-quad@example.com")
    _mark(client, headers)

    body = client.post(
        "/api/v1/assessments/leetcode-completions/two-sum/analyze",
        headers=headers,
        json={"code": NESTED_LOOP_TWO_SUM, "language": "python"},
    ).json()

    review = body["review"]
    assert review is not None
    assert review["time_complexity"] == "O(n^2)"
    assert review["ai_generated"] is False
    assert review["improvements"]
    assert body["analyzed_at"]

    # persisted -- a later GET returns the same review
    again = client.get("/api/v1/assessments/leetcode-completions/two-sum/analysis", headers=headers).json()
    assert again["review"]["time_complexity"] == "O(n^2)"
    assert again["code"].startswith("def two_sum")


def test_analyze_reports_linear_for_hash_solution(client) -> None:
    headers = _register(client, "lc-analyze-lin@example.com")
    _mark(client, headers)

    review = client.post(
        "/api/v1/assessments/leetcode-completions/two-sum/analyze",
        headers=headers,
        json={"code": HASH_TWO_SUM, "language": "python"},
    ).json()["review"]

    assert review["time_complexity"] == "O(n)"
    assert review["space_complexity"] == "O(n)"


def test_analyze_requires_marking_complete_first(client) -> None:
    headers = _register(client, "lc-analyze-404@example.com")
    resp = client.post(
        "/api/v1/assessments/leetcode-completions/two-sum/analyze",
        headers=headers,
        json={"code": HASH_TWO_SUM},
    )
    assert resp.status_code == 404
