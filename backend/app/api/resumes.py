import uuid

from fastapi import APIRouter, Depends, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.graphrag.service import get_resume_graph_diagnosis
from app.models.resume import Resume
from app.models.student import StudentProfile
from app.schemas.resume import (
    BulletGradeOut,
    ParseabilityOut,
    RecruiterCardOut,
    ResumeAnalysisOut,
    ResumeOut,
    ResumeSummaryOut,
    RewriteSuggestionOut,
    SelfConsistencyFlagOut,
)
from app.services.recruiter_card_service import build_recruiter_card
from app.services.resume_analysis_service import check_self_consistency, grade_bullets, score_parseability
from app.services.resume_rewrite_service import suggest_rewrites_for_gap
from app.services.resume_service import (
    activate_resume,
    get_latest_resume,
    list_resumes,
    process_resume,
)

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeOut, status_code=201)
async def upload_resume(
    file: UploadFile,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> Resume:
    content = await file.read()
    return process_resume(db, student_profile, file, content)


@router.get("/me", response_model=ResumeOut)
def get_my_latest_resume(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> Resume:
    resume = get_latest_resume(db, student_profile.id)
    if resume is None:
        raise NotFoundError("No resume has been uploaded yet.")
    return resume


@router.get("", response_model=list[ResumeSummaryOut])
def get_resume_history(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[ResumeSummaryOut]:
    resumes = list_resumes(db, student_profile.id)
    return [
        ResumeSummaryOut(
            id=r.id,
            original_filename=r.original_filename,
            file_size=r.file_size,
            parsing_status=r.parsing_status,
            uploaded_at=r.uploaded_at,
            parsed_at=r.parsed_at,
            is_active=r.is_active,
            superseded_at=r.superseded_at,
            skill_count=len(r.resume_skills),
        )
        for r in resumes
    ]


@router.post("/{resume_id}/activate", response_model=ResumeOut)
def activate_resume_version(
    resume_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> Resume:
    return activate_resume(db, student_profile, resume_id)


@router.get("/me/analysis", response_model=ResumeAnalysisOut)
def get_my_resume_analysis(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> ResumeAnalysisOut:
    """Bullet-strength grading, self-consistency check, parseability score,
    and resume-to-graph diagnosis in one call -- all computed fresh from the
    active resume, never persisted, so they can never drift out of date."""
    resume = get_latest_resume(db, student_profile.id)
    if resume is None or resume.parsing_status != "parsed":
        return ResumeAnalysisOut(has_resume=False)

    bullet_grades = grade_bullets(resume)
    flags = check_self_consistency(db, resume)
    parseability = score_parseability(resume)
    graph_diagnosis = get_resume_graph_diagnosis(db, student_profile, resume)

    return ResumeAnalysisOut(
        has_resume=True,
        bullet_grades=[BulletGradeOut.model_validate(g.__dict__) for g in bullet_grades],
        self_consistency_flags=[SelfConsistencyFlagOut.model_validate(f.__dict__) for f in flags],
        parseability=ParseabilityOut(score=parseability.score, warnings=parseability.warnings),
        graph_diagnosis=graph_diagnosis,
    )


@router.get("/me/recruiter-card", response_model=RecruiterCardOut)
def get_my_recruiter_card(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> RecruiterCardOut:
    """Self-view of the same evidence-completeness card a recruiter would see
    for this student -- always available to the student about their own
    data, independent of the recruiter_visible consent toggle (that toggle
    only gates whether an actual recruiter account can see it)."""
    resume = get_latest_resume(db, student_profile.id)
    card = build_recruiter_card(db, student_profile, resume)
    return RecruiterCardOut(**card.__dict__)


@router.get("/me/rewrite-suggestions", response_model=list[RewriteSuggestionOut])
def get_my_rewrite_suggestions(
    listing_id: uuid.UUID = Query(..., description="A tracked Job Match dream job to scope the gap plan to."),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[RewriteSuggestionOut]:
    resume = get_latest_resume(db, student_profile.id)
    suggestions = suggest_rewrites_for_gap(db, student_profile, resume, listing_id)
    return [RewriteSuggestionOut(**s.__dict__) for s in suggestions]
