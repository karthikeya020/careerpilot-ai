import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AssessmentPage from "@/app/assessment/page";
import type { AssessmentDomainOut, AttemptProgressOut } from "@/types/api";

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
  { id: "d1", slug: "sql", name: "SQL", description: "Relational database querying." },
];

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
    concept_name: "Relational Model",
  },
  is_complete: false,
};

const COMPLETE_PROGRESS: AttemptProgressOut = {
  attempt_id: "attempt-1",
  response: null,
  next_question: null,
  is_complete: true,
};

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
  it("lists available assessment domains and starts an attempt", async () => {
    getMock.mockResolvedValueOnce(DOMAINS);
    postMock.mockResolvedValueOnce(MULTIPLE_CHOICE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    expect(await screen.findByText("SQL")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /start assessment/i }));

    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/assessments/attempts", { domain_slug: "sql" }));
    expect(await screen.findByText(/uniquely identifies a row/i)).toBeInTheDocument();
    expect(screen.getByText("Relational Model")).toBeInTheDocument();
  });

  it("labels itself as an educational prototype, not a psychometric evaluation", async () => {
    getMock.mockResolvedValueOnce(DOMAINS);
    postMock.mockResolvedValueOnce(MULTIPLE_CHOICE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /start assessment/i }));
    expect(await screen.findByText(/not a psychometric evaluation/i)).toBeInTheDocument();
  });

  it("submits a multiple-choice answer with the selected option id", async () => {
    getMock.mockResolvedValueOnce(DOMAINS);
    postMock.mockResolvedValueOnce(MULTIPLE_CHOICE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /start assessment/i }));
    await screen.findByText(/uniquely identifies a row/i);

    postMock.mockResolvedValueOnce(COMPLETE_PROGRESS);
    await user.click(screen.getByLabelText("The primary key"));
    await user.click(screen.getByRole("button", { name: /submit answer/i }));

    await waitFor(() =>
      expect(postMock).toHaveBeenCalledWith("/assessments/attempts/attempt-1/responses", {
        question_id: "q1",
        response_payload: { selected_option_ids: ["a"] },
        time_spent_seconds: undefined,
      }),
    );
  });

  it("shows a completion state once the attempt finishes, without exposing an evidence-of-hiring claim", async () => {
    getMock.mockResolvedValueOnce(DOMAINS);
    postMock.mockResolvedValueOnce(COMPLETE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /start assessment/i }));

    expect(await screen.findByText("Assessment complete")).toBeInTheDocument();
    expect(screen.getByText(/Career Twin has been updated/i)).toBeInTheDocument();
    expect(screen.queryByText(/probability/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/hired/i)).not.toBeInTheDocument();
  });

  it("disables the submit button until an answer is chosen", async () => {
    getMock.mockResolvedValueOnce(DOMAINS);
    postMock.mockResolvedValueOnce(MULTIPLE_CHOICE_PROGRESS);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /start assessment/i }));
    await screen.findByText(/uniquely identifies a row/i);

    expect(screen.getByRole("button", { name: /submit answer/i })).toBeDisabled();
    await user.click(screen.getByLabelText("The primary key"));
    expect(screen.getByRole("button", { name: /submit answer/i })).toBeEnabled();
  });
});
