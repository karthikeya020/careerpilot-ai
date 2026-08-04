import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ResponsibleAIPage from "@/app/responsible-ai/page";
import type { ResponsibleAIOverviewOut } from "@/types/api";

const { getMock, deleteMock, logoutMock, pushMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  deleteMock: vi.fn(),
  logoutMock: vi.fn(),
  pushMock: vi.fn(),
}));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), delete: deleteMock } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
  usePathname: () => "/responsible-ai",
  useParams: () => ({}),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    user: { id: "1", email: "student@example.com", roles: ["student"] },
    isLoading: false,
    logout: logoutMock,
  }),
}));

vi.mock("@/lib/theme-provider", () => ({
  useTheme: () => ({ theme: "dark", toggle: vi.fn() }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

const OVERVIEW: ResponsibleAIOverviewOut = {
  evaluates: ["Resume and job-description keyword/skill coverage"],
  does_not_evaluate: ["Anything without linked evidence"],
  versions: {
    care_policy_version: "care-policy-v1",
    career_twin_formula_version: "twin-v2",
    simulation_engine_version: "sim-v1",
    agent_prompt_versions: { technical: "technical-interview-v1" },
  },
  human_review: { pending_count: 0 },
  evidence_provenance: { interview: 4 },
  current_career_twin_confidence: 0.42,
  consent: { data_processing: true },
  stored_interview_audio_count: 2,
  non_claims: [
    "No hiring probability is ever computed or displayed.",
    "No public ranking of students is shown to any role.",
  ],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ResponsibleAIPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  deleteMock.mockReset();
  logoutMock.mockReset();
  pushMock.mockReset();
  getMock.mockResolvedValue(OVERVIEW);
});

describe("ResponsibleAIPage", () => {
  it("shows the non-claims and versions", async () => {
    renderPage();
    expect(await screen.findByText(/No hiring probability is ever computed/i)).toBeInTheDocument();
    expect(screen.getByText(/No public ranking of students/i)).toBeInTheDocument();
    expect(screen.getByText(/care-policy-v1/)).toBeInTheDocument();
    expect(screen.getByText(/twin-v2/)).toBeInTheDocument();
  });

  it("deletes interview audio and refreshes the count", async () => {
    deleteMock.mockResolvedValueOnce({ deleted_count: 2 });
    const user = userEvent.setup();
    renderPage();

    await screen.findByText(/Delete interview audio \(2 stored\)/i);
    await user.click(screen.getByRole("button", { name: /delete audio/i }));

    await waitFor(() => expect(deleteMock).toHaveBeenCalledWith("/responsible-ai/interview-audio"));
  });

  it("requires a password before permanently deleting the account", async () => {
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("Your data controls");
    await user.click(screen.getByRole("button", { name: /^delete my account$/i }));

    const confirmButton = screen.getByRole("button", { name: /confirm permanent deletion/i });
    expect(confirmButton).toBeDisabled();

    await user.type(screen.getByLabelText(/confirm password to delete account/i), "Password1");
    expect(confirmButton).toBeEnabled();

    deleteMock.mockResolvedValueOnce(undefined);
    await user.click(confirmButton);

    await waitFor(() => expect(deleteMock).toHaveBeenCalledWith("/responsible-ai/account", { password: "Password1" }));
    await waitFor(() => expect(logoutMock).toHaveBeenCalled());
    expect(pushMock).toHaveBeenCalledWith("/login");
  });
});
