import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import CareerTwinPage from "@/app/career-twin/page";
import type { CareerTwinSnapshotOut, ComponentProjectionOut, RoleAlignmentOut, StudentGraphOverviewOut } from "@/types/api";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/career-twin",
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
    score: 0.75,
    confidence: 0.6,
    status: "scored" as const,
    evidence_count: 4,
    explanation: "Derived from real evidence.",
    trend: 0.1,
    uncertainty: 0.4,
    evidence_diversity: 2,
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
  version: 3,
  overall_score: 0.72,
  overall_confidence: 0.55,
  evidence_count: 10,
  formula_version: "twin-v2",
  change_summary: "Technical readiness improved.",
  score_delta: 0.05,
  created_at: "2026-08-06T00:00:00Z",
  components: [
    makeComponent({ component_type: "technical_readiness", score: 0.72 }),
    makeComponent({ component_type: "role_alignment_readiness", score: 0.5 }),
  ],
  milestones: ["Technical crossed 70% readiness for the first time."],
};

const ROLE_ALIGNMENTS: RoleAlignmentOut[] = [
  { role_title: "Data Analyst", alignment: 0.72, matched_skills: ["SQL", "Python"], missing_skills: [] },
  { role_title: "Software Engineer", alignment: 0.58, matched_skills: ["Python"], missing_skills: ["Data Structures"] },
];

const PROJECTIONS: ComponentProjectionOut[] = [
  {
    component_type: "technical_readiness",
    current_score: 0.55,
    status: "projected",
    weeks_to_target: 6,
    weeks_to_target_low: 4,
    weeks_to_target_high: 9,
    weekly_rate: 0.02,
    note: "Estimated from your own historical rate. This is a heuristic, not a guarantee.",
  },
];

const GRAPH_OVERVIEW: Partial<StudentGraphOverviewOut> = {
  graph_source: "neo4j",
  strengths: [
    {
      concept_slug: "python-basics",
      concept_name: "Python Fundamentals",
      domain_name: "Python",
      status: "strong",
      mastery: 0.85,
      confidence: 0.7,
      evidence_count: 3,
      reasoning: "Based on 3 pieces of real evidence, your mastery is 85%.",
      depends_on: [],
      blocks: [],
      target_role_relevant: true,
      recommended_resource: null,
      practice_available: false,
      questions_answered: 2,
      questions_total: 2,
    },
  ],
  weaknesses: [],
  concepts_with_evidence: 5,
  total_concepts: 10,
  overall_mastery: 0.6,
};

function mockEndpoints() {
  getMock.mockImplementation((url: string) => {
    if (url === "/career-twin") return Promise.resolve(SNAPSHOT);
    if (url === "/career-twin/history") return Promise.resolve([SNAPSHOT]);
    if (url === "/career-twin/multi-role") return Promise.resolve(ROLE_ALIGNMENTS);
    if (url === "/career-twin/time-to-target") return Promise.resolve(PROJECTIONS);
    if (url === "/graph/student-overview") return Promise.resolve(GRAPH_OVERVIEW);
    return Promise.resolve(null);
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <CareerTwinPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
});

describe("CareerTwinPage", () => {
  it("shows a milestone banner when the snapshot crossed a threshold", async () => {
    mockEndpoints();
    renderPage();
    expect(await screen.findByText(/crossed 70% readiness for the first time/i)).toBeInTheDocument();
  });

  it("renders the multi-role alignment panel with per-role percentages", async () => {
    mockEndpoints();
    renderPage();
    expect(await screen.findByText("Data Analyst")).toBeInTheDocument();
    expect(await screen.findByText("Software Engineer")).toBeInTheDocument();
    expect(screen.getAllByText("72%").length).toBeGreaterThan(0);
  });

  it("renders the time-to-target projection with a heuristic disclaimer", async () => {
    mockEndpoints();
    renderPage();
    expect(await screen.findByText(/time to 70% readiness/i)).toBeInTheDocument();
    expect(await screen.findByText(/~6w/)).toBeInTheDocument();
  });

  it("renders the strength-chains panel reusing the GraphRAG overview", async () => {
    mockEndpoints();
    renderPage();
    expect(await screen.findByText(/what to lean into/i)).toBeInTheDocument();
    expect(await screen.findByText("Python Fundamentals")).toBeInTheDocument();
  });

  it("links to the exportable snapshot proof page", async () => {
    mockEndpoints();
    renderPage();
    const link = await screen.findByRole("link", { name: /export proof/i });
    expect(link).toHaveAttribute("href", "/career-twin/proof/snap-1");
  });
});
