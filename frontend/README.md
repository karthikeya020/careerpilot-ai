# CareerPilot Frontend — Career OS

Next.js (App Router) + TypeScript + Tailwind CSS v4 frontend for CareerPilot AI.

## Stack

- **Next.js 16** (App Router, Turbopack) + **React 19** + **TypeScript**
- **Tailwind CSS v4** (CSS-first config, dark/light theme via a `.dark` class + manual toggle)
- Hand-built shadcn/ui-style component primitives (`components/ui/*`) on top of Radix UI
  primitives (`@radix-ui/react-*`) — kept small and auditable rather than pulling the full
  shadcn CLI
- **@tanstack/react-query** for server state (`hooks/*`)
- **react-hook-form** + **zod** (`lib/schemas.ts`) for form validation
- **recharts** for the readiness radar chart
- **sonner** for toasts
- **vitest** + **@testing-library/react** for component tests

## Pages

| Route | Purpose |
|---|---|
| `/` | Landing page |
| `/register`, `/login` | Auth |
| `/demo` | One-click sign-in as the seeded demo student |
| `/onboarding` | Target role, career goal, self-assessed skills |
| `/dashboard` | Career OS home — readiness, mission, evidence, trust |
| `/career-twin` | Full Career Twin snapshot + version history |
| `/resume` | Upload + parsed sections/skills |
| `/job-description` | Paste a JD, see matched/partial/missing skills |
| `/settings` | Account, profile, audit trail |

## Auth model

Access token lives in memory + `localStorage` (`lib/token-store.ts`); the refresh token is an
httpOnly cookie set by the backend. `lib/api-client.ts` auto-retries a request once on 401 by
calling `/auth/refresh`. Storing the access token in `localStorage` is a known Phase 2 hardening
item (see `docs/implementation/PHASE_1_EXECUTION_PLAN.md`) — acceptable for a Phase 1 foundation,
not for production as-is.

## Running locally

```bash
npm install
cp .env.local.example .env.local   # points at the local backend by default
npm run dev
```

Requires the backend running at `http://localhost:8000` (see `../backend/README` / root `README.md`).

## Commands

```bash
npm run dev      # dev server (Turbopack)
npm run build    # production build (also type-checks)
npm run lint     # eslint
npx tsc --noEmit # type-check only
npm test         # vitest component tests
```
