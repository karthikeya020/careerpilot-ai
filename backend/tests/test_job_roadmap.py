"""Dream-job roadmap: phase structure, the brutal-bar framing, sector-driven
difficulty, and the catalog-listing variant.
"""


def _register(client, email):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Roadmap Student"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_faang_roadmap_is_brutal_and_complete(client) -> None:
    headers = _register(client, "roadmap-faang@example.com")
    body = client.get(
        "/api/v1/job-catalog/roadmap",
        headers=headers,
        params={
            "company": "Google",
            "title": "Software Engineer, New Grad",
            "sector": "faang",
            "skills": "Data Structures,Algorithms,System Design,Python",
        },
    ).json()

    assert body["difficulty"] == "brutal"
    assert "Google" in body["bar"]
    titles = [p["title"] for p in body["phases"]]
    assert "Foundations" in titles
    assert "System design" in titles
    assert any("mock" in t.lower() for t in titles)
    assert body["total_weeks"] > 0
    assert all(p["weeks"].startswith("Weeks ") for p in body["phases"])
    assert all(p["actions"] for p in body["phases"])
    # every phase has at least one in-app or external link somewhere
    assert any(a.get("link") for p in body["phases"] for a in p["actions"])


def test_government_roadmap_is_achievable_and_leaner(client) -> None:
    headers = _register(client, "roadmap-gov@example.com")
    body = client.get(
        "/api/v1/job-catalog/roadmap",
        headers=headers,
        params={"company": "ISRO", "title": "Scientist/Engineer", "sector": "government", "skills": "Python,SQL"},
    ).json()

    assert body["difficulty"] == "achievable"
    assert "System design" not in [p["title"] for p in body["phases"]]
    assert body["total_weeks"] <= 20


def test_roadmap_for_a_seeded_listing(client) -> None:
    headers = _register(client, "roadmap-listing@example.com")
    recommended = client.get("/api/v1/job-catalog/recommended", headers=headers).json()
    listing_id = recommended[0]["listing"]["id"]

    body = client.get(f"/api/v1/job-catalog/{listing_id}/roadmap", headers=headers)
    assert body.status_code == 200
    data = body.json()
    assert data["company"] == recommended[0]["listing"]["company"]
    assert len(data["phases"]) >= 5
