"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Briefcase,
  ChevronDown,
  ClipboardCheck,
  Clock,
  Cpu,
  FileText,
  GitBranch,
  MessageSquare,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { ReadinessComponentOut } from "@/types/api";
import { cn, formatPercent, titleCase } from "@/lib/utils";

const PROVENANCE_COLORS = [
  "var(--color-brand)",
  "var(--color-accent-2)",
  "var(--color-positive)",
  "var(--color-warning)",
  "var(--color-accent)",
];

const COMPONENT_ICON: Record<string, typeof FileText> = {
  resume_readiness: FileText,
  technical_readiness: Cpu,
  communication_readiness: MessageSquare,
  assessment_readiness: ClipboardCheck,
  portfolio_readiness: Briefcase,
  role_alignment_readiness: Target,
};

export function ComponentScoreCard({
  component,
  compact = false,
}: {
  component: ReadinessComponentOut;
  compact?: boolean;
}) {
  const [reasoningOpen, setReasoningOpen] = useState(false);
  const label = titleCase(component.component_type.replace("_readiness", ""));
  const isScored = component.status === "scored";
  const Icon = COMPONENT_ICON[component.component_type] ?? Sparkles;
  const trendPercent = component.trend !== null ? Math.round(component.trend * 100) : null;

  return (
    <div className="card-premium card-premium-hover rounded-[var(--radius-md)] p-4">
      <div className="mb-2.5 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[var(--radius-sm)] bg-brand-soft">
            <Icon className="h-3.5 w-3.5 text-brand" aria-hidden="true" />
          </span>
          <p className="text-sm font-medium text-foreground">{label}</p>
        </div>
        {isScored ? (
          <div className="flex items-center gap-1.5">
            {trendPercent !== null && trendPercent !== 0 && (
              <span
                className={cn(
                  "flex items-center gap-0.5 text-[11px] font-medium tabular-nums",
                  trendPercent > 0 ? "text-positive" : "text-danger",
                )}
              >
                {trendPercent > 0 ? (
                  <TrendingUp className="h-3 w-3" aria-hidden="true" />
                ) : (
                  <TrendingDown className="h-3 w-3" aria-hidden="true" />
                )}
                {trendPercent > 0 ? "+" : ""}
                {trendPercent}%
              </span>
            )}
            <span className="text-lg font-bold tabular-nums text-foreground">{formatPercent(component.score)}</span>
          </div>
        ) : (
          <Badge variant="muted">Insufficient evidence</Badge>
        )}
      </div>
      <Progress
        value={isScored ? (component.score ?? 0) * 100 : 0}
        className="mb-2.5"
        aria-label={`${label} readiness: ${isScored ? formatPercent(component.score) : "insufficient evidence"}`}
      />
      <div className="flex items-center justify-between text-xs text-muted">
        <span>{component.evidence_count} evidence item{component.evidence_count === 1 ? "" : "s"}</span>
        {isScored ? <span>Confidence {formatPercent(component.confidence)}</span> : null}
      </div>
      {isScored && (
        <p className="mt-1 text-xs text-muted">
          {component.evidence_diversity} independent source{component.evidence_diversity === 1 ? "" : "s"}
        </p>
      )}
      {component.is_low_sample && component.low_sample_notice && (
        <div className="mt-2.5 flex items-start gap-1.5 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2 text-xs text-warning">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span>{component.low_sample_notice}</span>
        </div>
      )}
      {component.is_stale_evidence && component.stale_evidence_notice && (
        <div className="mt-2.5 flex items-start gap-1.5 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2 text-xs text-warning">
          <Clock className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span>{component.stale_evidence_notice}</span>
        </div>
      )}
      {!compact && isScored && Object.keys(component.provenance).length > 0 && (
        <div className="mt-2.5">
          <p className="mb-1 text-[11px] font-medium uppercase tracking-wide text-muted">Built from</p>
          <div className="flex h-1.5 w-full overflow-hidden rounded-full bg-surface-muted">
            {Object.entries(component.provenance).map(([type, fraction], i) => (
              <span
                key={type}
                style={{ width: `${fraction * 100}%`, background: PROVENANCE_COLORS[i % PROVENANCE_COLORS.length] }}
                title={`${titleCase(type)}: ${formatPercent(fraction)}`}
              />
            ))}
          </div>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-muted">
            {Object.entries(component.provenance).map(([type, fraction], i) => (
              <span key={type} className="flex items-center gap-1">
                <span
                  className="h-1.5 w-1.5 rounded-full"
                  style={{ background: PROVENANCE_COLORS[i % PROVENANCE_COLORS.length] }}
                />
                {titleCase(type)} {formatPercent(fraction)}
              </span>
            ))}
          </div>
        </div>
      )}
      {!compact && component.ripple_notes.length > 0 && (
        <div className="mt-2.5 space-y-1">
          {component.ripple_notes.map((note, i) => (
            <p key={i} className="flex items-start gap-1.5 text-[11px] leading-relaxed text-muted">
              <GitBranch className="mt-0.5 h-3 w-3 shrink-0 text-brand" aria-hidden="true" />
              <span>
                <span className="font-medium text-foreground">This also affects {titleCase(note.target_component.replace("_readiness", ""))}:</span>{" "}
                {note.reason}
              </span>
            </p>
          ))}
        </div>
      )}
      <button
        type="button"
        onClick={() => setReasoningOpen((o) => !o)}
        className="mt-2.5 flex w-full items-center justify-between gap-2 rounded-[var(--radius-sm)] text-left text-xs font-medium text-muted transition-colors hover:text-foreground"
        aria-expanded={reasoningOpen}
      >
        <span>Why this score?</span>
        <ChevronDown className={cn("h-3.5 w-3.5 shrink-0 transition-transform", reasoningOpen && "rotate-180")} aria-hidden="true" />
      </button>
      {reasoningOpen && <p className="animate-fade-in mt-1.5 text-xs leading-relaxed text-muted">{component.explanation}</p>}
    </div>
  );
}
