import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import InterviewPage from "@/app/interview/page";
import type { DashboardOut, InterviewProgressOut, JobDescriptionOut } from "@/types/api";

const { getMock, postMock, pushMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
  pushMock: vi.fn(),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: postMock, patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
  usePathname: () => "/interview",
  useParams: () => ({}),
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

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

const DASHBOARD_NO_ROLE: Partial<DashboardOut> = {
  student_name: "Ada",
  target_role: null,
};

const JOB_DESCRIPTIONS: JobDescriptionOut[] = [];

const PROGRESS: InterviewProgressOut = {
  session: {
    id: "session-1",
    mode: "technical",
    target_role_id: null,
    job_description_id: null,
    company_name: null,
    status: "in_progress",
    overall_score: null,
    overall_confidence: null,
    started_at: "2026-08-04T00:00:00Z",
    completed_at: null,
  },
  answer: null,
  evaluation: null,
  next_question: {
    id: "q1",
    order_index: 0,
    mode: "technical",
    prompt: "Explain INNER JOIN vs LEFT JOIN.",
    question_source: "bank",
  },
  is_complete: false,
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <InterviewPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
  pushMock.mockReset();
});

describe("InterviewPage", () => {
  it("lists all interview modes and warns when no target role is set", async () => {
    getMock.mockImplementation((path: string) => {
      if (path === "/dashboard") return Promise.resolve(DASHBOARD_NO_ROLE);
      if (path === "/job-descriptions") return Promise.resolve(JOB_DESCRIPTIONS);
      return Promise.resolve(null);
    });
    renderPage();

    expect(await screen.findByText("HR / Behavioral")).toBeInTheDocument();
    expect(screen.getByText("Technical")).toBeInTheDocument();
    expect(screen.getByText("Resume-based")).toBeInTheDocument();
    expect(screen.getByText("Company context")).toBeInTheDocument();
    expect(screen.getByText("Mixed")).toBeInTheDocument();
    expect(await screen.findByText(/No target role set/i)).toBeInTheDocument();
  });

  it("starts an interview and navigates to the session page", async () => {
    getMock.mockImplementation((path: string) => {
      if (path === "/dashboard") return Promise.resolve(DASHBOARD_NO_ROLE);
      if (path === "/job-descriptions") return Promise.resolve(JOB_DESCRIPTIONS);
      return Promise.resolve(null);
    });
    postMock.mockResolvedValueOnce(PROGRESS);
    const user = userEvent.setup();
    renderPage();

    const technicalCard = (await screen.findByText("Technical")).closest("div");
    const startButtons = screen.getAllByRole("button", { name: /start interview/i });
    // Technical is the second card in MODE_ORDER (hr, technical, ...).
    await user.click(startButtons[1]);

    await waitFor(() =>
      expect(postMock).toHaveBeenCalledWith("/interviews/sessions", {
        mode: "technical",
        target_role_id: null,
        job_description_id: null,
      }),
    );
    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/interview/session-1"));
    expect(technicalCard).toBeTruthy();
  });
});
