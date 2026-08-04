"""Interview Arena orchestration: session/question/answer lifecycle plus the
CARE-routed evaluation of each answer.

Design note on how CARE decides "which agents are needed" here (Prompt 3):
`CommunicationAgent` runs deterministically on every answer up front (it's
free and always relevant, exactly like MCQ scoring bypassing the AI grader
in the assessment engine). The judgment-heavy specialists (HR, Technical,
Resume Evidence, JD Alignment) are gated behind CARE's route decision:

- Technical/behavioral answers with enough bank context (concept + expected
  keywords, or a plain question with no external dependency) go straight to
  `single_agent` -- one specialist.
- Resume-based, role-specific, and company-context questions start with
  evidence intentionally marked insufficient (their grounding -- resume
  text, the job description -- must be gathered first), so CARE routes
  through `graphrag_agent` as a context-gathering pass before the primary
  specialist(s) run.
- A short/off-topic/ungrounded answer is flagged `evidence_conflict=True`
  up front (a real, checkable signal -- not a guess) which routes straight
  to a `multi_agent` council plus `ConsensusAgent`, and on to
  `critic_reflection` if the council disagrees -- matching "weak or
  conflicting evaluation -> critic + consensus" from the brief.
- `single_agent`, when reached *after* an escalation already produced a
  result, is treated as CARE's generic "resolved, stop" terminal label (see
  `app/care_engine/policy.py`'s docstring) rather than triggering a second,
  redundant single-pass judgment -- `state["primary_confidence"]` guards
  against re-running agents that already produced the settled result.
"""

import random
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import AgentOutput
from app.agents.communication_agent import CommunicationAgent, CommunicationInput
from app.agents.consensus_agent import ConsensusAgent, ConsensusInput, ConsensusVote
from app.agents.critic_agent import CriticAgent, CriticClaim, CriticInput
from app.agents.hr_agent import HRAgent, HRInterviewInput
from app.agents.jd_alignment_agent import JDAlignmentAgent, JDAlignmentInput
from app.agents.memory_agent import MemoryAgent, MemoryInput
from app.agents.resume_evidence_agent import ResumeEvidenceAgent, ResumeEvidenceCheckInput
from app.agents.technical_agent import TechnicalAgent, TechnicalInterviewInput
from app.care_engine.engine import AgentRunRecord, StepOutcome, run_care_task
from app.care_engine.schemas import RoutingFactors
from app.career_twin.scoring import recompute_twin
from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError, UnprocessableError
from app.models.assessment import Concept
from app.models.base import utcnow
from app.models.care import AgentRun
from app.models.interview import (
    INTERVIEW_MODE_COMPANY_CONTEXT,
    INTERVIEW_MODE_HR,
    INTERVIEW_MODE_RESUME,
    INTERVIEW_MODE_ROLE_SPECIFIC,
    INTERVIEW_MODE_TECHNICAL,
    INTERVIEW_STATUS_COMPLETED,
    TRANSCRIPT_SOURCE_TYPED,
    TRANSCRIPT_SOURCE_UNAVAILABLE,
    InterviewAnswer,
    InterviewEvaluation,
    InterviewQuestion,
    InterviewSession,
)
from app.models.job_description import JobDescription
from app.models.skill import EVIDENCE_TYPE_INTERVIEW, Skill, SkillEvidence
from app.models.student import StudentProfile, TargetRole
from app.services import storage
from app.services.resume_service import get_latest_resume
from app.services.speech_to_text import get_speech_to_text_provider

_TASK_TYPE = "interview_evaluation"
_MIN_WORDS_FOR_CONFIDENT_ANSWER = 12
_ALLOWED_AUDIO_MIME_PREFIXES = ("audio/", "video/webm")  # some browsers report webm audio as a video/webm container

# (prompt, expected_keywords, concept_slug|None, concept_domain|None)
_TECHNICAL_BANK = [
    (
        "Explain the difference between an INNER JOIN and a LEFT JOIN, and give an example of when you'd use each.",
        ["inner join", "left join", "match", "unmatched", "null"],
        "inner_join",
        "sql",
    ),
    (
        "What does GROUP BY do, and how does it interact with aggregate functions like COUNT or SUM?",
        ["group", "aggregate", "count", "sum", "collapse"],
        "group_by",
        "sql",
    ),
    (
        "What is a Python list comprehension, and when would you prefer it over a for loop?",
        ["list comprehension", "iterable", "concise", "loop"],
        "list_comprehension",
        "python",
    ),
]

