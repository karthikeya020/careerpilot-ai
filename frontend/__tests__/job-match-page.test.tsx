import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import JobDescriptionPage from "@/app/job-description/page";
import type { JobListingMatchOut, SectorOut, TrackedJobOut } from "@/types/api";

const { getMock, postMock, deleteMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
  deleteMock: vi.fn(),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: postMock, patch: vi.fn(), delete: deleteMock } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/job-description",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ user: { id: "1", email: "student@example.com", roles: ["student"] }, isLoading: false, logout: vi.fn() }),
}));

vi.mock("@/lib/theme-provider", () => ({ useTheme: () => ({ theme: "dark", toggle: vi.fn() }) }));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const SECTORS: SectorOut[] = [
  { slug: "faang", label: "FAANG / Big Tech", listing_count: 10 },
  { slug: "startup", label: "Startup", listing_count: 10 },
];

function makeMatch(overrides: Partial<JobListingMatchOut> = {}): JobListingMatchOut {
  return {
    listing: {
      id: "listing-1",
      company: "Google",
      title: "Software Engineer, New Grad",
      sector: "faang",
      seniority: "entry_level",
      package_min_lpa: 30,
      package_max_lpa: 45,
      description: "Build core infrastructure.",
      emphasis_domains: ["dsa", "python"],
      created_at: "2026-01-01T00:00:00Z",
    },
    matched_skills: [{ id: "s1", name: "Python", category: "technical" }],
    partial_skills: [],
    missing_skills: [{ id: "s2", name: "Data Structures", category: "technical" }],
    readiness: 0.5,
    is_tracked: false,
    ...overrides,
  };
}

const RECOMMENDED = [makeMatch()];
const TRACKED: TrackedJobOut[] = [];

const LIVE_JOB = {
  id: "greenhouse:stripe:101",
  company: "Google",
  title: "Software Engineer, Backend",
  location: "Remote - US",
  remote: true,
  url: "https://boards.greenhouse.io/x/jobs/101",
  sector: "faang",
  source: "greenhouse",
  posted_at: null,
  team: "Infra",
  summary: "Own core services.",
  description: "Own core services end to end.",
  responsibilities: [],
  requirements: [],
  skills: [{ name: "Python", importance: "core" }],
  comp_note: null,
  is_live: true,
  is_internship: false,
};
const LIVE_SEARCH = { jobs: [LIVE_JOB], total: 1, live: true };

const ROADMAP = {
  company: "Google",
  title: "Software Engineer, New Grad",
  sector: "faang",
  seniority: "entry_level",
  difficulty: "brutal",
  bar: "Google: hard.",
  total_weeks: 24,
  summary: "Plan for 24 weeks.",
  skills_focus: ["Data Structures"],
  phases: [
    { title: "Foundations", weeks: "Weeks 1-4", why: "w", actions: [{ text: "a", link: "/assessment" }], milestone: "m" },
  ],
};

