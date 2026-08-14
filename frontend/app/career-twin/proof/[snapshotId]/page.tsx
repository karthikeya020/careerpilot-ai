"use client";

import { useParams } from "next/navigation";
import { Printer, ShieldCheck } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useSnapshotProof } from "@/hooks/use-career-twin";
import { formatDateTime, formatPercent, titleCase } from "@/lib/utils";

function ProofBody() {
  const params = useParams<{ snapshotId: string }>();
  const { data: proof, isLoading, isError, error, refetch } = useSnapshotProof(params.snapshotId ?? null);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (isError || !proof) {
    return (
      <div className="mx-auto max-w-3xl">
        <ErrorState message={error instanceof Error ? error.message : "Couldn't load this snapshot proof."} onRetry={() => refetch()} titleAs="h1" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="print-hidden flex items-center justify-between">
        <p className="text-sm text-muted">A one-page, evidence-backed proof of readiness at this point in time.</p>
        <Button onClick={() => window.print()}>
          <Printer className="h-4 w-4" aria-hidden="true" /> Print / Save as PDF
        </Button>
      </div>

      <Card className="border-2 border-brand/30">
        <CardHeader className="flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand">
              <ShieldCheck className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
            </span>
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-foreground">
                {proof.student_name}&apos;s Career Twin Proof
              </h1>
              <p className="text-xs text-muted">
                Version {proof.version} · {formatDateTime(proof.created_at)}
                {proof.target_role ? ` · Targeting ${proof.target_role}` : ""}
              </p>
            </div>
          </div>
          <Badge>Formula {proof.formula_version}</Badge>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex flex-wrap gap-4 rounded-[var(--radius-md)] border border-border bg-surface-muted p-4">
            <div>
              <p className="text-[11px] uppercase tracking-wide text-muted">Overall readiness</p>
              <p className="text-2xl font-bold text-foreground">{formatPercent(proof.overall_score)}</p>
            </div>
            <div>
              <p className="text-[11px] uppercase tracking-wide text-muted">Overall confidence</p>
              <p className="text-2xl font-bold text-foreground">{formatPercent(proof.overall_confidence)}</p>
            </div>
          </div>

          {proof.components.map((component) => (
            <div key={component.component_type} className="border-t border-border pt-4">
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="text-sm font-semibold text-foreground">
                  {titleCase(component.component_type.replace("_readiness", ""))}
                </p>
                {component.status === "scored" ? (
                  <span className="text-sm font-bold tabular-nums text-foreground">
                    {formatPercent(component.score)} · confidence {formatPercent(component.confidence)}
                  </span>
                ) : (
                  <Badge variant="muted">Insufficient evidence</Badge>
                )}
              </div>
              {component.citations.length > 0 && (
                <ul className="space-y-1">
                  {component.citations.map((cite, i) => (
                    <li key={i} className="text-xs text-muted">
                      <span className="font-medium text-foreground">{cite.skill_name}</span> ·{" "}
                      {titleCase(cite.evidence_type)} · {cite.explanation}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}

          <p className="border-t border-border pt-4 text-[11px] leading-relaxed text-muted">{proof.disclaimer}</p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function SnapshotProofPage() {
  return (
    <Protected>
      <ProofBody />
    </Protected>
  );
}
