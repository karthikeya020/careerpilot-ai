"use client";

import { AlertTriangle, Briefcase } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useRecruiterCandidates } from "@/hooks/use-role-dashboards";
import { formatPercent } from "@/lib/utils";

function RecruiterBody() {
  const { data: candidates, isLoading, isError, error, refetch } = useRecruiterCandidates();

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError) {
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load candidates."} onRetry={() => refetch()} />;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
          <Briefcase className="h-5 w-5 text-brand" aria-hidden="true" />
          Recruiter Dashboard
        </h1>
        <p className="mt-1 text-sm text-muted">
          Only students who explicitly opted in to recruiter visibility appear here. No automatic hiring recommendation is ever computed.
        </p>
      </div>

      {!candidates || candidates.length === 0 ? (
        <EmptyState title="No candidates have opted in yet" description="Students choose to share their evidence with recruiters from their Settings page." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {candidates.map((candidate) => (
            <Card key={candidate.student_profile_id}>
              <CardHeader>
                <CardTitle>{candidate.full_name}</CardTitle>
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
                    <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
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
                      <Progress value={(c.score ?? 0) * 100} />
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