_HR_BANK = [
    "Tell me about a time you had to work with a difficult team member. How did you handle it?",
    "Describe a project where you had to meet a tight deadline. What was your approach?",
    "Tell me about a time you made a mistake at work or in a project. What did you learn?",
]

_RESUME_BANK = [
    "Walk me through a project on your resume that you're most proud of. What was your specific contribution?",
    "Tell me about a technical challenge you faced in one of the projects listed on your resume, and how you resolved it.",
]

_ROLE_SPECIFIC_BANK = [
    "Why are you interested in the {role} role, and what makes you a strong fit for it?",
    "What do you think are the most important skills for a successful {role}, and how do you measure up?",
]

_COMPANY_CONTEXT_BANK = [
    "What do you know about {company}'s work, and why do you want to interview for this role specifically?",
    "How would your background contribute to the team at {company} on day one?",
]

_BETTER_ANSWER_FRAMEWORKS = {
    INTERVIEW_MODE_TECHNICAL: (
        "State the core concept in one sentence, walk through a concrete example, then note a "
        "trade-off or edge case to show depth."
    ),
    "default": (
        "Structure your answer with STAR: briefly set the Situation and Task, describe the specific "
        "Action you took, and close with a measurable Result."
    ),
}


def _significant_words(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    stopwords = {"the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "your", "you"}
    return {w for w in words if len(w) >= 4 and w not in stopwords}


def start_session(
    db: Session,
    student_profile: StudentProfile,
    mode: str,
    target_role_id: uuid.UUID | None = None,
    job_description_id: uuid.UUID | None = None,
    company_name: str | None = None,
) -> InterviewSession:
    target_role = None
    if target_role_id is not None:
        target_role = db.get(TargetRole, target_role_id)
        if target_role is None or target_role.student_profile_id != student_profile.id:
            raise NotFoundError("Target role not found.")
    job_description = None
    if job_description_id is not None:
        job_description = db.get(JobDescription, job_description_id)
        if job_description is None or job_description.student_profile_id != student_profile.id:
            raise NotFoundError("Job description not found.")

    session = InterviewSession(
        student_profile_id=student_profile.id,
        mode=mode,
        target_role_id=target_role.id if target_role else None,
        job_description_id=job_description.id if job_description else None,
        company_name=company_name or (job_description.company if job_description else None),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    _generate_questions(db, session, student_profile, target_role, job_description)
    db.commit()
    db.refresh(session)
    return session


def _make_question(session: InterviewSession, order_index: int, mode: str, prompt: str, **kwargs) -> InterviewQuestion:
    return InterviewQuestion(
        session_id=session.id,
        order_index=order_index,
        mode=mode,
        prompt=prompt,
        question_source=kwargs.get("question_source", "bank"),
        concept_id=kwargs.get("concept_id"),
        expected_keywords=kwargs.get("expected_keywords", []),
    )


def _generate_questions(
    db: Session,
    session: InterviewSession,
    student_profile: StudentProfile,
    target_role: TargetRole | None,
    job_description: JobDescription | None,
) -> None:
    rng = random.Random(str(session.id))
    role_title = target_role.title if target_role else "this role"
    company = session.company_name or (job_description.company if job_description else None) or "this company"

    def _tech_q(order: int) -> InterviewQuestion:
        prompt, keywords, concept_slug, _domain_slug = rng.choice(_TECHNICAL_BANK)
        concept = db.scalar(select(Concept).where(Concept.slug == concept_slug))
        return _make_question(
            session, order, INTERVIEW_MODE_TECHNICAL, prompt,
            expected_keywords=keywords, concept_id=concept.id if concept else None,
        )

    def _hr_q(order: int) -> InterviewQuestion:
        return _make_question(session, order, INTERVIEW_MODE_HR, rng.choice(_HR_BANK))

    def _resume_q(order: int) -> InterviewQuestion:
        return _make_question(session, order, INTERVIEW_MODE_RESUME, rng.choice(_RESUME_BANK), question_source="resume")

    def _role_q(order: int) -> InterviewQuestion:
        prompt = rng.choice(_ROLE_SPECIFIC_BANK).format(role=role_title)
        return _make_question(session, order, INTERVIEW_MODE_ROLE_SPECIFIC, prompt, question_source="job_description")

    def _company_q(order: int) -> InterviewQuestion:
        prompt = rng.choice(_COMPANY_CONTEXT_BANK).format(company=company)
        return _make_question(session, order, INTERVIEW_MODE_COMPANY_CONTEXT, prompt, question_source="job_description")

    builders = {
        INTERVIEW_MODE_TECHNICAL: [_tech_q, _tech_q],
        INTERVIEW_MODE_HR: [_hr_q, _hr_q],
        INTERVIEW_MODE_RESUME: [_resume_q, _hr_q],
        INTERVIEW_MODE_ROLE_SPECIFIC: [_role_q, _hr_q],
        INTERVIEW_MODE_COMPANY_CONTEXT: [_company_q, _role_q],
        "mixed": [_hr_q, _tech_q, _resume_q, _role_q if job_description or target_role else _hr_q],
    }
    question_builders = builders.get(session.mode, [_hr_q, _hr_q])
    for order, builder in enumerate(question_builders):
        db.add(builder(order))


def get_session(db: Session, session_id: uuid.UUID) -> InterviewSession | None:
    return db.get(InterviewSession, session_id)


def get_next_question(session: InterviewSession) -> InterviewQuestion | None:
    for question in session.questions:
        if question.answer is None:
            return question
    return None


def _record(agent_name: str, prompt_version: str, input_payload: dict, output: AgentOutput, latency_ms: float) -> AgentRunRecord:
    return AgentRunRecord(
        agent_name=agent_name,
        prompt_version=prompt_version,
        input_payload=input_payload,
        output_payload=output.model_dump(),
        confidence=output.confidence,
        evidence_citations=output.evidence_ids,
        inference_type=output.inference_type,
        latency_ms=latency_ms,
    )


def _validate_audio_upload(audio_bytes: bytes, audio_filename: str | None, audio_mime_type: str | None) -> None:
    settings = get_settings()
    if len(audio_bytes) > settings.max_audio_upload_bytes:
        raise UnprocessableError(
            f"Audio recording exceeds the {settings.max_audio_upload_bytes // (1024 * 1024)}MB upload limit."
        )
    suffix = Path(audio_filename or "").suffix.lower()
    if suffix and suffix not in storage.AUDIO_SUFFIXES:
        raise UnprocessableError("Unsupported audio file type.")
    if audio_mime_type and not audio_mime_type.startswith(_ALLOWED_AUDIO_MIME_PREFIXES):
        raise UnprocessableError("Unsupported audio content type.")


def submit_answer(
    db: Session,
    student_profile: StudentProfile,
    question: InterviewQuestion,
    audio_bytes: bytes | None = None,
    audio_filename: str | None = None,
    audio_mime_type: str | None = None,
    audio_duration_seconds: float | None = None,
    typed_answer_text: str | None = None,
) -> InterviewAnswer:
    if question.answer is not None:
        raise ConflictError("This question has already been answered.")

    audio_storage_path = None
    transcript = ""
    transcript_source = TRANSCRIPT_SOURCE_UNAVAILABLE

    if audio_bytes:
        _validate_audio_upload(audio_bytes, audio_filename, audio_mime_type)
        audio_storage_path = storage.save_audio(student_profile.id, audio_filename or "answer.webm", audio_bytes)
        result = get_speech_to_text_provider().transcribe(audio_bytes, audio_mime_type or "audio/webm")
        transcript = result.transcript
        transcript_source = result.source

    if not transcript.strip() and typed_answer_text and typed_answer_text.strip():
        transcript = typed_answer_text.strip()
        transcript_source = TRANSCRIPT_SOURCE_TYPED

    if not transcript.strip():
        raise UnprocessableError(
            "The recording could not be transcribed and no typed answer was provided. "
            "Please type your answer to continue."
        )

    answer = InterviewAnswer(
        question_id=question.id,
        audio_storage_path=audio_storage_path,
        audio_mime_type=audio_mime_type,
        audio_duration_seconds=audio_duration_seconds,
        transcript=transcript,
        transcript_source=transcript_source,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


@dataclass
class _ModeContext:
    resume_text: str
    resume_id: uuid.UUID | None
    jd_text: str


def evaluate_answer(
    db: Session, student_profile: StudentProfile, session: InterviewSession, question: InterviewQuestion, answer: InterviewAnswer
) -> InterviewEvaluation:
    resume = get_latest_resume(db, student_profile.id)
    ctx = _ModeContext(
        resume_text=resume.raw_text if resume else "",
        resume_id=resume.id if resume else None,
        jd_text=session.job_description.raw_text if session.job_description else "",
    )

    communication_output, comm_latency = CommunicationAgent().safe_run(
        CommunicationInput(
            transcript=answer.transcript,
            audio_duration_seconds=float(answer.audio_duration_seconds) if answer.audio_duration_seconds else None,
            check_star_structure=question.mode in (INTERVIEW_MODE_HR, INTERVIEW_MODE_RESUME),
        )
    )
    communication_record = _record("communication", CommunicationAgent.prompt_version, {}, communication_output, comm_latency)

    evidence_conflict, evidence_count, evidence_quality = _initial_evidence_state(question, answer, ctx)

    state: dict = {}

    def _graphrag_step(factors: RoutingFactors) -> StepOutcome:
        agent_runs: list[AgentRunRecord] = []
        output: dict = {}
        retrieval_confidence = 0.4
        new_quality = factors.evidence_quality
        new_count = factors.evidence_count

        if question.mode in (INTERVIEW_MODE_ROLE_SPECIFIC, INTERVIEW_MODE_COMPANY_CONTEXT):
            jd_agent = JDAlignmentAgent()
            out, latency = jd_agent.safe_run(JDAlignmentInput(transcript=answer.transcript, job_description_text=ctx.jd_text))
            state["jd_alignment"] = out
            agent_runs.append(_record(jd_agent.name, jd_agent.prompt_version, {"has_job_description": bool(ctx.jd_text)}, out, latency))
            retrieval_confidence = out.confidence
            new_quality = 0.75 if ctx.jd_text else 0.25
            new_count = 2 if ctx.jd_text else 0
            output = out.model_dump()
        elif question.mode == INTERVIEW_MODE_RESUME:
            retrieval_confidence = 0.7 if ctx.resume_text else 0.2
            new_quality = 0.7 if ctx.resume_text else 0.2
            new_count = 2 if ctx.resume_text else 0
            output = {"resume_available": bool(ctx.resume_text)}
        else:
            memory_agent = MemoryAgent(db)
            mem_out, latency = memory_agent.safe_run(MemoryInput(student_profile_id=student_profile.id))
            agent_runs.append(_record(memory_agent.name, memory_agent.prompt_version, {}, mem_out, latency))
            retrieval_confidence = 0.4
            output = mem_out.model_dump()

        updated = factors.model_copy(
            update={
                "retrieval_attempted": True,
                "retrieval_confidence": retrieval_confidence,
                "evidence_quality": new_quality,
                "evidence_count": new_count,
            }
        )
        return StepOutcome(factors=updated, output=output, evidence_ids=[], agent_runs=agent_runs)

    def _run_primary(factors: RoutingFactors) -> tuple[dict, list[AgentRunRecord], list[dict], list[float]]:
        agent_runs: list[AgentRunRecord] = []
        dims: dict[str, float] = {}
        evidence_checks: list[dict] = []
        confidences: list[float] = []

        if question.mode == INTERVIEW_MODE_TECHNICAL:
            tech_agent = TechnicalAgent()
            concept_name = question.concept.name if question.concept else ""
            tech_out, latency = tech_agent.safe_run(
                TechnicalInterviewInput(
                    question_prompt=question.prompt,
                    transcript=answer.transcript,
                    expected_keywords=question.expected_keywords,
                    concept_name=concept_name,
                )
            )
            state["technical_output"] = tech_out
            agent_runs.append(_record(tech_agent.name, tech_agent.prompt_version, {"question_id": str(question.id)}, tech_out, latency))
            dims.update({"relevance": tech_out.relevance_score, "correctness": tech_out.correctness_score, "depth": tech_out.depth_score})
            confidences.append(tech_out.confidence)
        else:
            hr_agent = HRAgent()
            hr_out, latency = hr_agent.safe_run(HRInterviewInput(question_prompt=question.prompt, transcript=answer.transcript))
            state["hr_output"] = hr_out
            agent_runs.append(_record(hr_agent.name, hr_agent.prompt_version, {"question_id": str(question.id)}, hr_out, latency))
            dims.update({"relevance": hr_out.relevance_score, "structure": hr_out.structure_score, "evidence": hr_out.evidence_score})
            confidences.append(hr_out.confidence)

            if question.mode == INTERVIEW_MODE_RESUME:
                re_agent = ResumeEvidenceAgent()
                re_out, re_latency = re_agent.safe_run(
                    ResumeEvidenceCheckInput(
                        claim_text=answer.transcript,
                        resume_text=ctx.resume_text,
                        evidence_ids=[str(ctx.resume_id)] if ctx.resume_id else [],
                    )
                )
                state["resume_evidence_output"] = re_out
                agent_runs.append(_record(re_agent.name, re_agent.prompt_version, {"has_resume": bool(ctx.resume_text)}, re_out, re_latency))
                evidence_checks.append(
                    {"claim": answer.transcript[:300], "classification": re_out.classification, "explanation": re_out.explanation_text}
                )
                confidences.append(re_out.confidence)

            jd_out = state.get("jd_alignment")
            if jd_out is not None and question.mode in (INTERVIEW_MODE_ROLE_SPECIFIC, INTERVIEW_MODE_COMPANY_CONTEXT):
                dims["role_alignment"] = jd_out.role_alignment_score
                confidences.append(jd_out.confidence)

        return dims, agent_runs, evidence_checks, confidences

    def _single_agent_step(factors: RoutingFactors) -> StepOutcome:
        if state.get("primary_confidence") is not None:
            return StepOutcome(factors=factors, output=state.get("primary_output", {}))

        dims, agent_runs, evidence_checks, confidences = _run_primary(factors)
        primary_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0
        output = {"dimension_scores": dims}
        state["primary_confidence"] = primary_confidence
        state["primary_output"] = output
        state["evidence_checks"] = evidence_checks
        updated = factors.model_copy(update={"agent_confidence": primary_confidence})
        return StepOutcome(factors=updated, output=output, evidence_ids=[], agent_runs=agent_runs)

    def _multi_agent_step(factors: RoutingFactors) -> StepOutcome:
        agent_runs: list[AgentRunRecord] = []
        votes: list[ConsensusVote] = []

        if state.get("primary_confidence") is None:
            dims, primary_runs, evidence_checks, confidences = _run_primary(factors)
            agent_runs.extend(primary_runs)
            primary_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.0
            state["primary_confidence"] = primary_confidence
            state["primary_output"] = {"dimension_scores": dims}
            state["evidence_checks"] = evidence_checks

        votes.append(ConsensusVote(agent_name="primary_specialist", confidence=state["primary_confidence"]))

        if question.mode == INTERVIEW_MODE_TECHNICAL:
            hr_agent = HRAgent()
            hr_out, hr_latency = hr_agent.safe_run(HRInterviewInput(question_prompt=question.prompt, transcript=answer.transcript))
            agent_runs.append(_record(hr_agent.name, hr_agent.prompt_version, {}, hr_out, hr_latency))
            votes.append(ConsensusVote(agent_name="hr_secondary", confidence=hr_out.confidence))
        elif "resume_evidence_output" not in state:
            re_agent = ResumeEvidenceAgent()
            re_out, re_latency = re_agent.safe_run(
                ResumeEvidenceCheckInput(claim_text=answer.transcript, resume_text=ctx.resume_text)
            )
            state["resume_evidence_output"] = re_out
            agent_runs.append(_record(re_agent.name, re_agent.prompt_version, {}, re_out, re_latency))
            state.setdefault("evidence_checks", []).append(
                {"claim": answer.transcript[:300], "classification": re_out.classification, "explanation": re_out.explanation_text}
            )
            votes.append(ConsensusVote(agent_name="resume_evidence", confidence=re_out.confidence))

        memory_agent = MemoryAgent(db)
        mem_out, mem_latency = memory_agent.safe_run(MemoryInput(student_profile_id=student_profile.id))
        agent_runs.append(_record(memory_agent.name, memory_agent.prompt_version, {}, mem_out, mem_latency))

        consensus_agent = ConsensusAgent()
        consensus_out, consensus_latency = consensus_agent.safe_run(ConsensusInput(votes=votes))
        agent_runs.append(
            _record(consensus_agent.name, consensus_agent.prompt_version, {"vote_count": len(votes)}, consensus_out, consensus_latency)
        )

        state["primary_confidence"] = consensus_out.consensus_confidence
        state["primary_output"] = {**state.get("primary_output", {}), "consensus": consensus_out.model_dump()}
        state["council_claims"] = [{"agent_name": v.agent_name, "confidence": v.confidence, "evidence_ids": []} for v in votes]

        updated = factors.model_copy(
            update={
                "agent_confidence": consensus_out.consensus_confidence,
                "agent_disagreement": consensus_out.disagreement,
                "multi_agent_attempted": True,
            }
        )
        return StepOutcome(factors=updated, output=state["primary_output"], evidence_ids=[], agent_runs=agent_runs)

    def _critic_step(factors: RoutingFactors) -> StepOutcome:
        claims = [CriticClaim(**c) for c in state.get("council_claims", [])]
        critic_agent = CriticAgent()
        out, latency = critic_agent.safe_run(CriticInput(claims=claims))
        state["primary_confidence"] = out.adjusted_confidence
        state["critic_output"] = out
        updated = factors.model_copy(update={"agent_confidence": out.adjusted_confidence})
        return StepOutcome(
            factors=updated,
            output={**state.get("primary_output", {}), "critic": out.model_dump()},
            evidence_ids=[],
            agent_runs=[_record(critic_agent.name, critic_agent.prompt_version, {}, out, latency)],
        )

    initial_factors = RoutingFactors(
        task_type=_TASK_TYPE,
        task_risk="high" if question.mode == INTERVIEW_MODE_RESUME else "medium",
        student_impact_level="medium",
        evidence_count=evidence_count,
        evidence_quality=evidence_quality,
        evidence_conflict=evidence_conflict,
        deterministic_eligible=False,
        min_evidence_for_confidence=2,
    )
    execution, _output = run_care_task(
        db,
        student_profile.id,
        _TASK_TYPE,
        request_summary=f"Evaluate a {question.mode} interview answer.",
        factors=initial_factors,
        executors={
            "graphrag_agent": _graphrag_step,
            "single_agent": _single_agent_step,
            "multi_agent": _multi_agent_step,
            "critic_reflection": _critic_step,
        },
        input_evidence_ids=[str(ctx.resume_id)] if ctx.resume_id else [],
    )

    # CommunicationAgent runs unconditionally (see module docstring) and is
    # therefore not one of run_care_task's route-dependent executors -- append
    # it to the persisted execution directly so the Trust Center still shows
    # it as part of this decision's agent trace.
    execution.agent_runs.append(
        AgentRun(
            agent_name=communication_record.agent_name,
            prompt_version=communication_record.prompt_version,
            input_payload=communication_record.input_payload,
            output_payload=communication_record.output_payload,
            confidence=communication_record.confidence,
            evidence_citations=communication_record.evidence_citations,
            inference_type=communication_record.inference_type,
            latency_ms=communication_record.latency_ms,
        )
    )
    if "communication" not in execution.agents_invoked:
        execution.agents_invoked = [*execution.agents_invoked, "communication"]
    db.commit()
    db.refresh(execution)

    dims: dict = state.get("primary_output", {}).get("dimension_scores", {})
    comm_dims = {
        "clarity": communication_output.clarity_score,
        "conciseness": communication_output.conciseness_score,
        "professional_communication": communication_output.professional_communication_score,
    }
    all_dims = {**dims, **comm_dims}
    overall_score = round(sum(all_dims.values()) / len(all_dims), 4) if all_dims else 0.0

    strengths, improvements = _derive_strengths_and_improvements(dims, communication_output, state)
    timeline_markers = _derive_timeline_markers(answer.transcript, communication_output, state.get("evidence_checks", []))
    better_answer = _BETTER_ANSWER_FRAMEWORKS.get(question.mode, _BETTER_ANSWER_FRAMEWORKS["default"])

    evaluation = InterviewEvaluation(
        answer_id=answer.id,
        care_execution_id=execution.id,
        dimension_scores=all_dims,
        overall_score=overall_score,
        confidence=float(execution.confidence),
        agreement=float(execution.agreement) if execution.agreement is not None else None,
        strengths=strengths,
        improvements=improvements,
        evidence_checks=state.get("evidence_checks", []),
        communication_metrics=communication_output.model_dump(),
        timeline_markers=timeline_markers,
        better_answer_framework=better_answer,
        requires_human_review=execution.requires_human_review,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    _record_interview_evidence(db, student_profile, question, evaluation)
    return evaluation


def _initial_evidence_state(question: InterviewQuestion, answer: InterviewAnswer, ctx: _ModeContext) -> tuple[bool, int, float]:
    word_count = len(answer.transcript.split())
    too_thin = word_count < _MIN_WORDS_FOR_CONFIDENT_ANSWER

    off_topic = False
    if question.mode == INTERVIEW_MODE_TECHNICAL and question.expected_keywords:
        transcript_lower = answer.transcript.lower()
        off_topic = not any(k.lower() in transcript_lower for k in question.expected_keywords)
    elif question.mode in (INTERVIEW_MODE_HR, INTERVIEW_MODE_RESUME):
        prompt_terms = _significant_words(question.prompt)
        off_topic = bool(prompt_terms) and not (prompt_terms & _significant_words(answer.transcript))

    missing_context = False
    if question.mode == INTERVIEW_MODE_RESUME and not ctx.resume_text:
        missing_context = True
    if question.mode in (INTERVIEW_MODE_ROLE_SPECIFIC, INTERVIEW_MODE_COMPANY_CONTEXT) and not ctx.jd_text:
        missing_context = True

    evidence_conflict = too_thin or off_topic or missing_context

    if question.mode == INTERVIEW_MODE_TECHNICAL:
        evidence_count, evidence_quality = 2, 0.7
    elif question.mode == INTERVIEW_MODE_HR:
        evidence_count, evidence_quality = 2, 0.6
    elif question.mode == INTERVIEW_MODE_RESUME:
        evidence_count, evidence_quality = 0, 0.2
    else:
        evidence_count, evidence_quality = 1 if ctx.jd_text else 0, 0.5 if ctx.jd_text else 0.2

    return evidence_conflict, evidence_count, evidence_quality


def _derive_strengths_and_improvements(dims: dict, communication_output, state: dict) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    improvements: list[str] = []

    for name, score in dims.items():
        label = name.replace("_", " ")
        if score >= 0.7:
            strengths.append(f"Strong {label}.")
        elif score < 0.5:
            improvements.append(f"Work on {label} -- this scored below the target range.")

    if communication_output.filler_ratio > 0.08:
        improvements.append("Reduce filler words (um, uh, you know) to sound more confident and concise.")
    else:
        strengths.append("Clear, filler-light delivery.")

    if communication_output.conciseness_score >= 0.8:
        strengths.append("Answer length was well-calibrated -- not too short, not rambling.")
    elif communication_output.word_count < 30:
        improvements.append("Answer was quite short -- add more detail and a concrete example.")

    if communication_output.star_components_found and len(communication_output.star_components_found) < 4:
        missing = {"situation", "task", "action", "result"} - set(communication_output.star_components_found)
        improvements.append(f"Strengthen the missing STAR component(s): {', '.join(sorted(missing))}.")
    elif len(communication_output.star_components_found) == 4:
        strengths.append("Answer follows a complete STAR structure (Situation, Task, Action, Result).")

    for check in state.get("evidence_checks", []):
        if check["classification"] in ("not_currently_supported", "contradicted_by_uploaded_evidence"):
            improvements.append(check["explanation"])
        elif check["classification"] == "supported_by_resume_evidence":
            strengths.append("This claim is well grounded in your uploaded resume evidence.")

    return strengths[:6], improvements[:6]


def _derive_timeline_markers(transcript: str, communication_output, evidence_checks: list[dict]) -> list[dict]:
    markers: list[dict] = []
    if not transcript.strip():
        return markers
    total_len = max(len(transcript), 1)

    first_sentence = re.split(r"[.!?]", transcript, maxsplit=1)[0]
    if len(first_sentence.split()) >= 5:
        markers.append({"type": "strong_introduction", "label": "Confident, substantive opening.", "position_percent": 0.0})

    if communication_output.filler_ratio > 0.08:
        match = re.search(r"\b(um+|uh+|you know|sort of|kind of)\b", transcript, re.IGNORECASE)
        position = round((match.start() / total_len) * 100, 1) if match else 10.0
        markers.append(
            {"type": "excessive_filler_words", "label": f"Filler words made up {communication_output.filler_ratio:.0%} of the answer.", "position_percent": position}
        )

    if evidence_checks:
        for check in evidence_checks:
            if check["classification"] in ("not_currently_supported", "contradicted_by_uploaded_evidence"):
                markers.append({"type": "unsupported_claim", "label": check["explanation"], "position_percent": 50.0})
                break

    if communication_output.star_components_found and "result" in communication_output.star_components_found:
        markers.append({"type": "strong_example", "label": "Answer closes with a measurable result.", "position_percent": 80.0})

    last_sentence = [s for s in re.split(r"[.!?]", transcript) if s.strip()]
    if last_sentence and len(last_sentence[-1].split()) < 4:
        markers.append({"type": "missing_conclusion", "label": "Answer trails off without a clear closing statement.", "position_percent": 95.0})

    return markers


def _record_interview_evidence(
    db: Session, student_profile: StudentProfile, question: InterviewQuestion, evaluation: InterviewEvaluation
) -> None:
    communication_skill = db.scalar(select(Skill).where(Skill.name == "Communication"))
    comm_score = evaluation.communication_metrics.get("professional_communication_score", 0.0)
    if communication_skill is not None:
        db.add(
            SkillEvidence(
                student_profile_id=student_profile.id,
                skill_id=communication_skill.id,
                evidence_type=EVIDENCE_TYPE_INTERVIEW,
                source_object_type="interview_answer",
                source_object_id=evaluation.answer_id,
                raw_score=comm_score,
                normalized_score=comm_score,
                weight=0.85,
                confidence=float(evaluation.confidence),
                explanation=(
                    f"Interview answer ({question.mode}) communication metrics: "
                    f"clarity {evaluation.communication_metrics.get('clarity_score', 0):.2f}, "
                    f"conciseness {evaluation.communication_metrics.get('conciseness_score', 0):.2f}."
                ),
            )
        )

    if question.concept is not None and question.concept.skill_id is not None:
        technical_dims = {k: v for k, v in evaluation.dimension_scores.items() if k in ("relevance", "correctness", "depth")}
        if technical_dims:
            tech_score = round(sum(technical_dims.values()) / len(technical_dims), 4)
            db.add(
                SkillEvidence(
                    student_profile_id=student_profile.id,
                    skill_id=question.concept.skill_id,
                    concept_id=question.concept.id,
                    evidence_type=EVIDENCE_TYPE_INTERVIEW,
                    source_object_type="interview_answer",
                    source_object_id=evaluation.answer_id,
                    raw_score=tech_score,
                    normalized_score=tech_score,
                    weight=0.9,
                    confidence=float(evaluation.confidence),
                    explanation=f"Technical interview answer on '{question.concept.name}' scored {tech_score:.2f}.",
                )
            )
    db.commit()


def complete_session(db: Session, student_profile: StudentProfile, session: InterviewSession) -> InterviewSession:
    evaluations = [q.answer.evaluation for q in session.questions if q.answer is not None and q.answer.evaluation is not None]
    if evaluations:
        session.overall_score = round(sum(float(e.overall_score) for e in evaluations) / len(evaluations), 4)
        session.overall_confidence = round(sum(float(e.confidence) for e in evaluations) / len(evaluations), 4)
    session.status = INTERVIEW_STATUS_COMPLETED
    session.completed_at = utcnow()
    db.commit()
    db.refresh(session)

    if evaluations:
        recompute_twin(db, student_profile, reason=f"Completed a {session.mode} mock interview ({len(evaluations)} question(s)).")
    return session
