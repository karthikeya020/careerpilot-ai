import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ExperimentLabPage from "@/app/experiment-lab/page";
import type { DashboardOut, ExperimentScenarioOut, SkillOut } from "@/types/api";

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
  usePathname: () => "/experiment-lab",
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

const SKILLS: SkillOut[] = [{ id: "s1", name: "SQL", category: "technical" }];
const DASHBOARD: Partial<DashboardOut> = { target_role: null };

const SCENARIO_RESULT: ExperimentScenarioOut = {
  id: "scenario-1",
  name: "20 hours SQL",
  target_role_id: null,
  time_horizon_days: 30,
  allocations: [{ skill_name: "SQL", activity_type: "practice_problems", hours: 20 }],
  created_at: "2026-08-05T00:00:00Z",
  result: {
    id: "result-1",
    engine_version: "sim-v1",
    baseline_snapshot_id: null,
    current_overall_score: 0.5,
    simulated_overall_score: 0.62,
    overall_score_delta: 0.12,
    overall_confidence: 0.3,
    overall_uncertainty: 0.7,
    component_changes: [
      {
        component_type: "technical_readiness",
        current_score: 0.5,
        simulated_score: 0.68,
        delta: 0.18,
        confidence: 0.35,
        uncertainty: 0.65,
        assumptions: [],
        evidence_used: ["e1"],
      },
    ],
    assumptions: ["Activity-effectiveness weights are fixed heuristic multipliers."],
    evidence_used: ["e1"],
    explanation: "Technical is estimated to improve by 0.18.",
    disclaimer: "Personalized scenario estimate—not a guaranteed outcome or hiring prediction.",
    created_at: "2026-08-05T00:00:00Z",
  },
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ExperimentLabPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
  getMock.mockImplementation((path: string) => {
    if (path === "/experiments/activity-types") return Promise.resolve(["practice_problems", "mock_interview"]);
    if (path === "/skills") return Promise.resolve(SKILLS);
    if (path === "/dashboard") return Promise.resolve(DASHBOARD);
    if (path === "/experiments/scenarios") return Promise.resolve([]);
    return Promise.resolve(null);
  });
});

describe("ExperimentLabPage", () => {
  it("runs a scenario and shows the side-by-side comparison with the mandatory disclaimer", async () => {
    postMock.mockResolvedValueOnce(SCENARIO_RESULT);
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("Build a scenario");
    await user.click(screen.getByRole("button", { name: /run scenario/i }));

    await waitFor(() => expect(postMock).toHaveBeenCalled());
    const [url, body] = postMock.mock.calls[0];
    expect(url).toBe("/experiments/scenarios");
    expect(body.allocations[0]).toEqual({ skill_name: "SQL", activity_type: "practice_problems", hours: 20 });

    expect(await screen.findByText(/62%/)).toBeInTheDocument();
    expect(screen.getAllByText(/Personalized scenario estimate/i).length).toBeGreaterThan(0);
  });

  it("lets the user add and remove allocations for a mixed scenario", async () => {
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("Build a scenario");
    expect(screen.getAllByLabelText("Skill")).toHaveLength(1);

    await user.click(screen.getByRole("button", { name: /add allocation/i }));
    expect(screen.getAllByLabelText("Skill")).toHaveLength(2);

    const removeButtons = screen.getAllByLabelText("Remove allocation");
    await user.click(removeButtons[1]);
    expect(screen.getAllByLabelText("Skill")).toHaveLength(1);
  });

  it("always shows the disclaimer on the page even before running a scenario", async () => {
    renderPage();
    await screen.findByText("Build a scenario");
    expect(screen.getByText(/Personalized scenario estimate—not a guaranteed outcome or hiring prediction\./)).toBeInTheDocument();
  });
});
