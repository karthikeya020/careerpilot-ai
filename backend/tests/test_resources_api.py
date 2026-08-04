def _register_and_auth(client, email="resources-api@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Resources Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_resources_filtered_by_concept(client) -> None:
    headers = _register_and_auth(client)
    response = client.get("/api/v1/resources", headers=headers, params={"concept": "inner_join"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    assert all("url" in r for r in body)


def test_recommend_resources_for_concept(client) -> None:
    headers = _register_and_auth(client)
    response = client.get("/api/v1/resources/recommendations", headers=headers, params={"concept": "inner_join"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["resources"]) >= 1
    assert body["confidence"] > 0
