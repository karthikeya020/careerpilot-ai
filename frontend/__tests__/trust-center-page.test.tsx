import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import TrustCenterPage from "@/app/trust-center/page";
import type { CareExecutionDetailOut, CareExecutionSummaryOut } from "@/types/api";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/trust-center",
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

const EXECUTIONS: CareExecutionSummaryOut[] = [
  {
    id: "exec-1",
    task_type: "root_cause_analysis",
    route: "single_agent",
    confidence: 0.6,
    agents_invoked: ["graphrag", "career_coach"],
    retrieval_used: true,
    reflection_used: false,
    requires_human_review: false,
    final_status: "completed",
    created_at: "2026-08-04T14:29:50.948839",
  },
];

const DETAIL: CareExecutionDetailOut = {
  ...EXECUTIONS[0],
  request_summary: "Root-cause analysis for missed question on concept 'Inner Join'.",
  input_evidence_ids: ["e1", "e2"],
  routing_factors: { task_type: "root_cause_analysis" },
  reasoning_summary: "Evidence was sufficient and initial confidence was high enough for a single specialist.",
  agreement: null,
  cost_usd: 0,
  latency_ms: 1671.331,
  policy_version: "care-policy-v1",
  agent_runs: [
    {
      id: "run-1",
      agent_name: "graphrag",
      prompt_version: "graphrag-v1",
      confidence: 0.95,
      evidence_citations: ["e1", "e2"],
      inference_type: "extracted_fact",
      status: "completed",
      latency_ms: 29,
      created_at: "2026-08-04T14:29:50.950624",
      output_payload: { graph_source: "neo4j" },
    },
    {
      id: "run-2",
      agent_name: "career_coach",
      prompt_version: "career-coach-v1",
      confidence: 0.6,
      evidence_citations: ["e1", "e2"],
      inference_type: "deterministic_calculation",
      status: "completed",
      latency_ms: 0.1,
      created_at: "2026-08-04T14:29:50.950636",
      output_payload: {},
    },
  ],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <TrustCenterPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
});

describe("TrustCenterPage", () => {
  it("lists recent CARE decisions with a human-readable route label", async () => {
    getMock.mockImplementation((path: string) => {
      if (path.startsWith("/trust-center/executions?")) return Promise.resolve(EXECUTIONS);
      return Promise.resolve(DETAIL);
    });
    renderPage();

    expect(await screen.findByText("Root Cause Analysis")).toBeInTheDocument();
    expect(screen.getAllByText("Single specialist").length).toBeGreaterThan(0);
  });

  it("shows the full decision trace for the selected execution, including agents invoked", async () => {
    getMock.mockImplementation((path: string) => {
      if (path.startsWith("/trust-center/executions?")) return Promise.resolve(EXECUTIONS);
      return Promise.resolve(DETAIL);
    });
    renderPage();

    await screen.findByText("Root Cause Analysis");
    expect(await screen.findByText("Graphrag")).toBeInTheDocument();
    expect(screen.getByText("Career Coach")).toBeInTheDocument();
    expect(screen.getByText(/Evidence was sufficient/i)).toBeInTheDocument();
  });

  it("labels which graph source produced the GraphRAG agent's result", async () => {
    getMock.mockImplementation((path: string) => {
      if (path.startsWith("/trust-center/executions?")) return Promise.resolve(EXECUTIONS);
      return Promise.resolve(DETAIL);
    });
    renderPage();

    expect(await screen.findByText("Neo4j graph")).toBeInTheDocument();
  });

  it("labels the relational fallback distinctly when Neo4j was unavailable", async () => {
    const fallbackDetail: CareExecutionDetailOut = {
      ...DETAIL,
      agent_runs: [
        { ...DETAIL.agent_runs[0], output_payload: { graph_source: "relational_fallback" } },
        DETAIL.agent_runs[1],
      ],
    };
    getMock.mockImplementation((path: string) => {
      if (path.startsWith("/trust-center/executions?")) return Promise.resolve(EXECUTIONS);
      return Promise.resolve(fallbackDetail);
    });
    renderPage();

    expect(await screen.findByText(/Relational fallback/i)).toBeInTheDocument();
  });

  it("shows an empty state when no AI decisions exist yet", async () => {
    getMock.mockImplementation((path: string) => {
      if (path.startsWith("/trust-center/executions?")) return Promise.resolve([]);
      return Promise.resolve(null);
    });
    renderPage();

    expect(await screen.findByText(/No AI decisions yet/i)).toBeInTheDocument();
  });

  it("lets the user select a different execution from the list", async () => {
    const secondExecution: CareExecutionSummaryOut = {
      ...EXECUTIONS[0],
      id: "exec-2",
      task_type: "resume_insight",
      route: "deterministic",
    };
    getMock.mockImplementation((path: string) => {
      if (path.startsWith("/trust-center/executions?")) return Promise.resolve([EXECUTIONS[0], secondExecution]);
      if (path === "/trust-center/executions/exec-2") return Promise.resolve({ ...DETAIL, id: "exec-2", route: "deterministic", agent_runs: [] });
      return Promise.resolve(DETAIL);
    });
    const user = userEvent.setup();
    renderPage();

    await screen.findByText("Root Cause Analysis");
    await user.click(screen.getByText("Resume Insight"));

    await waitFor(() => expect(getMock).toHaveBeenCalledWith("/trust-center/executions/exec-2"));
  });
});