function mockEndpoints({ recommended = RECOMMENDED, search = RECOMMENDED, tracked = TRACKED }: { recommended?: JobListingMatchOut[]; search?: JobListingMatchOut[]; tracked?: TrackedJobOut[] } = {}) {
  getMock.mockImplementation((url: string) => {
    if (url === "/job-catalog/sectors") return Promise.resolve(SECTORS);
    if (url === "/job-catalog/recommended") return Promise.resolve(recommended);
    if (url.startsWith("/job-catalog/search")) return Promise.resolve(search);
    if (url === "/job-catalog/tracked") return Promise.resolve(tracked);
    if (url === "/job-descriptions") return Promise.resolve([]);
    if (url.startsWith("/job-catalog/live/search")) return Promise.resolve(LIVE_SEARCH);
    if (url.includes("/roadmap")) return Promise.resolve(ROADMAP);
    return Promise.resolve(null);
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <JobDescriptionPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
  deleteMock.mockReset();
});

describe("JobMatchPage", () => {
  it("auto-populates recommended jobs from the resume, no manual entry required", async () => {
    mockEndpoints();
    renderPage();

    expect(await screen.findByRole("heading", { name: "Job Match" })).toBeInTheDocument();
    expect(await screen.findByText("Recommended for you")).toBeInTheDocument();
    expect((await screen.findAllByText("Google")).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/50%/).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Data Structures").length).toBeGreaterThan(0);
  });

  it("searches live jobs from the single bar and hides everything else", async () => {
    mockEndpoints();
    renderPage();

    await screen.findByRole("heading", { name: "Job Match" });
    expect(screen.getByText("Recommended for you")).toBeInTheDocument();

    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/search jobs/i), "Google");

    await waitFor(() =>
      expect(getMock).toHaveBeenCalledWith(expect.stringContaining("/job-catalog/live/search?q=Google")),
    );
    // Only the search results remain -- Recommended / Dream Jobs / manual JD are gone.
    await waitFor(() => expect(screen.queryByText("Recommended for you")).not.toBeInTheDocument());
    expect(screen.queryByText("My Dream Jobs")).not.toBeInTheDocument();
    expect(await screen.findByText(/live opening/i)).toBeInTheDocument();
    expect(screen.getByText("Software Engineer, Backend")).toBeInTheDocument();
  });

  it("lets a student mark 'I want this job' and shows it as tracked", async () => {
    mockEndpoints();
    postMock.mockResolvedValueOnce({
      id: "tracked-1",
      created_at: "2026-01-01T00:00:00Z",
      match: makeMatch({ is_tracked: true }),
    } satisfies TrackedJobOut);
    const user = userEvent.setup();
    renderPage();

    await screen.findAllByText("Google");
    const trackButtons = await screen.findAllByRole("button", { name: /i want this job/i });
    await user.click(trackButtons[0]);

    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/job-catalog/tracked/listing-1", {}));
  });

  it("shows the Job Gap Simulator with what/how much/how far for a tracked job", async () => {
    mockEndpoints({ tracked: [{ id: "tracked-1", created_at: "2026-01-01T00:00:00Z", match: makeMatch({ is_tracked: true }) }] });
    getMock.mockImplementation((url: string) => {
      if (url === "/job-catalog/sectors") return Promise.resolve(SECTORS);
      if (url === "/job-catalog/recommended") return Promise.resolve(RECOMMENDED);
      if (url.startsWith("/job-catalog/search")) return Promise.resolve(RECOMMENDED);
      if (url === "/job-catalog/tracked") {
        return Promise.resolve([{ id: "tracked-1", created_at: "2026-01-01T00:00:00Z", match: makeMatch({ is_tracked: true }) }]);
      }
      if (url === "/job-descriptions") return Promise.resolve([]);
      if (url.includes("/roadmap")) return Promise.resolve(ROADMAP);
      if (url.startsWith("/job-catalog/listing-1/gap-plan") || url.includes("/gap-plan")) {
        return Promise.resolve({
          listing: makeMatch().listing,
          readiness: 0.5,
          matched_count: 1,
          partial_count: 0,
          missing_count: 1,
          total_estimated_hours: 14,
          weekly_commitment_hours: 10,
          estimated_weeks_to_ready: 2,
          items: [{ skill_name: "Data Structures", status: "missing", estimated_hours: 14, recommended_resource: null }],
          assumptions: ["Assumes 10 focused hours/week.", "This is a heuristic planning estimate, not a guarantee."],
        });
      }
      return Promise.resolve(null);
    });
    renderPage();

    expect(await screen.findByText("My Dream Jobs")).toBeInTheDocument();
    expect(await screen.findByText("Job Gap Simulator")).toBeInTheDocument();
    expect(await screen.findByText(/~2w/)).toBeInTheDocument();
    expect(screen.getAllByText(/14h/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Prepare for this job in Interview Arena/i)).toBeInTheDocument();
  });

  it("still supports pasting a specific job description manually, collapsed by default", async () => {
    mockEndpoints();
    const user = userEvent.setup();
    renderPage();

    await screen.findByRole("heading", { name: "Job Match" });
    const toggle = screen.getByText(/have a specific job posting instead/i);
    expect(screen.queryByLabelText(/job title/i)).not.toBeInTheDocument();
    await user.click(toggle);
    expect(await screen.findByLabelText(/job title/i)).toBeInTheDocument();
  });
});
