import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ResearchReportPage from "@/app/research-lab/report/page";
import type { ResearchReportOut } from "@/types/api";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/research-lab/report",
  useParams: () => ({}),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ user: { id: "1", email: "student@example.com", roles: ["student"] }, isLoading: false, logout: vi.fn() }),
}));

vi.mock("@/lib/theme-provider", () => ({ useTheme: () => ({ theme: "dark", toggle: vi.fn() }) }));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const REPORT: ResearchReportOut = {
  report_version: "research-report-v1",
  generated_at: "2026-08-06T00:00:00Z",
  calibration: { sample_size: 10 },
  ablations: { harness_version: "ablation-v1" },
  efficiency_frontier: { case_count: 4 },
  threshold_tuning: { combinations_swept: 85 },
  adversarial_suite: { passed_count: 4 },
  fallback_fidelity: { measurable: false },
  fairness_probe: { pair_count: 2 },
  drift_canary: { any_drifted: false },
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <ResearchReportPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  getMock.mockImplementation((path: string) => {
    if (path === "/research/report") return Promise.resolve(REPORT);
    return Promise.resolve(null);
  });
});

describe("ResearchReportPage", () => {
  it("generates and renders every report section with a print button", async () => {
    renderPage();
    expect(await screen.findByText(/CareerPilot AI Research Report/i)).toBeInTheDocument();
    expect(await screen.findByText("Confidence calibration")).toBeInTheDocument();
    expect(screen.getByText("Six-ablation comparison")).toBeInTheDocument();
    expect(screen.getByText("Scoring-drift canary")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /print/i })).toBeInTheDocument();
  });
});
