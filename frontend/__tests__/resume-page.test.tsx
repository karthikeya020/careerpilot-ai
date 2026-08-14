import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ResumePage from "@/app/resume/page";
import type {
  DashboardOut,
  RecruiterCardOut,
  ResumeAnalysisOut,
  ResumeOut,
  ResumeSummaryOut,
} from "@/types/api";

const { getMock, postMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: postMock, patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/resume",
  useParams: () => ({}),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    user: { id: "1", email: "student@example.com", roles: ["student"] },
    isLoading: false,
    logout: vi.fn(),
  }),
}));

vi.mock("@/lib/theme-provider", () => ({
  useTheme: () => ({ theme: "dark", toggle: vi.fn() }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const ACTIVE_RESUME: ResumeOut = {
  id: "resume-b",
  original_filename: "resume-b.docx",
  content_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  file_size: 2048,
  parsing_status: "parsed",
  parsing_error: null,
  uploaded_at: "2026-08-06T00:00:00Z",
  parsed_at: "2026-08-06T00:00:05Z",
  is_active: true,
  superseded_at: null,
  sections: [],
  resume_skills: [{ skill: { id: "sk1", name: "Pandas", category: "technical" }, confidence: 0.7, evidence_snippet: "Pandas" }],
};

const HISTORY: ResumeSummaryOut[] = [
  {
    id: "resume-b",
    original_filename: "resume-b.docx",
    file_size: 2048,
    parsing_status: "parsed",
    uploaded_at: "2026-08-06T00:00:00Z",
    parsed_at: "2026-08-06T00:00:05Z",
    is_active: true,
    superseded_at: null,
    skill_count: 1,
  },
  {
    id: "resume-a",
    original_filename: "resume-a.docx",
    file_size: 1024,
    parsing_status: "parsed",
    uploaded_at: "2026-08-05T00:00:00Z",
    parsed_at: "2026-08-05T00:00:05Z",
    is_active: false,
    superseded_at: "2026-08-06T00:00:00Z",
    skill_count: 1,
  },
];

const ANALYSIS: ResumeAnalysisOut = {
  has_resume: true,
  bullet_grades: [
    {
      section_type: "projects",
      text: "Built a REST API using Python, cutting latency by 40%.",
      strength: "strong",
      has_action_verb: true,
      has_metric: true,
      has_outcome_language: true,
      fix_suggestion: null,
    },
    {
      section_type: "experience",
      text: "Worked on backend development for the team.",
      strength: "weak",
      has_action_verb: false,
      has_metric: false,
      has_outcome_language: false,
      fix_suggestion: "Start with a strong action verb and add a measurable outcome.",
    },
  ],
  self_consistency_flags: [
    { skill_id: "sk2", skill_name: "Kubernetes", message: "\"Kubernetes\" is listed in your Skills section but isn't backed up anywhere else." },
  ],
  parseability: { score: 0.85, warnings: [] },
  graph_diagnosis: [
    {
      concept_slug: "python-basics",
      concept_name: "Python Fundamentals",
      domain_name: "Python",
      status: "developing",
      mastery: 0.55,
      confidence: 0.6,
      evidence_count: 2,
      reasoning: "Based on 2 pieces of real evidence, your mastery of Python Fundamentals is 55%.",
      depends_on: [],
      blocks: [],
      target_role_relevant: true,
      recommended_resource: null,
      practice_available: true,
      questions_answered: 1,
      questions_total: 3,
    },
  ],
};

const RECRUITER_CARD: RecruiterCardOut = {
  has_resume: true,
  trust_score: 0.72,
  strengths: ["2 of 2 experience/project bullets read as strong, evidence-backed claims."],
  concerns: ["\"Kubernetes\" is listed in your Skills section but isn't backed up anywhere else."],
  verified_skill_count: 1,
  total_skill_count: 2,
  parseability_score: 0.85,
  bullet_strong_ratio: 0.5,
  disclaimer: "This is an evidence-completeness signal -- not a hiring recommendation, interview outcome, or placement guarantee. CareerPilot never computes or displays a probability of being hired.",
};

const DASHBOARD_WITH_MISSION: Partial<DashboardOut> = {
  student_name: "Ada",
  mission: {
    id: "mission-1",
    title: "Strengthen your Kubernetes evidence",
    description: "Complete a project demonstrating Kubernetes to back up your resume claim.",
    status: "pending",
    source_component: "skill_depth_readiness",
    target_skill: { id: "sk2", name: "Kubernetes", category: "technical" },
  } as DashboardOut["mission"],
};

function mockEndpoints() {
  getMock.mockImplementation((path: string) => {
    if (path === "/resumes/me") return Promise.resolve(ACTIVE_RESUME);
    if (path === "/resumes") return Promise.resolve(HISTORY);
    if (path === "/resumes/me/analysis") return Promise.resolve(ANALYSIS);
    if (path === "/resumes/me/recruiter-card") return Promise.resolve(RECRUITER_CARD);
    if (path === "/dashboard") return Promise.resolve(DASHBOARD_WITH_MISSION);
    if (path === "/job-catalog/tracked") return Promise.resolve([]);
    return Promise.resolve(null);
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ResumePage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
});

describe("ResumePage", () => {
  it("shows the active resume badge and a history list with a superseded version", async () => {
    mockEndpoints();
    renderPage();

    expect(await screen.findByText("resume-b.docx")).toBeInTheDocument();
    expect(screen.getAllByText(/active resume/i).length).toBeGreaterThan(0);
    expect(await screen.findByText("resume-a.docx")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /make active/i })).toBeInTheDocument();
  });

  it("lets the student reactivate an older resume version", async () => {
    mockEndpoints();
    postMock.mockResolvedValueOnce({ ...ACTIVE_RESUME, id: "resume-a", is_active: true });
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("resume-a.docx");
    await user.click(screen.getByRole("button", { name: /make active/i }));

    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/resumes/resume-a/activate"));
  });

  it("grades bullets for evidence strength with fix suggestions on weak bullets", async () => {
    mockEndpoints();
    renderPage();

    expect(await screen.findByText(/cutting latency by 40%/i)).toBeInTheDocument();
    expect(await screen.findByText(/worked on backend development/i)).toBeInTheDocument();
    expect(screen.getByText(/strong action verb and add a measurable outcome/i)).toBeInTheDocument();
  });

  it("flags a skill listed but not evidenced elsewhere on the resume", async () => {
    mockEndpoints();
    renderPage();

    expect((await screen.findAllByText(/isn't backed up anywhere else/i)).length).toBeGreaterThan(0);
  });

  it("shows the parseability score and the resume-to-graph diagnosis", async () => {
    mockEndpoints();
    renderPage();

    expect(await screen.findByText(/real ats check/i)).toBeInTheDocument();
    expect(await screen.findByText("Python Fundamentals")).toBeInTheDocument();
    expect(screen.getByText("Developing")).toBeInTheDocument();
  });

  it("renders the recruiter view card with a trust score and the non-hiring disclaimer", async () => {
    mockEndpoints();
    renderPage();

    expect(await screen.findByText(/what a recruiter would see/i)).toBeInTheDocument();
    expect(await screen.findByText("72")).toBeInTheDocument();
    expect(screen.getByText(/not a hiring recommendation/i)).toBeInTheDocument();
  });

  it("shows the first-mission callout right after a successful upload", async () => {
    mockEndpoints();
    postMock.mockResolvedValueOnce(ACTIVE_RESUME);
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("resume-b.docx");
    expect(screen.queryByText(/first diagnosed gap and mission/i)).not.toBeInTheDocument();

    const file = new File(["dummy"], "resume.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const input = document.getElementById("resume-upload") as HTMLInputElement;
    await user.upload(input, file);

    expect(await screen.findByText(/first diagnosed gap and mission/i)).toBeInTheDocument();
    expect(screen.getByText(/strengthen your kubernetes evidence/i)).toBeInTheDocument();
  });
});
