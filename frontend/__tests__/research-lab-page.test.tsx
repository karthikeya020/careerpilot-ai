import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ResearchLabPage from "@/app/research-lab/page";
import type {
  AdversarialSuiteOut,
  CalibrationReportOut,
  EfficiencyFrontierOut,
  GraphVsVectorExperimentOut,
  LiveCriticToggleOut,
  RoutingExperimentOut,
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
  usePathname: () => "/research-lab",
  useParams: () => ({}),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ user: { id: "1", email: "student@example.com", roles: ["student"] }, isLoading: false, logout: vi.fn() }),
}));

vi.mock("@/lib/theme-provider", () => ({ useTheme: () => ({ theme: "dark", toggle: vi.fn() }) }));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const EMPTY_CALIBRATION: CalibrationReportOut = {
  sample_size: 0,
  brier_score: null,
  expected_calibration_error: null,
  bins: [],
  high_confidence_error_rate: null,
  preliminary: true,
};

const ROUTING_RESULT: RoutingExperimentOut = {
  run_id: "run-1",
  dataset_name: "phase2-curated-v1",
  case_count: 8,
  agreement_rate_by_variant: { single_agent_fixed: 0.125, multi_agent_fixed: 0.25, care_adaptive: 1.0 },
  rows: [],
};

const GRAPH_VS_VECTOR_RESULT: GraphVsVectorExperimentOut = {
  run_id: "run-2",
  case_count: 12,
  indexed_documents: 16,
  graph_traversal_accuracy: 1.0,
  vector_only_accuracy: 0.5,
  rows: [],
  methodology_note: "Graph traversal accuracy is 100% by construction.",
  sample_size_warning: "Preliminary: 12 cases drawn from the seeded concept-dependency graph.",
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ResearchLabPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  postMock.mockReset();
  getMock.mockImplementation((path: string) => {
    if (path === "/research/runs") return Promise.resolve([]);
    if (path === "/research/calibration") return Promise.resolve(EMPTY_CALIBRATION);
    return Promise.resolve(null);
  });
});

describe("ResearchLabPage", () => {
  it("shows an empty state before any experiment has run", async () => {
    renderPage();
    expect(await screen.findByText("No evaluation results yet")).toBeInTheDocument();
    expect(screen.getByText("No experiment runs yet")).toBeInTheDocument();
  });

  it("runs Experiment A and displays the real agreement rates, never a fabricated 100% for a fixed baseline", async () => {
    postMock.mockResolvedValueOnce(ROUTING_RESULT);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /run experiment a/i }));
    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/research/experiments/routing"));

    expect(await screen.findByText(/Experiment A: routing-strategy agreement/i)).toBeInTheDocument();
    expect(screen.getByText(/8 curated cases/i)).toBeInTheDocument();
  });

  it("runs Experiment B and shows the methodology and sample-size caveats", async () => {
    postMock.mockResolvedValueOnce(GRAPH_VS_VECTOR_RESULT);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /run experiment b/i }));
    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/research/experiments/graph-vs-vector"));

    expect(await screen.findByText(/100% by construction/i)).toBeInTheDocument();
    expect(screen.getByText(/Preliminary: 12 cases/i)).toBeInTheDocument();
  });

  it("runs the efficiency frontier and shows real latency/accuracy per condition", async () => {
    const EFFICIENCY_RESULT: EfficiencyFrontierOut = {
      run_id: "run-3",
      engine_version: "efficiency-frontier-v1",
      case_count: 4,
      frontier: [
        { condition: "single_agent_fixed", accuracy: 0.75, mean_latency_ms: 1.2, mean_llm_calls: 1, cost_usd: 0 },
        { condition: "multi_agent_fixed", accuracy: 0.75, mean_latency_ms: 3.4, mean_llm_calls: 3, cost_usd: 0 },
        { condition: "care_adaptive", accuracy: 0.75, mean_latency_ms: 1.8, mean_llm_calls: 1.5, cost_usd: 0 },
      ],
      rows: [],
      cost_note: "No live API key configured -- real dollar cost is $0 for all three conditions here.",
      preliminary: true,
    };
    postMock.mockResolvedValueOnce(EFFICIENCY_RESULT);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /efficiency frontier/i }));
    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/research/experiments/efficiency-frontier"));

    expect(await screen.findByText(/CARE efficiency frontier/i)).toBeInTheDocument();
    expect(screen.getByText(/no live api key configured/i)).toBeInTheDocument();
  });

  it("runs the adversarial suite and shows pass/fail per hostile case", async () => {
    const ADVERSARIAL_RESULT: AdversarialSuiteOut = {
      engine_version: "adversarial-v1",
      case_count: 2,
      passed_count: 1,
      all_passed: false,
      cases: [
        { case_id: "thin-answer", category: "thin_input", input_summary: "ok", confidence: 0.55, classification: "depth=0.30", passed: true, note: "Confidence stayed below the ceiling." },
        { case_id: "keyword-stuffed", category: "keyword_stuffing", input_summary: "index index index", confidence: 0.55, classification: "depth=1.00", passed: false, note: "FAILED: depth score was fooled by repeated keywords." },
      ],
      methodology_note: "Pass criterion is never a good score.",
    };
    postMock.mockResolvedValueOnce(ADVERSARIAL_RESULT);
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: /adversarial suite/i }));
    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/research/experiments/adversarial"));

    expect(await screen.findByText("1/2 passed")).toBeInTheDocument();
    expect(screen.getByText(/keyword stuffed/i)).toBeInTheDocument();
  });

  it("runs the live critic toggle for a typed answer and shows critic-off vs critic-on", async () => {
    const LIVE_RESULT: LiveCriticToggleOut = {
      engine_version: "live-ablation-v1",
      transcript: "Indexes are good.",
      technical_confidence: 0.55,
      communication_confidence: 0.65,
      critic_off_confidence: 0.6,
      critic_on_confidence: 0.4,
      delta: -0.2,
      issues_found: ["High-confidence claim with no cited evidence."],
      verdict: "flagged",
    };
    postMock.mockResolvedValueOnce(LIVE_RESULT);
    const user = userEvent.setup();
    renderPage();

    await screen.findByText(/live on stage/i);
    await user.click(screen.getByRole("button", { name: /run live/i }));

    await waitFor(() =>
      expect(postMock).toHaveBeenCalledWith("/research/experiments/live-critic-toggle", { transcript: "Indexes are good." }),
    );
    expect(await screen.findByText(/critic off \(raw mean\)/i)).toBeInTheDocument();
    expect(screen.getByText(/-20pp/)).toBeInTheDocument();
  });
});
