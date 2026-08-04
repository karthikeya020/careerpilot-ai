# Phase 1 — Start Here

> **Status: Phase 1 is implemented.** See `docs/implementation/PHASE_1_COMPLETION_REPORT.md`
> for what was built, exact run commands, and demo credentials. This file is kept as the
> original planning brief.

## Goal

Create the foundation on which every advanced AI capability can be safely built.

## First Sprint Tasks

1. Install Docker Desktop, Python 3.11+, Node.js LTS, and Git.
2. Run `scripts/start_infrastructure.ps1`.
3. Run `scripts/start_backend.ps1`.
4. Open `http://localhost:8000/docs`.
5. Confirm `GET /api/v1/health` returns `status: ok`.
6. Initialize the Next.js frontend inside `frontend/`.
7. Implement registration, login, and student onboarding.
8. Connect PostgreSQL using SQLAlchemy and Alembic.
9. Build the static Career OS shell.
10. Seed one demo student account.

## Phase 1 Exit Test

A demo student can sign in, complete profile onboarding, and view a Career OS shell populated by real API/database data.
