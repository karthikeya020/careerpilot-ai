"""Deterministic resume text extraction and section detection.

This module is the "adapter" boundary for resume understanding: Phase 1 uses
regex/keyword heuristics; a future phase can drop in an LLM-backed parser
behind the same `extract_text` / `detect_sections` function signatures
without touching callers (app/services/resume_service.py).
"""

import io
import re
from dataclasses import dataclass

from docx import Document
from pypdf import PdfReader

from app.core.errors import UnprocessableError
from app.models.resume import (
    SECTION_ACHIEVEMENTS,
    SECTION_CERTIFICATIONS,
    SECTION_EDUCATION,
    SECTION_EXPERIENCE,
    SECTION_OTHER,
    SECTION_PROJECTS,
    SECTION_SKILLS,
    SECTION_SUMMARY,
)

PDF_CONTENT_TYPES = {"application/pdf"}
DOCX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

SECTION_HEADINGS: dict[str, set[str]] = {
    SECTION_SUMMARY: {"summary", "objective", "profile", "about me", "career objective"},
    SECTION_EDUCATION: {"education", "academic background", "academics"},
    SECTION_EXPERIENCE: {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "internship experience",
        "internships",
    },
    SECTION_PROJECTS: {"projects", "personal projects", "academic projects", "key projects"},
    SECTION_SKILLS: {
        "skills",
        "technical skills",
        "core competencies",
        "skills and interests",
        "technologies",
    },
    SECTION_CERTIFICATIONS: {"certifications", "certificates", "licenses", "licenses and certifications"},
    SECTION_ACHIEVEMENTS: {"achievements", "awards", "honors", "honors and awards", "accomplishments"},
}


def extract_text(content: bytes, content_type: str, filename: str) -> str:
    lower_name = filename.lower()
    if content_type in PDF_CONTENT_TYPES or lower_name.endswith(".pdf"):
        return _extract_pdf_text(content)
    if content_type in DOCX_CONTENT_TYPES or lower_name.endswith(".docx"):
        return _extract_docx_text(content)
    if content_type == "text/plain" or lower_name.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")
    raise UnprocessableError(
        "Unsupported resume file type. Upload a PDF, DOCX, or plain-text file.",
        details={"content_type": content_type, "filename": filename},
    )


def _extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # pypdf raises various error types for malformed PDFs
        raise UnprocessableError("Could not read PDF file. It may be corrupted or scanned as images.") from exc


def _extract_docx_text(content: bytes) -> str:
    try:
        document = Document(io.BytesIO(content))
        return "\n".join(p.text for p in document.paragraphs)
    except Exception as exc:
        raise UnprocessableError("Could not read DOCX file. It may be corrupted.") from exc


def _normalize_heading(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or len(stripped) > 45:
        return None
    letters_only = re.sub(r"[^a-z ]", "", stripped.lower()).strip()
    letters_only = re.sub(r"\s+", " ", letters_only)
    return letters_only or None


def _match_heading(line: str) -> str | None:
    normalized = _normalize_heading(line)
    if normalized is None:
        return None
    for section_type, variants in SECTION_HEADINGS.items():
        if normalized in variants:
            return section_type
    return None


@dataclass
class DetectedSection:
    section_type: str
    heading: str
    text: str
    order_index: int


def detect_sections(raw_text: str) -> list[DetectedSection]:
    lines = raw_text.splitlines()
    sections: list[DetectedSection] = []
    current_type: str | None = None
    current_heading = ""
    current_lines: list[str] = []
    order = 0

    def flush() -> None:
        nonlocal current_lines, order
        text = "\n".join(current_lines).strip()
        if text:
            sections.append(
                DetectedSection(
                    section_type=current_type or SECTION_OTHER,
                    heading=current_heading,
                    text=text,
                    order_index=order,
                )
            )
            order += 1
        current_lines = []

    for line in lines:
        matched = _match_heading(line)
        if matched:
            flush()
            current_type = matched
            current_heading = line.strip()
        else:
            current_lines.append(line)
    flush()

    if not sections:
        stripped = raw_text.strip()
        if stripped:
            sections.append(DetectedSection(section_type=SECTION_OTHER, heading="", text=stripped, order_index=0))
    return sections
