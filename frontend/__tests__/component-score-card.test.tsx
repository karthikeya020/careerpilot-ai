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
  stale_evidence_fraction: 0,
  is_stale_evidence: false,
  stale_evidence_notice: null,
  ripple_notes: [],
  provenance: {},
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

const STALE_COMPONENT: ReadinessComponentOut = {
  ...ESTABLISHED_COMPONENT,
  is_stale_evidence: true,
  stale_evidence_fraction: 0.67,
  stale_evidence_notice: "This component's confidence is capped because 67% of its evidence is 6+ months old.",
};

const RIPPLE_COMPONENT: ReadinessComponentOut = {
  ...ESTABLISHED_COMPONENT,
  provenance: { resume: 0.6, technical_assessment: 0.4 },
  ripple_notes: [
    { target_component: "role_alignment_readiness", reason: "Shares evidence for Python with Role Alignment." },
  ],
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

  it("shows the freshness notice when a majority of evidence is stale", () => {
    render(<ComponentScoreCard component={STALE_COMPONENT} />);
    expect(screen.getByText(/6\+ months old/i)).toBeInTheDocument();
  });

  it("renders the provenance breakdown and ripple-effect notes when not compact", () => {
    render(<ComponentScoreCard component={RIPPLE_COMPONENT} />);
    expect(screen.getByText(/built from/i)).toBeInTheDocument();
    expect(screen.getByText(/this also affects role alignment/i)).toBeInTheDocument();
  });

  it("hides provenance and ripple notes in compact mode", () => {
    render(<ComponentScoreCard component={RIPPLE_COMPONENT} compact />);
    expect(screen.queryByText(/built from/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/this also affects/i)).not.toBeInTheDocument();
  });
});
