def _register(client, email="student@example.com", password="Password1", full_name="Ada Student"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )


def test_register_creates_student_with_role(client) -> None:
    response = _register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "student@example.com"
    assert body["user"]["roles"] == ["student"]
    assert "access_token" in body
    assert "careerpilot_refresh_token" in response.cookies


def test_register_duplicate_email_conflicts(client) -> None:
    _register(client)
    response = _register(client)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_weak_password_rejected(client) -> None:
    response = _register(client, password="allletters")
    assert response.status_code == 422


def test_login_success_and_wrong_password(client) -> None:
    _register(client)
    ok = client.post("/api/v1/auth/login", json={"email": "student@example.com", "password": "Password1"})
    assert ok.status_code == 200

    bad = client.post("/api/v1/auth/login", json={"email": "student@example.com", "password": "wrongpass1"})
    assert bad.status_code == 401
    assert bad.json()["error"]["code"] == "unauthorized"


def test_me_requires_bearer_token(client) -> None:
    unauthenticated = client.get("/api/v1/auth/me")
    assert unauthenticated.status_code == 401

    register_response = _register(client)
    access_token = register_response.json()["access_token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "student@example.com"


def test_refresh_rotates_token_and_logout_revokes(client) -> None:
    _register(client)
    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me.status_code == 200

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    reuse_response = client.post("/api/v1/auth/refresh")
    assert reuse_response.status_code == 401
