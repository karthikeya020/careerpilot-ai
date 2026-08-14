import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DashboardPage from "@/app/dashboard/page";
import type { CareerTwinSnapshotOut, DashboardOut } from "@/types/api";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard",
  useParams: () => ({}),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ user: { id: "1", email: "student@example.com", roles: ["student"] }, isLoading: false, logout: vi.fn() }),
}));

vi.mock("@/lib/theme-provider", () => ({ useTheme: () => ({ theme: "dark", toggle: vi.fn() }) }));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

function makeComponent(overrides: Partial<CareerTwinSnapshotOut["components"][number]> = {}) {
  return {
    component_type: "technical_readiness",
    score: 0.72,
    confidence: 0.55,
    status: "scored" as const,
    evidence_count: 12,
    explanation: "Derived from real evidence.",
    trend: 0.05,
    uncertainty: 0.45,
    evidence_diversity: 3,
    is_low_sample: false,
    low_sample_notice: null,
    stale_evidence_fraction: 0,
    is_stale_evidence: false,
    stale_evidence_notice: null,
    ripple_notes: [],
    provenance: { resume: 1.0 },
    ...overrides,
  };
}

const SNAPSHOT: CareerTwinSnapshotOut = {
  id: "snap-1",
  version: 5,
  overall_score: 0.72,
  overall_confidence: 0.35,
  evidence_count: 46,
  formula_version: "twin-v2",
  change_summary: "Completed a mixed mock interview.",
  score_delta: 0.07,
  created_at: "2026-08-06T00:00:00Z",
  components: [
    makeComponent({ component_type: "technical_readiness", score: 0.83, evidence_count: 21 }),
    makeComponent({ component_type: "resume_readiness", score: 0.72, evidence_count: 9 }),
    makeComponent({ component_type: "communication_readiness", score: 0.94, evidence_count: 7 }),
    makeComponent({ component_type: "assessment_readiness", score: 0.5, evidence_count: 2 }),
    makeComponent({ component_type: "portfolio_readiness", score: null, status: "insufficient_evidence", evidence_count: 0 }),
    makeComponent({ component_type: "role_alignment_readiness", score: 0.4, evidence_count: 7 }),
  ],
  milestones: ["Communication crossed 70% readiness for the first time."],
};

const HISTORY: CareerTwinSnapshotOut[] = [
  { ...SNAPSHOT, id: "snap-0", version: 4, overall_score: 0.6, milestones: [] },
  SNAPSHOT,
];

const DASHBOARD: DashboardOut = {
  student_name: "Aanya Sharma",
  onboarding_completed: true,
  target_role: { id: "role-1", title: "Backend Engineering Intern", seniority: "entry_level", is_primary: true },
  career_twin: SNAPSHOT,
  mission: null,
  priority_weakness: null,
  resume_status: { uploaded: true, filename: "resume.docx", parsing_status: "parsed", parsing_error: null, skills_detected: 9, uploaded_at: "2026-08-01T00:00:00Z" },
  job_description_status: { added: true, title: "Backend Engineering Intern", coverage: 0.8, matched_count: 8, partial_count: 1, missing_count: 1 },
  recent_evidence: [],
  recent_twin_updates: [],
  recent_audit_events: [],
  system_trust: { formula_version: "twin-v2", components_scored: 5, components_total: 6, total_evidence_count: 46 },
};

function mockEndpoints() {
  getMock.mockImplementation((url: string) => {
    if (url === "/dashboard") return Promise.resolve(DASHBOARD);
    if (url === "/career-twin/history") return Promise.resolve(HISTORY);
    return Promise.resolve(null);
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <DashboardPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
});

describe("DashboardPage", () => {
  it("renders the hero with the student's name and target role", async () => {
    mockEndpoints();
    renderPage();
    expect(await screen.findByText(/welcome back, aanya/i)).toBeInTheDocument();
    expect((await screen.findAllByText(/backend engineering intern/i)).length).toBeGreaterThan(0);
  });

  it("shows the milestone banner when the snapshot has one", async () => {
    mockEndpoints();
    renderPage();
    expect(await screen.findByText(/crossed 70% readiness for the first time/i)).toBeInTheDocument();
  });

  it("renders the readiness trend chart from real snapshot history", async () => {
    mockEndpoints();
    renderPage();
    expect(await screen.findByText(/readiness over time/i)).toBeInTheDocument();
    expect(await screen.findByRole("img", { name: /line chart of overall readiness/i })).toBeInTheDocument();
  });

  it("renders the evidence composition donut chart from real component data", async () => {
    mockEndpoints();
    renderPage();
    expect(await screen.findByText(/where your evidence comes from/i)).toBeInTheDocument();
    expect(await screen.findByRole("img", { name: /donut chart of evidence distribution/i })).toBeInTheDocument();
    expect(screen.getAllByText(/technical/i).length).toBeGreaterThan(0);
  });
});
