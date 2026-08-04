from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.assessments import router as assessments_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.career_twin import router as career_twin_router
from app.api.dashboard import router as dashboard_router
from app.api.experiments import router as experiments_router
from app.api.graphrag import router as graphrag_router
from app.api.health import router as health_router
from app.api.interviews import router as interviews_router
from app.api.job_descriptions import router as job_descriptions_router
from app.api.missions import router as missions_router
from app.api.onboarding import router as onboarding_router
from app.api.resources import router as resources_router
from app.api.resumes import router as resumes_router
from app.api.skills import router as skills_router
from app.api.students import router as students_router
from app.api.trust_center import router as trust_center_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging

settings = get_settings()
configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Evidence-grounded adaptive agentic career intelligence API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(students_router, prefix=settings.api_v1_prefix)
app.include_router(onboarding_router, prefix=settings.api_v1_prefix)
app.include_router(resumes_router, prefix=settings.api_v1_prefix)
app.include_router(job_descriptions_router, prefix=settings.api_v1_prefix)
app.include_router(career_twin_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(missions_router, prefix=settings.api_v1_prefix)
app.include_router(audit_router, prefix=settings.api_v1_prefix)
app.include_router(skills_router, prefix=settings.api_v1_prefix)
app.include_router(graphrag_router, prefix=settings.api_v1_prefix)
app.include_router(assessments_router, prefix=settings.api_v1_prefix)
app.include_router(resources_router, prefix=settings.api_v1_prefix)
app.include_router(trust_center_router, prefix=settings.api_v1_prefix)
app.include_router(interviews_router, prefix=settings.api_v1_prefix)
app.include_router(experiments_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "CareerPilot AI",
        "phase": "Phase 1 foundation",
        "docs": "/docs",
    }
