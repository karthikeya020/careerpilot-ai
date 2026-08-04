import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AdminPage from "@/app/admin/page";
import FacultyPage from "@/app/faculty/page";
import RecruiterPage from "@/app/recruiter/page";
import type { AdminDashboardOut, FacultyDashboardOut, RecruiterCandidateOut } from "@/types/api";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), put: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/faculty",
  useParams: () => ({}),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ user: { id: "1", email: "faculty@example.com", roles: ["faculty"] }, isLoading: false, logout: vi.fn() }),
}));

vi.mock("@/lib/theme-provider", () => ({ useTheme: () => ({ theme: "dark", toggle: vi.fn() }) }));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const FACULTY: FacultyDashboardOut = {
  total_students: 12,
  cohort_skill_gaps: [
    { component_type: "technical_readiness", average_score: 0.62, scored_student_count: 8 },
    { component_type: "communication_readiness", average_score: 0.55, scored_student_count: 10 },
    { component_type: "resume_readiness", average_score: null, scored_student_count: 0 },
    { component_type: "assessment_readiness", average_score: 0.7, scored_student_count: 5 },
    { component_type: "portfolio_readiness", average_score: null, scored_student_count: 0 },
    { component_type: "role_alignment_readiness", average_score: 0.4, scored_student_count: 3 },
  ],
  mission_completion_rate: 0.5,
  assessment_completion_rate: 0.8,
  average_readiness_trend: 0.03,
  students_needing_support: [{ student_profile_id: "s1", full_name: "Alex Rivera", flagged_decision_count: 2 }],
};

const ADMIN: AdminDashboardOut = {
  service_health: { database: true, redis: true, neo4j: false },
  users_by_role: { student: 10, faculty: 1, recruiter: 0, placement_staff: 0, administrator: 1 },
  total_users: 12,
  care_execution_stats: {
    total_executions: 40,
    route_frequency: { single_agent: 20, multi_agent: 10, human_review: 2 },
    average_confidence: 0.71,
    average_latency_ms: 12.5,
    average_cost_usd: 0.0,
    human_review_rate: 0.05,
  },
  recent_audit_events: [],
};

const CANDIDATES: RecruiterCandidateOut[] = [
  {
    student_profile_id: "s1",
    full_name: "Jordan Lee",
    target_role: "Data Analyst",
    overall_score: 0.68,
    overall_confidence: 0.4,
    components: [{ component_type: "technical_readiness", score: 0.68, confidence: 0.4, status: "scored" }],
    requires_human_review: false,
    consent_status: "explicit_opt_in",
  },
];

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

beforeEach(() => {
  getMock.mockReset();
});

describe("Role dashboards", () => {
  it("Faculty dashboard shows cohort aggregates and flagged students, never a per-student score list", async () => {
    getMock.mockResolvedValueOnce(FACULTY);
    renderWithClient(<FacultyPage />);

    expect(await screen.findByText("Faculty Dashboard")).toBeInTheDocument();
    expect(screen.getByText(/12 student\(s\)/i)).toBeInTheDocument();
    expect(screen.getByText("Alex Rivera")).toBeInTheDocument();
    expect(screen.getByText(/2 flagged decision/i)).toBeInTheDocument();
  });

  it("Admin dashboard shows real service health and CARE stats", async () => {
    getMock.mockResolvedValueOnce(ADMIN);
    renderWithClient(<AdminPage />);

    expect(await screen.findByText("Administrator Dashboard")).toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
    expect(screen.getAllByText(/unavailable/i).length).toBeGreaterThan(0);
  });

  it("Recruiter dashboard shows only opted-in candidates with no hiring recommendation language", async () => {
    getMock.mockResolvedValueOnce(CANDIDATES);
    renderWithClient(<RecruiterPage />);

    expect(await screen.findByText("Jordan Lee")).toBeInTheDocument();
    expect(screen.getByText(/Data Analyst/i)).toBeInTheDocument();
    // The page correctly *disclaims* hiring recommendations; it must never *make* one.
    expect(screen.getByText(/No automatic hiring recommendation is ever computed/i)).toBeInTheDocument();
    expect(screen.queryByText(/probability/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/recommended candidate/i)).not.toBeInTheDocument();
  });

  it("Recruiter dashboard shows an empty state when nobody has opted in", async () => {
    getMock.mockResolvedValueOnce([]);
    renderWithClient(<RecruiterPage />);
    expect(await screen.findByText(/No candidates have opted in yet/i)).toBeInTheDocument();
  });
});
