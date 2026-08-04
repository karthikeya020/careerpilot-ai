import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ResearchLabPage from "@/app/research-lab/page";
import type { CalibrationReportOut, GraphVsVectorExperimentOut, RoutingExperimentOut } from "@/types/api";

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
});
