import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ComponentScoreCard } from "@/components/dashboard/component-score-card";
import type { ReadinessComponentOut } from "@/types/api";

const LOW_SAMPLE_COMPONENT: ReadinessComponentOut = {
  component_type: "technical_readiness",
  score: 0.55,
  confidence: 0.14,
  status: "scored",
  evidence_count: 2,
  explanation: "Derived from 2 evidence item(s) from 1 distinct source(s)...",
  trend: null,
  uncertainty: 0.86,
  evidence_diversity: 1,
  is_low_sample: true,
  low_sample_notice: "Strong performance in this session, but more evidence is required to establish long-term proficiency.",
};

const ESTABLISHED_COMPONENT: ReadinessComponentOut = {
  ...LOW_SAMPLE_COMPONENT,
  score: 0.85,
  confidence: 0.68,
  evidence_count: 5,
  evidence_diversity: 3,
  is_low_sample: false,
  low_sample_notice: null,
};

describe("ComponentScoreCard", () => {
  it("shows the low-sample notice when evidence is sparse or narrowly sourced", () => {
    render(<ComponentScoreCard component={LOW_SAMPLE_COMPONENT} />);
    expect(screen.getByText(/more evidence is required to establish long-term proficiency/i)).toBeInTheDocument();
    expect(screen.getByText(/1 independent source/i)).toBeInTheDocument();
  });

  it("does not show the low-sample notice once evidence is diverse and sufficient", () => {
    render(<ComponentScoreCard component={ESTABLISHED_COMPONENT} />);
    expect(screen.queryByText(/more evidence is required/i)).not.toBeInTheDocument();
    expect(screen.getByText(/3 independent sources/i)).toBeInTheDocument();
  });
});
