import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AssessmentPage from "@/app/assessment/page";
import type { ActivityDayOut, AssessmentAnalyticsOut, AssessmentDomainOut, AttemptProgressOut } from "@/types/api";

const { getMock, postMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: postMock, put: vi.fn(), patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/assessment",
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

const DOMAINS: AssessmentDomainOut[] = [
  {
    id: "d1",
    slug: "sql",
    name: "SQL",
    description: "Relational database querying.",
    question_count: 13,
    recommended: false,
    matched_skills: [],
  },
];

const RECOMMENDED_DOMAINS: AssessmentDomainOut[] = [
  {
    id: "d2",
    slug: "java",
    name: "Java",
    description: "Core language, collections, exceptions, memory.",
    question_count: 15,
    recommended: true,
    matched_skills: ["Java"],
  },
  ...DOMAINS,
];

const ACTIVITY: ActivityDayOut[] = [];
const ANALYTICS: AssessmentAnalyticsOut = {
  total_answered: 0,
  total_correct: 0,
  overall_accuracy: null,
  accuracy_by_domain: [],
  accuracy_by_difficulty: [],
  score_trend: [],
  current_streak_days: 0,
  longest_streak_days: 0,
  active_day_count: 0,
};

const MULTIPLE_CHOICE_PROGRESS: AttemptProgressOut = {
  attempt_id: "attempt-1",
  response: null,
  next_question: {
    id: "q1",
    question_type: "multiple_choice",
    prompt: "In the relational model, what uniquely identifies a row within a table?",
    options: [
      { id: "a", text: "The primary key" },
      { id: "b", text: "The table name" },
    ],
    difficulty: 1,
    difficulty_band: "easy",
    concept_name: "Relational Model",
  },
  is_complete: false,
  domain_exhausted: false,
  answered_in_domain: 0,
  total_in_domain: 13,
};

const ANSWERED_PROGRESS: AttemptProgressOut = {
  attempt_id: "attempt-1",
  response: {
    id: "r1",
    question_id: "q1",
    is_correct: true,
    score: 1,
    ai_evaluated: false,
    explanation: "A primary key uniquely identifies each row in a table.",
  },
  next_question: {
    id: "q2",
    question_type: "multiple_choice",
    prompt: "What does GROUP BY do?",
    options: [{ id: "a", text: "Collapses rows sharing a value" }],
    difficulty: 2,
    difficulty_band: "easy",
    concept_name: "Grouping",
  },
  is_complete: false,
  domain_exhausted: false,
  answered_in_domain: 1,
  total_in_domain: 13,
};

const COMPLETE_PROGRESS: AttemptProgressOut = {
  attempt_id: "attempt-1",
  response: null,
  next_question: null,
  is_complete: true,
  domain_exhausted: false,
  answered_in_domain: 2,
  total_in_domain: 13,
};

function mockHomeEndpoints(domains: AssessmentDomainOut[] = DOMAINS) {
  getMock.mockImplementation((url: string) => {
    if (url === "/assessments/domains") return Promise.resolve(domains);
    if (url.startsWith("/assessments/activity-calendar?year=")) return Promise.resolve(ACTIVITY);
    if (url === "/assessments/analytics") return Promise.resolve(ANALYTICS);
    if (url.startsWith("/assessments/activity-calendar/")) return Promise.resolve([]);
    if (url === "/students/me/leetcode-profile") return Promise.resolve({ status: "not_configured" });
    if (url === "/assessments/leetcode-recommendations")
      return Promise.resolve({ source: "profile", summary: "", weakness_threshold: 0.6, groups: [], disclaimer: "" });
    if (url === "/assessments/leetcode-completions") return Promise.resolve([]);
    if (url === "/assessments/daily-goal")
      return Promise.resolve({
        goal: null,
        date: "2026-09-02",
        matched_domains: [],
        target_per_day: 5,
        completed_today: 0,
        questions: [],
      });
    return Promise.resolve(null);
  });
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <AssessmentPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
});

describe("AssessmentPage", () => {
  it("lists available assessment topics and starts an attempt", async () => {
    mockHomeEndpoints();
    postMock.mockResolvedValueOnce(MULTIPLE_CHOICE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText("SQL")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /start practicing/i }));

    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/assessments/attempts", { domain_slug: "sql" }));
    expect(await screen.findByText(/uniquely identifies a row/i)).toBeInTheDocument();
    expect(screen.getByText("Relational Model")).toBeInTheDocument();
    expect(screen.getByText("Easy")).toBeInTheDocument();
  });

  it("shows a 'Recommended for you' section only for resume-matched topics", async () => {
    mockHomeEndpoints(RECOMMENDED_DOMAINS);
    renderPage();

    expect(await screen.findByText(/recommended for you/i)).toBeInTheDocument();
    expect(screen.getByText(/recommended from your resume/i)).toBeInTheDocument();
  });

  it("labels itself as an educational prototype, not a psychometric evaluation", async () => {
    mockHomeEndpoints();
    postMock.mockResolvedValueOnce(MULTIPLE_CHOICE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /start practicing/i }));
    expect(await screen.findByText(/not a psychometric evaluation/i)).toBeInTheDocument();
  });

  it("submits a multiple-choice answer, reveals the explanation, then advances on continue", async () => {
    mockHomeEndpoints();
    postMock.mockResolvedValueOnce(MULTIPLE_CHOICE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /start practicing/i }));
    await screen.findByText(/uniquely identifies a row/i);

    postMock.mockResolvedValueOnce(ANSWERED_PROGRESS);
    await user.click(screen.getByLabelText("The primary key"));
    await user.click(screen.getByRole("button", { name: /submit answer/i }));

    await waitFor(() =>
      expect(postMock).toHaveBeenCalledWith("/assessments/attempts/attempt-1/responses", {
        question_id: "q1",
        response_payload: { selected_option_ids: ["a"] },
        time_spent_seconds: expect.any(Number),
      }),
    );

    // Explanation reveal must show before the next question -- this is the
    // actual learning payoff, not just an instant pass-through.
    expect(await screen.findByText("Correct!")).toBeInTheDocument();
    expect(screen.getByText(/uniquely identifies each row/i)).toBeInTheDocument();
    expect(screen.queryByText(/what does group by do/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /next question/i }));
    expect(await screen.findByText(/what does group by do/i)).toBeInTheDocument();
  });

  it("shows a completion state once the attempt finishes, without exposing an evidence-of-hiring claim", async () => {
    mockHomeEndpoints();
    postMock.mockResolvedValueOnce(COMPLETE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /start practicing/i }));

    expect(await screen.findByText("Assessment complete")).toBeInTheDocument();
    expect(screen.getByText(/Career Twin has been updated/i)).toBeInTheDocument();
    expect(screen.queryByText(/probability/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/hired/i)).not.toBeInTheDocument();
  });

  it("disables the submit button until an answer is chosen", async () => {
    mockHomeEndpoints();
    postMock.mockResolvedValueOnce(MULTIPLE_CHOICE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /start practicing/i }));
    await screen.findByText(/uniquely identifies a row/i);

    expect(screen.getByRole("button", { name: /submit answer/i })).toBeDisabled();
    await user.click(screen.getByLabelText("The primary key"));
    expect(screen.getByRole("button", { name: /submit answer/i })).toBeEnabled();
  });
});
