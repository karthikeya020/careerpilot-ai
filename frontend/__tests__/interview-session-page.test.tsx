import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import InterviewSessionPage from "@/app/interview/[sessionId]/page";
import type { InterviewProgressOut } from "@/types/api";

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
  usePathname: () => "/interview/session-1",
  useParams: () => ({ sessionId: "session-1" }),
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

const IN_PROGRESS: InterviewProgressOut = {
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
    difficulty: "medium",
    question_source: "bank",
    is_follow_up: false,
    follow_up_rationale: null,
  },
  is_complete: false,
};

const AFTER_ANSWER: InterviewProgressOut = {
  session: IN_PROGRESS.session,
  answer: {
    id: "answer-1",
    question_id: "q1",
    transcript: "An inner join returns only matched rows.",
    transcript_source: "typed",
    audio_duration_seconds: null,
    audio_mime_type: null,
    has_audio: false,
    submitted_at: "2026-08-04T00:01:00Z",
  },
  evaluation: {
    id: "eval-1",
    care_execution_id: "exec-1",
    dimension_scores: { relevance: 0.9, correctness: 0.8, depth: 0.6 },
    overall_score: 0.8,
    confidence: 0.75,
    agreement: null,
    strengths: ["Strong relevance."],
    improvements: ["Add more depth."],
    evidence_checks: [],
    communication_metrics: {
      word_count: 8,
      filler_word_count: 0,
      filler_ratio: 0,
      sentence_count: 1,
      sentence_completeness_ratio: 1,
      speaking_rate_wpm: null,
      star_components_found: [],
      clarity_score: 1,
      conciseness_score: 0.8,
      professional_communication_score: 0.9,
      camera_on_ratio: null,
    },
    timeline_markers: [],
    better_answer_framework: "State the concept, give an example, note a trade-off.",
    requires_human_review: false,
    created_at: "2026-08-04T00:01:05Z",
  },
  next_question: null,
  is_complete: true,
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <InterviewSessionPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
});

async function enterReadyRoom(user: ReturnType<typeof userEvent.setup>) {
  await screen.findByText(/ready room/i);
  await user.click(screen.getByRole("button", { name: /begin round/i }));
}

describe("InterviewSessionPage", () => {
  it("renders the current question and never leaks expected_keywords", async () => {
    getMock.mockResolvedValue(IN_PROGRESS);
    const user = userEvent.setup();
    renderPage();
    await enterReadyRoom(user);

    expect(await screen.findByText(/Explain INNER JOIN vs LEFT JOIN/i)).toBeInTheDocument();
    expect(screen.queryByText(/expected_keywords/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/model_answer_summary/i)).not.toBeInTheDocument();
  });

  it("disables submit until an answer is typed, then submits a typed answer", async () => {
    getMock.mockResolvedValue(IN_PROGRESS);
    const user = userEvent.setup();
    renderPage();
    await enterReadyRoom(user);

    await screen.findByText(/Explain INNER JOIN vs LEFT JOIN/i);
    const submitButton = screen.getByRole("button", { name: /submit answer/i });
    expect(submitButton).toBeDisabled();

    await user.type(screen.getByLabelText(/your answer/i), "An inner join returns only matched rows.");
    expect(submitButton).toBeEnabled();

    postMock.mockResolvedValueOnce(AFTER_ANSWER);
    await user.click(submitButton);

    await waitFor(() => expect(postMock).toHaveBeenCalledTimes(1));
    const [url, body, options] = postMock.mock.calls[0];
    expect(url).toBe("/interviews/sessions/session-1/answers");
    expect(body).toBeInstanceOf(FormData);
    expect((body as FormData).get("question_id")).toBe("q1");
    expect((body as FormData).get("typed_answer_text")).toBe("An inner join returns only matched rows.");
    expect(options).toEqual({ isFormData: true });
  });

  it("shows the evaluation panel and completion state after the last question", async () => {
    getMock.mockResolvedValue(IN_PROGRESS);
    postMock.mockResolvedValueOnce(AFTER_ANSWER);
    const user = userEvent.setup();
    renderPage();
    await enterReadyRoom(user);

    await screen.findByText(/Explain INNER JOIN vs LEFT JOIN/i);
    await user.type(screen.getByLabelText(/your answer/i), "An inner join returns only matched rows.");
    await user.click(screen.getByRole("button", { name: /submit answer/i }));

    expect(await screen.findByText("Interview complete")).toBeInTheDocument();
    expect(screen.getByText(/Strong relevance/i)).toBeInTheDocument();
    expect(screen.getByText(/Add more depth/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open interview replay/i })).toHaveAttribute(
      "href",
      "/interview/session-1/replay",
    );
    // Constitution rule 5: no hiring-prediction language anywhere on this screen.
    expect(screen.queryByText(/probability of being hired/i)).not.toBeInTheDocument();
  });

  it("allows recording as an alternative to typing (mic-permission path never blocks the form)", async () => {
    getMock.mockResolvedValue(IN_PROGRESS);
    const user = userEvent.setup();
    renderPage();
    await enterReadyRoom(user);

    await screen.findByText(/Explain INNER JOIN vs LEFT JOIN/i);
    expect(screen.getByRole("button", { name: /record answer/i })).toBeInTheDocument();
    // No microphone in the test environment -- the typed answer must remain a fully usable path.
    expect(screen.getByLabelText(/your answer/i)).toBeEnabled();
  });
});
