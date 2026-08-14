def _register_and_auth(client, email="student-profile@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Profile Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_update_profile_persists_new_fields(client) -> None:
    headers = _register_and_auth(client)

    response = client.patch(
        "/api/v1/students/me",
        headers=headers,
        json={
            "full_name": "Ada Updated",
            "date_of_birth": "2003-05-14",
            "college_year": "3rd year",
            "branch": "Computer Science",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Ada Updated"
    assert body["date_of_birth"] == "2003-05-14"
    assert body["college_year"] == "3rd_year"
    assert body["branch"] == "Computer Science"

    me_response = client.get("/api/v1/students/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["branch"] == "Computer Science"


def test_update_profile_partial_update_leaves_other_fields(client) -> None:
    headers = _register_and_auth(client, email="partial-update@example.com")

    client.patch("/api/v1/students/me", headers=headers, json={"branch": "Mechanical Engineering"})
    response = client.patch("/api/v1/students/me", headers=headers, json={"college_year": "2nd year"})

    assert response.status_code == 200
    body = response.json()
    assert body["branch"] == "Mechanical Engineering"
    assert body["college_year"] == "2nd_year"


def test_update_profile_rejects_invalid_college_year(client) -> None:
    headers = _register_and_auth(client, email="invalid-year@example.com")

    response = client.patch("/api/v1/students/me", headers=headers, json={"college_year": "9th year"})
    assert response.status_code == 422


def test_update_profile_rejects_unrealistic_date_of_birth(client) -> None:
    headers = _register_and_auth(client, email="invalid-dob@example.com")

    response = client.patch("/api/v1/students/me", headers=headers, json={"date_of_birth": "2020-01-01"})
    assert response.status_code == 422


def test_update_profile_requires_auth(client) -> None:
    response = client.patch("/api/v1/students/me", json={"branch": "Civil Engineering"})
    assert response.status_code == 401
