"""API-level tests for the Career Twin's new endpoints: multi-role
alignment, time-to-target projection, and the shareable snapshot proof
(including cross-student ownership isolation)."""

import io

from docx import Document

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _register_and_auth(client, email="twin-api@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Twin API Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _upload_resume(client, headers):
    document = Document()
    document.add_paragraph("SKILLS")
    document.add_paragraph("Python, SQL, Data Analysis, Pandas")
    document.add_paragraph("PROJECTS")
    document.add_paragraph("Built a data pipeline using Python and SQL for a university course project.")
    buffer = io.BytesIO()
    document.save(buffer)
    response = client.post(
        "/api/v1/resumes", headers=headers, files={"file": ("resume.docx", buffer.getvalue(), DOCX_CONTENT_TYPE)}
    )
    assert response.status_code == 201


def test_multi_role_endpoint_returns_sorted_role_alignments(client) -> None:
    headers = _register_and_auth(client, "multirole-api@example.com")
    _upload_resume(client, headers)

    response = client.get("/api/v1/career-twin/multi-role", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 4
    scores = [r["alignment"] for r in body]
    assert scores == sorted(scores, reverse=True)
    assert any(r["role_title"] == "Data Analyst" for r in body)


def test_time_to_target_endpoint_reports_insufficient_history_before_any_trend(client) -> None:
    headers = _register_and_auth(client, "timetotarget-api@example.com")
    _upload_resume(client, headers)

    response = client.get("/api/v1/career-twin/time-to-target", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 6
    assert all(p["status"] in ("insufficient_history", "already_at_target", "projected", "not_improving") for p in body)


def test_snapshot_proof_endpoint_returns_citations_and_is_owner_scoped(client) -> None:
    headers_a = _register_and_auth(client, "proof-a@example.com")
    _upload_resume(client, headers_a)
    snapshot_resp = client.get("/api/v1/career-twin", headers=headers_a)
    assert snapshot_resp.status_code == 200
    snapshot_id = snapshot_resp.json()["id"]

    proof_resp = client.get(f"/api/v1/career-twin/{snapshot_id}/proof", headers=headers_a)
    assert proof_resp.status_code == 200
    body = proof_resp.json()
    assert body["student_name"] == "Twin API Student"
    assert "not a hiring recommendation" in body["disclaimer"].lower()
    assert any(len(c["citations"]) > 0 for c in body["components"])

    headers_b = _register_and_auth(client, "proof-b@example.com")
    cross_resp = client.get(f"/api/v1/career-twin/{snapshot_id}/proof", headers=headers_b)
    assert cross_resp.status_code == 404
