import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CareActivityCard } from "@/components/dashboard/care-activity-card";
import type { CareExecutionSummaryOut } from "@/types/api";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: getMock, post: vi.fn(), patch: vi.fn(), delete: vi.fn() } };
});

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

function renderCard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <CareActivityCard />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  getMock.mockReset();
});

describe("CareActivityCard", () => {
  it("shows an empty state before any CARE decision has run", async () => {
    getMock.mockResolvedValueOnce([]);
    renderCard();
    expect(await screen.findByText("No AI decisions yet")).toBeInTheDocument();
  });

  it("lists recent CARE task types with a human-readable route badge", async () => {
    getMock.mockResolvedValueOnce(EXECUTIONS);
    renderCard();
    expect(await screen.findByText("Root Cause Analysis")).toBeInTheDocument();
    expect(screen.getByText("Single specialist")).toBeInTheDocument();
  });

  it("links through to the full Trust Center", async () => {
    getMock.mockResolvedValueOnce(EXECUTIONS);
    renderCard();
    await screen.findByText("Root Cause Analysis");
    expect(screen.getByRole("link", { name: /view trust center/i })).toHaveAttribute("href", "/trust-center");
  });
});
