import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TwinTimeline } from "@/components/dashboard/twin-timeline";
import type { TwinUpdateSummaryOut } from "@/types/api";

const UPDATES: TwinUpdateSummaryOut[] = [
  {
    version: 5,
    created_at: "2026-08-04T15:10:00.000000",
    change_summary: "Completed 'SQL' assessment attempt. Overall readiness moved up by 0.0769 since version 4.",
    overall_score: 0.83,
    score_delta: 0.0769,
  },
  {
    version: 4,
    created_at: "2026-08-04T14:48:00.000000",
    change_summary: "Completed 'SQL' assessment attempt. Overall readiness moved down by 0.0603 since version 3.",
    overall_score: 0.75,
    score_delta: -0.0603,
  },
  {
    version: 1,
    created_at: "2026-08-04T14:00:00.000000",
    change_summary: "Onboarding completed: target role and self-assessment recorded. This is the first Career Twin snapshot for this student.",
    overall_score: 0.5,
    score_delta: null,
  },
];

describe("TwinTimeline", () => {
  it("shows an empty state before any Career Twin snapshot exists", () => {
    render(<TwinTimeline updates={[]} />);
    expect(screen.getByText("No updates yet")).toBeInTheDocument();
  });

  it("renders every snapshot version with its exact change explanation", () => {
    render(<TwinTimeline updates={UPDATES} />);
    expect(screen.getByText("Version 5")).toBeInTheDocument();
    expect(screen.getByText(/moved up by 0.0769 since version 4/)).toBeInTheDocument();
    expect(screen.getByText("Version 4")).toBeInTheDocument();
    expect(screen.getByText(/moved down by 0.0603 since version 3/)).toBeInTheDocument();
    expect(screen.getByText("Version 1")).toBeInTheDocument();
    expect(screen.getByText(/first Career Twin snapshot/)).toBeInTheDocument();
  });

  it("shows a signed percentage delta for score increases and decreases", () => {
    render(<TwinTimeline updates={UPDATES} />);
    expect(screen.getByText(/Overall 83% \(\+8%\)/)).toBeInTheDocument();
    expect(screen.getByText(/Overall 75% \(-6%\)/)).toBeInTheDocument();
  });

  it("renders no delta annotation for the first snapshot, which has none to compare against", () => {
    render(<TwinTimeline updates={UPDATES} />);
    expect(screen.getByText("Overall 50%")).toBeInTheDocument();
  });

  it("preserves immutable snapshot ordering as given, without re-sorting or collapsing history", () => {
    render(<TwinTimeline updates={UPDATES} />);
    const versionLabels = screen.getAllByText(/^Version \d+$/).map((el) => el.textContent);
    expect(versionLabels).toEqual(["Version 5", "Version 4", "Version 1"]);
  });
});
