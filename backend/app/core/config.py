import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent

# Stable for the lifetime of the process so tokens issued and verified within
# one dev/test run stay valid, without ever being an insecure hardcoded value.
_DEV_FALLBACK_JWT_SECRET = secrets.token_urlsafe(32)


class Settings(BaseSettings):
    app_name: str = "CareerPilot AI API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://careerpilot:careerpilot@localhost:5432/careerpilot"
    test_database_url: str = "sqlite:///./test_careerpilot.db"

    redis_url: str = "redis://localhost:6379/0"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "careerpilot-password"

    jwt_secret: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14

    cors_origins: list[str] = ["http://localhost:3000"]

    upload_dir: Path = BACKEND_ROOT / "var" / "uploads"
    max_upload_bytes: int = 5 * 1024 * 1024

    primary_llm_api_key: str = ""
    primary_llm_model: str = "claude-sonnet-4-5-20250929"
    secondary_llm_api_key: str = ""

    demo_student_email: str = "demo.student@careerpilot.ai"
    demo_student_password: str = "DemoPass!2026"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def effective_jwt_secret(self) -> str:
        if self.jwt_secret and self.jwt_secret != "change-me-in-env":
            return self.jwt_secret
        if self.is_production:
            raise RuntimeError("JWT_SECRET must be set explicitly in production")
        return _DEV_FALLBACK_JWT_SECRET


@lru_cache
def get_settings() -> Settings:
    return Settings()
