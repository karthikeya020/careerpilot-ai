import mimetypes
import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.interview import (
    ALL_INTERVIEW_MODES,
    InterviewAnswer,
    InterviewQuestion,
    InterviewSession,
)
from app.models.student import StudentProfile
from app.schemas.interview import (
    InterviewAnswerOut,
    InterviewEvaluationOut,
    InterviewProgressOut,
    InterviewQuestionOut,
    InterviewReplayItemOut,
    InterviewReplayOut,
    InterviewReplayQuestionOut,
    InterviewRoundSummaryOut,
    InterviewSessionOut,
    StartInterviewRequest,
)
from app.services import interview_service, storage

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _get_owned_session(db: Session, session_id: uuid.UUID, student_profile: StudentProfile) -> InterviewSession:
    session = interview_service.get_session(db, session_id)
    if session is None or session.student_profile_id != student_profile.id:
        raise NotFoundError("Interview session not found.")
    return session


def _question_out(question: InterviewQuestion | None) -> InterviewQuestionOut | None:
    return InterviewQuestionOut.model_validate(question) if question is not None else None


def _answer_out(answer: InterviewAnswer) -> InterviewAnswerOut:
    return InterviewAnswerOut(
        id=answer.id,
        question_id=answer.question_id,
        transcript=answer.transcript,
        transcript_source=answer.transcript_source,
        audio_duration_seconds=float(answer.audio_duration_seconds) if answer.audio_duration_seconds else None,
        audio_mime_type=answer.audio_mime_type,
        has_audio=answer.audio_storage_path is not None,
        submitted_at=answer.submitted_at,
    )


def _progress_out(session: InterviewSession, answer: InterviewAnswer | None = None) -> InterviewProgressOut:
    next_question = interview_service.get_next_question(session)
    is_complete = next_question is None
    evaluation = None
    if answer is not None and answer.evaluation is not None:
        evaluation = InterviewEvaluationOut.model_validate(answer.evaluation)
    return InterviewProgressOut(
        session=InterviewSessionOut.model_validate(session),
        answer=_answer_out(answer) if answer is not None else None,
        evaluation=evaluation,
        next_question=_question_out(next_question),
        is_complete=is_complete,
    )


@router.get("/modes")
def list_modes() -> list[str]:
    return ALL_INTERVIEW_MODES


@router.post("/sessions", response_model=InterviewProgressOut, status_code=201)
def start_session(
    payload: StartInterviewRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> InterviewProgressOut:
    if payload.mode not in ALL_INTERVIEW_MODES:
        raise NotFoundError(f"Unknown interview mode '{payload.mode}'.")
    session = interview_service.start_session(
        db,
        student_profile,
        mode=payload.mode,
        target_role_id=payload.target_role_id,
        job_description_id=payload.job_description_id,
        company_name=payload.company_name,
    )
    return _progress_out(session)


@router.get("/sessions/{session_id}", response_model=InterviewProgressOut)
def get_session_progress(
    session_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> InterviewProgressOut:
    session = _get_owned_session(db, session_id, student_profile)
    return _progress_out(session)


@router.post("/sessions/{session_id}/answers", response_model=InterviewProgressOut)
async def submit_answer(
    session_id: uuid.UUID,
    question_id: uuid.UUID = Form(...),
    typed_answer_text: str | None = Form(None),
    audio_duration_seconds: float | None = Form(None),
    used_browser_transcription: bool = Form(False),
    camera_on_ratio: float | None = Form(None),
    audio: UploadFile | None = File(None),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> InterviewProgressOut:
    session = _get_owned_session(db, session_id, student_profile)
    question = db.get(InterviewQuestion, question_id)
    if question is None or question.session_id != session.id:
        raise NotFoundError("Interview question not found in this session.")

    audio_bytes = await audio.read() if audio is not None else None
    answer = interview_service.submit_answer(
        db,
        student_profile,
        question,
        audio_bytes=audio_bytes,
        audio_filename=audio.filename if audio is not None else None,
        audio_mime_type=audio.content_type if audio is not None else None,
        audio_duration_seconds=audio_duration_seconds,
        typed_answer_text=typed_answer_text,
        used_browser_transcription=used_browser_transcription,
    )
    evaluation = interview_service.evaluate_answer(db, student_profile, session, question, answer, camera_on_ratio=camera_on_ratio)
    interview_service.maybe_insert_follow_up(db, session, question, answer, evaluation)
    db.refresh(session)

    next_question = interview_service.get_next_question(session)
    if next_question is None and session.status != "completed":
        session = interview_service.complete_session(db, student_profile, session)

    db.refresh(answer)
    return _progress_out(session, answer)


@router.get("/sessions/{session_id}/replay", response_model=InterviewReplayOut)
def get_replay(
    session_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> InterviewReplayOut:
    session = _get_owned_session(db, session_id, student_profile)
    items = []
    for question in session.questions:
        if question.answer is None:
            continue
        items.append(
            InterviewReplayItemOut(
                question=InterviewReplayQuestionOut.model_validate(question),
                answer=_answer_out(question.answer),
                evaluation=(
                    InterviewEvaluationOut.model_validate(question.answer.evaluation)
                    if question.answer.evaluation is not None
                    else None
                ),
            )
        )
    summary = InterviewRoundSummaryOut(**interview_service.build_round_summary(session))
    return InterviewReplayOut(session=InterviewSessionOut.model_validate(session), items=items, summary=summary)


@router.get("/answers/{answer_id}/audio")
def get_answer_audio(
    answer_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> Response:
    answer = db.get(InterviewAnswer, answer_id)
    if answer is None or answer.question.session.student_profile_id != student_profile.id:
        raise NotFoundError("Interview answer audio not found.")
    if answer.audio_storage_path is None:
        raise NotFoundError("This answer has no stored audio (typed answer).")
    content = storage.read(answer.audio_storage_path)
    media_type = answer.audio_mime_type or mimetypes.guess_type(answer.audio_storage_path)[0] or "application/octet-stream"
    return Response(content=content, media_type=media_type)
