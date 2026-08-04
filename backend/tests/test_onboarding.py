def _register_and_auth(client, email="onboard@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Onboarding Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_onboarding_persists_goal_role_and_scores_twin(client) -> None:
    headers = _register_and_auth(client)

    response = client.post(
        "/api/v1/onboarding",
        headers=headers,
        json={
            "full_name": "Ada Onboarded",
            "career_goal_description": "Become a backend engineer at a product company.",
            "timeline_months": 6,
            "target_role_title": "Backend Engineer",
            "target_role_seniority": "entry level",
            "self_assessed_skills": [
                {"skill_name": "Python", "rating": 0.7},
                {"skill_name": "SQL", "rating": 0.6},
                {"skill_name": "Not A Real Skill", "rating": 0.9},
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Ada Onboarded"
    assert body["onboarding_completed"] is True
    assert body["primary_target_role"]["title"] == "Backend Engineer"
    assert body["primary_target_role"]["seniority"] == "entry_level"
    assert len(body["career_goals"]) == 1

    me_response = client.get("/api/v1/students/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["onboarding_completed"] is True


def test_onboarding_requires_student_auth(client) -> None:
    response = client.post(
        "/api/v1/onboarding",
        json={
            "full_name": "No Auth",
            "career_goal_description": "x",
            "target_role_title": "Engineer",
        },
    )
    assert response.status_code == 401


def test_onboarding_rejects_invalid_seniority(client) -> None:
    headers = _register_and_auth(client)
    response = client.post(
        "/api/v1/onboarding",
        headers=headers,
        json={
            "full_name": "Ada",
            "career_goal_description": "Goal",
            "target_role_title": "Engineer",
            "target_role_seniority": "godlike",
        },
    )
    assert response.status_code == 422
