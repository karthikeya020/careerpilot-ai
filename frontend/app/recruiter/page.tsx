"use client";

import { AlertTriangle, Briefcase, ShieldCheck } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useRecruiterCandidates } from "@/hooks/use-role-dashboards";
import { ApiError } from "@/lib/api-client";
import { cn, formatPercent } from "@/lib/utils";

function RecruiterBody() {
  const { data: candidates, isLoading, isError, error, refetch } = useRecruiterCandidates();

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError) {
    const isPermissionDenied = error instanceof ApiError && error.status === 403;
    return (
      <ErrorState
        message={isPermissionDenied ? "This dashboard is only available to recruiter and administrator accounts." : error instanceof Error ? error.message : "Couldn't load candidates."}
        onRetry={isPermissionDenied ? undefined : () => refetch()}
        isPermissionDenied={isPermissionDenied}
        titleAs="h1"
      />
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border p-8 md:p-10" style={{ background: "radial-gradient(circle at 15% 80%, color-mix(in srgb, var(--brand-2) 18%, transparent), transparent 45%), var(--color-background)" }}>
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)]" style={{ background: "linear-gradient(135deg, var(--brand-2), var(--brand))" }}>
            <Briefcase className="h-5 w-5 text-white" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Recruiter Dashboard</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Only students who explicitly opted in to recruiter visibility appear here. No automatic hiring
          recommendation is ever computed.
        </p>
        <div className="relative mt-3 flex items-center gap-1.5 text-xs text-muted">
          <ShieldCheck className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          Evidence coverage and role alignment only — not a hiring decision.
        </div>
      </div>

      {!candidates || candidates.length === 0 ? (
        <EmptyState icon={Briefcase} title="No candidates have opted in yet" description="Students choose to share their evidence with recruiters from their Settings page." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {candidates.map((candidate, i) => (
            <Card key={candidate.student_profile_id} interactive className={cn("animate-fade-up", `delay-${Math.min(i + 1, 8)}`)}>
              <CardHeader>
                <CardTitle as="h2">{candidate.full_name}</CardTitle>
                <p className="text-xs text-muted">{candidate.target_role ?? "No target role set"}</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted">Overall readiness</span>
                  <span className="font-medium text-foreground">{formatPercent(candidate.overall_score)}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted">Confidence</span>
                  <span className="font-medium text-foreground">{formatPercent(candidate.overall_confidence)}</span>
                </div>
                {candidate.requires_human_review && (
                  <div className="flex items-center gap-1.5 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2 text-xs text-warning">
                    <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                    Some evidence for this candidate is flagged for human review.
                  </div>
                )}
                <div className="space-y-1">
                  {candidate.components.map((c) => (
                    <div key={c.component_type}>
                      <div className="mb-0.5 flex justify-between text-[11px] text-muted">
                        <span className="capitalize">{c.component_type.replaceAll("_", " ")}</span>
                        <span>{c.status === "scored" ? formatPercent(c.score) : "insufficient evidence"}</span>
                      </div>
                      <Progress
                        value={(c.score ?? 0) * 100}
                        aria-label={`${c.component_type.replaceAll("_", " ")}: ${c.status === "scored" ? formatPercent(c.score) : "insufficient evidence"}`}
                      />
                    </div>
                  ))}
                </div>
                <Badge variant="muted">Consent: {candidate.consent_status.replaceAll("_", " ")}</Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default function RecruiterPage() {
  return (
    <Protected>
      <RecruiterBody />
    </Protected>
  );
}
