import { AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import type { ReadinessComponentOut } from "@/types/api";
import { formatPercent, titleCase } from "@/lib/utils";

export function ComponentScoreCard({ component }: { component: ReadinessComponentOut }) {
  const label = titleCase(component.component_type.replace("_readiness", ""));
  const isScored = component.status === "scored";

  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-surface p-4">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-sm font-medium text-foreground">{label}</p>
        {isScored ? (
          <span className="text-sm font-semibold text-foreground">{formatPercent(component.score)}</span>
        ) : (
          <Badge variant="muted">Insufficient evidence</Badge>
        )}
      </div>
      <Progress
        value={isScored ? (component.score ?? 0) * 100 : 0}
        className="mb-2"
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
        <div className="mt-2 flex items-start gap-1.5 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2 text-xs text-warning">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span>{component.low_sample_notice}</span>
        </div>
      )}
      <p className="mt-2 text-xs text-muted">{component.explanation}</p>
    </div>
  );
}
