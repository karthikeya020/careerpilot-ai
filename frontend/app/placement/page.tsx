"use client";

import { AlertTriangle, BarChart3, Building2 } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { usePlacementDashboard } from "@/hooks/use-role-dashboards";
import { ApiError } from "@/lib/api-client";
import { cn, formatPercent } from "@/lib/utils";

function PlacementBody() {
  const { data, isLoading, isError, error, refetch } = usePlacementDashboard();

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) {
    const isPermissionDenied = error instanceof ApiError && error.status === 403;
    return (
      <ErrorState
        message={isPermissionDenied ? "This dashboard is only available to placement-staff and administrator accounts." : error instanceof Error ? error.message : "Couldn't load the placement dashboard."}
        onRetry={isPermissionDenied ? undefined : () => refetch()}
        isPermissionDenied={isPermissionDenied}
        titleAs="h1"
      />
    );
  }

  const maxCount = Math.max(1, ...data.readiness_distribution.map((b) => b.student_count));
  const isCohortOfOne = data.student_count_with_snapshot <= 1;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border p-8 md:p-10" style={{ background: "radial-gradient(circle at 85% 20%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 45%), var(--color-background)" }}>
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)]" style={{ background: "linear-gradient(135deg, var(--accent), var(--accent-2))" }}>
            <Building2 className="h-5 w-5 text-white" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Placement-Cell Dashboard</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Cohort readiness distribution across {data.student_count_with_snapshot} student(s) with a Career Twin snapshot.
        </p>
        {isCohortOfOne && (
          <div className="relative mt-3 flex items-start gap-2 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-3 text-xs text-warning">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            Cohort of one: the distribution and averages below reflect a single student, not an institutional trend.
          </div>
        )}
      </div>

      <div className="animate-fade-up delay-1 rounded-[var(--radius-md)] border border-brand/30 bg-brand-soft p-3 text-center text-xs font-medium text-brand">
        {data.disclaimer}
      </div>

      <Card className="animate-fade-up delay-2">
        <CardHeader>
          <CardTitle as="h2" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" style={{ color: "var(--accent)" }} aria-hidden="true" /> Readiness distribution
          </CardTitle>
          <CardDescription>Number of students by overall Career Twin readiness range.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-3" style={{ height: 160 }}>
            {data.readiness_distribution.map((bucket, i) => (
              <div key={bucket.range_start} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className={cn("w-full rounded-t transition-[height] duration-700 ease-out")}
                  style={{
                    height: `${Math.max(4, (bucket.student_count / maxCount) * 130)}px`,
                    background: "linear-gradient(180deg, var(--accent-2), var(--accent))",
                    animationDelay: `${i * 80}ms`,
                  }}
                />
                <span className="text-xs font-medium text-foreground">{bucket.student_count}</span>
                <span className="text-[10px] text-muted">
                  {bucket.range_start}-{bucket.range_end}%
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="animate-fade-up delay-3">
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Average role alignment</p>
            <p className="text-metric text-foreground">{formatPercent(data.role_alignment_average)}</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-up delay-4">
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Program effectiveness (avg. Twin delta)</p>
            <p className="text-metric text-foreground">
              {data.program_effectiveness_average_delta !== null
                ? `${data.program_effectiveness_average_delta >= 0 ? "+" : ""}${(data.program_effectiveness_average_delta * 100).toFixed(1)}%`
                : "—"}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="animate-fade-up delay-5">
        <CardHeader>
          <CardTitle as="h2">Most common skill gaps</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {data.common_skill_gaps.map((gap) => (
            <div key={gap.component_type} className="flex items-center justify-between text-sm">
              <span className="capitalize text-foreground">{gap.component_type.replaceAll("_", " ")}</span>
              <span className="text-muted">{formatPercent(gap.average_score)}</span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export default function PlacementPage() {
  return (
    <Protected>
      <PlacementBody />
    </Protected>
  );
}
