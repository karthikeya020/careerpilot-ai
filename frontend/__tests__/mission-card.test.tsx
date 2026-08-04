import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MissionCard } from "@/components/dashboard/mission-card";
import type { LearningMissionOut } from "@/types/api";

const { postMock } = vi.hoisted(() => ({ postMock: vi.fn() }));

vi.mock("@/lib/api-client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api-client")>("@/lib/api-client");
  return { ...actual, api: { get: vi.fn(), post: postMock, patch: vi.fn(), delete: vi.fn() } };
});

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const ROOT_CAUSE_MISSION: LearningMissionOut = {
  id: "mission-1",
  title: "Close the gap: Inner Join",
  description:
    "Aanya Sharma answered a question incorrectly -> Question tests concept: Inner Join -> Inner Join depends on Joins.",
  target_skill: null,
  source_component: "technical_readiness",
  status: "pending",
  created_at: "2026-08-04T14:29:50.000000",
  completed_at: null,
};

function renderCard(mission: LearningMissionOut | null) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MissionCard mission={mission} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  postMock.mockReset();
});

describe("MissionCard", () => {
  it("shows an empty state when there is no active mission", () => {
    renderCard(null);
    expect(screen.getByText("No mission yet")).toBeInTheDocument();
  });

  it("renders the mission title, root-cause description, and source component badge", () => {
    renderCard(ROOT_CAUSE_MISSION);
    expect(screen.getByText("Close the gap: Inner Join")).toBeInTheDocument();
    expect(screen.getByText(/Inner Join depends on Joins/)).toBeInTheDocument();
    expect(screen.getByText("Technical")).toBeInTheDocument();
  });

  it("links to the Trust Center so the student can see why the mission was generated", () => {
    renderCard(ROOT_CAUSE_MISSION);
    const link = screen.getByRole("link", { name: /why\?/i });
    expect(link).toHaveAttribute("href", "/trust-center");
  });

  it("marks the mission complete and disables the button afterward", async () => {
    postMock.mockResolvedValueOnce({ ...ROOT_CAUSE_MISSION, status: "completed" });
    const user = userEvent.setup();
    renderCard(ROOT_CAUSE_MISSION);

    await user.click(screen.getByRole("button", { name: /mark complete/i }));

    await waitFor(() => expect(postMock).toHaveBeenCalledWith("/missions/mission-1/complete"));
  });

  it("does not allow re-completing an already-completed mission", () => {
    renderCard({ ...ROOT_CAUSE_MISSION, status: "completed" });
    expect(screen.getByRole("button", { name: /completed/i })).toBeDisabled();
  });
});
