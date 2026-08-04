FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --upgrade pip && pip install .

EXPOSE 8000

# Run migrations, seed the demo student (idempotent -- safe on every
# restart), then start the API. Reference data (roles + skill taxonomy) is
# seeded by the migrations themselves.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed.seed_demo && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
