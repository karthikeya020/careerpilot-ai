"use client";

import { Building2 } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { usePlacementDashboard } from "@/hooks/use-role-dashboards";
import { formatPercent } from "@/lib/utils";

function PlacementBody() {
  const { data, isLoading, isError, error, refetch } = usePlacementDashboard();

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) {
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load the placement dashboard."} onRetry={() => refetch()} />;
  }

  const maxCount = Math.max(1, ...data.readiness_distribution.map((b) => b.student_count));

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
          <Building2 className="h-5 w-5 text-brand" aria-hidden="true" />
          Placement-Cell Dashboard
        </h1>
        <p className="mt-1 text-sm text-muted">
          Cohort readiness distribution across {data.student_count_with_snapshot} student(s) with a Career Twin snapshot.
        </p>
      </div>

      <div className="rounded-[var(--radius-md)] border border-brand/30 bg-brand-soft p-3 text-center text-xs font-medium text-brand">
        {data.disclaimer}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Readiness distribution</CardTitle>
          <CardDescription>Number of students by overall Career Twin readiness range.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-end gap-3" style={{ height: 160 }}>
            {data.readiness_distribution.map((bucket) => (
              <div key={bucket.range_start} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t bg-brand"
                  style={{ height: `${Math.max(4, (bucket.student_count / maxCount) * 130)}px` }}
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
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Average role alignment</p>
            <p className="text-3xl font-semibold text-foreground">{formatPercent(data.role_alignment_average)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Program effectiveness (avg. Twin delta)</p>
            <p className="text-3xl font-semibold text-foreground">
              {data.program_effectiveness_average_delta !== null
                ? `${data.program_effectiveness_average_delta >= 0 ? "+" : ""}${(data.program_effectiveness_average_delta * 100).toFixed(1)}%`
                : "—"}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Most common skill gaps</CardTitle>
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
