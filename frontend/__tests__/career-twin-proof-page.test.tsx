import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SnapshotProofPage from "@/app/career-twin/proof/[snapshotId]/page";
import type { SnapshotProofOut } from "@/types/api";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/career-twin/proof/snap-1",
  useParams: () => ({ snapshotId: "snap-1" }),
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({ user: { id: "1", email: "student@example.com", roles: ["student"] }, isLoading: false, logout: vi.fn() }),
}));

vi.mock("@/lib/theme-provider", () => ({ useTheme: () => ({ theme: "dark", toggle: vi.fn() }) }));
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const PROOF: SnapshotProofOut = {
  student_name: "Aanya Sharma",
  target_role: "Backend Engineering Intern",
  version: 4,
  created_at: "2026-08-06T00:00:00Z",
  overall_score: 0.72,
  overall_confidence: 0.55,
  formula_version: "twin-v2",
  disclaimer: "This is a snapshot of evidence-backed readiness -- not a hiring recommendation, guarantee, or ranking against other students.",
  components: [
    {
      component_type: "technical_readiness",
      score: 0.75,
      confidence: 0.6,
      status: "scored",
      evidence_count: 2,
      citations: [
        { skill_name: "Python", evidence_type: "resume", explanation: "Found in Projects section.", created_at: "2026-08-01T00:00:00Z" },
      ],
    },
  ],
};

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <SnapshotProofPage />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
  getMock.mockImplementation((url: string) => {
    if (url === "/career-twin/snap-1/proof") return Promise.resolve(PROOF);
    return Promise.resolve(null);
  });
});

describe("SnapshotProofPage", () => {
  it("renders the student name, evidence citations, and non-hiring disclaimer", async () => {
    renderPage();
    expect(await screen.findByText(/Aanya Sharma's Career Twin Proof/i)).toBeInTheDocument();
    expect(await screen.findByText("Python")).toBeInTheDocument();
    expect(screen.getByText(/found in projects section/i)).toBeInTheDocument();
    expect(screen.getByText(/not a hiring recommendation/i)).toBeInTheDocument();
  });

  it("has a print button", async () => {
    renderPage();
    expect(await screen.findByRole("button", { name: /print/i })).toBeInTheDocument();
  });
});
