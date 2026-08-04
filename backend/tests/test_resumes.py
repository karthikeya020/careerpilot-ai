import io

from docx import Document


def _register_and_auth(client, email="resume@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Resume Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _build_docx() -> bytes:
    document = Document()
    document.add_paragraph("Ada Lovelace")
    document.add_paragraph("SUMMARY")
    document.add_paragraph("Aspiring backend engineer with a passion for distributed systems.")
    document.add_paragraph("SKILLS")
    document.add_paragraph("Python, SQL, Git, Docker")
    document.add_paragraph("PROJECTS")
    document.add_paragraph("Built a REST API using FastAPI and PostgreSQL for a university course project.")
    document.add_paragraph("EDUCATION")
    document.add_paragraph("B.Tech Computer Science, 2026")
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_upload_docx_resume_parses_sections_and_skills(client) -> None:
    headers = _register_and_auth(client)
    docx_bytes = _build_docx()

    response = client.post(
        "/api/v1/resumes",
        headers=headers,
        files={"file": ("resume.docx", docx_bytes, DOCX_CONTENT_TYPE)},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["parsing_status"] == "parsed"

    section_types = {s["section_type"] for s in body["sections"]}
    assert {"summary", "skills", "projects", "education"}.issubset(section_types)

    skill_names = {rs["skill"]["name"] for rs in body["resume_skills"]}
    assert {"Python", "SQL", "Git", "Docker", "FastAPI", "PostgreSQL"}.issubset(skill_names)

    projects_evidence = next(rs for rs in body["resume_skills"] if rs["skill"]["name"] == "FastAPI")
    assert "FastAPI" in projects_evidence["evidence_snippet"]

    get_response = client.get("/api/v1/resumes/me", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == body["id"]


def test_upload_rejects_unsupported_file_type(client) -> None:
    headers = _register_and_auth(client)
    response = client.post(
        "/api/v1/resumes",
        headers=headers,
        files={"file": ("resume.exe", b"not a resume", "application/octet-stream")},
    )
    assert response.status_code == 422


def test_upload_rejects_empty_file(client) -> None:
    headers = _register_and_auth(client)
    response = client.post(
        "/api/v1/resumes",
        headers=headers,
        files={"file": ("resume.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 422


def test_get_resume_without_upload_returns_404(client) -> None:
    headers = _register_and_auth(client)
    response = client.get("/api/v1/resumes/me", headers=headers)
    assert response.status_code == 404
