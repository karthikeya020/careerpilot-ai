def test_health_check(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_check(client) -> None:
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] is True


def test_dependency_health_check(client) -> None:
    response = client.get("/api/v1/health/dependencies")
    assert response.status_code == 200
    body = response.json()
    assert "database" in body["dependencies"]
    assert "redis" in body["dependencies"]
    assert "neo4j" in body["dependencies"]
    assert body["dependencies"]["database"] is True
    assert body["status"] in ("ok", "degraded")
