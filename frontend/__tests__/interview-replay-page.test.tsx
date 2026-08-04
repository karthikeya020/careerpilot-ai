import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import InterviewReplayPage from "@/app/interview/[sessionId]/replay/page";
import type { InterviewReplayOut } from "@/types/api";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/interview/session-1/replay",
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

const REPLAY: InterviewReplayOut = {
  session: {
    id: "session-1",
    mode: "resume",
    target_role_id: null,
    job_description_id: null,
    company_name: null,
    status: "completed",
    overall_score: 0.55,
    overall_confidence: 0.6,
    started_at: "2026-08-04T00:00:00Z",
    completed_at: "2026-08-04T00:05:00Z",
  },
  items: [
    {
      question: {
        id: "q1",
        order_index: 0,
        mode: "resume",
        prompt: "Walk me through a project you're proud of.",
        question_source: "resume",
      },
      answer: {
        id: "answer-1",
        question_id: "q1",
        transcript: "I led the backend rewrite project.",
        transcript_source: "typed",
        audio_duration_seconds: null,
        has_audio: false,
        submitted_at: "2026-08-04T00:01:00Z",
      },
      evaluation: {
        id: "eval-1",
        care_execution_id: "exec-1",
        dimension_scores: { relevance: 0.7, structure: 0.5, evidence: 0.4 },
        overall_score: 0.55,
        confidence: 0.6,
        agreement: 0.9,
        strengths: [],
        improvements: ["Add a specific metric."],
        evidence_checks: [
          {
            claim: "I led the backend rewrite project.",
            classification: "insufficient_evidence",
            explanation: "No resume has been uploaded yet, so this claim cannot be checked against evidence.",
          },
        ],
        communication_metrics: {
          word_count: 7,
          filler_word_count: 0,
          filler_ratio: 0,
          sentence_count: 1,
          sentence_completeness_ratio: 1,
          speaking_rate_wpm: null,
          star_components_found: [],
          clarity_score: 0.8,
          conciseness_score: 0.5,
          professional_communication_score: 0.6,
        },
        timeline_markers: [
          { type: "strong_introduction", label: "Confident, substantive opening.", position_percent: 0 },
        ],
        better_answer_framework: "Structure your answer with STAR.",
        requires_human_review: false,
        created_at: "2026-08-04T00:01:05Z",
      },
    },
  ],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <InterviewReplayPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
});

describe("InterviewReplayPage", () => {
  it("renders the transcript, evidence check, and timeline for each answered question", async () => {
    getMock.mockResolvedValueOnce(REPLAY);
    renderPage();

    expect(await screen.findByText(/Walk me through a project/i)).toBeInTheDocument();
    expect(screen.getByText(/I led the backend rewrite project/i)).toBeInTheDocument();
    expect(screen.getByText(/typed answer/i)).toBeInTheDocument();
    expect(screen.getByText(/insufficient evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/No resume has been uploaded yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Confident, substantive opening/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view full decision trace in trust center/i })).toHaveAttribute(
      "href",
      "/trust-center?execution=exec-1",
    );
    // Respectful wording -- never accuses the student of dishonesty (Constitution rule 7).
    expect(screen.queryByText(/dishonest/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/lying/i)).not.toBeInTheDocument();
  });

  it("shows an empty state when the session has no answered questions", async () => {
    getMock.mockResolvedValueOnce({ session: REPLAY.session, items: [] });
    renderPage();

    expect(await screen.findByText(/No answered questions/i)).toBeInTheDocument();
  });
});
