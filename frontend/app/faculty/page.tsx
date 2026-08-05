"use client";

import { AlertTriangle, Users } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useFacultyDashboard } from "@/hooks/use-role-dashboards";
import { ApiError } from "@/lib/api-client";
import { formatPercent } from "@/lib/utils";

function FacultyBody() {
  const { data, isLoading, isError, error, refetch } = useFacultyDashboard();

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) {
    const isPermissionDenied = error instanceof ApiError && error.status === 403;
    return (
      <ErrorState
        message={isPermissionDenied ? "This dashboard is only available to faculty and administrator accounts." : error instanceof Error ? error.message : "Couldn't load the faculty dashboard."}
        onRetry={isPermissionDenied ? undefined : () => refetch()}
        isPermissionDenied={isPermissionDenied}
      />
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
          <Users className="h-5 w-5 text-brand" aria-hidden="true" />
          Faculty Dashboard
        </h1>
        <p className="mt-1 text-sm text-muted">
          Cohort-level, privacy-safe aggregates -- {data.total_students} student(s). No individual scores or rankings are shown here.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Mission completion rate</p>
            <p className="text-3xl font-semibold text-foreground">{formatPercent(data.mission_completion_rate)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Assessment completion rate</p>
            <p className="text-3xl font-semibold text-foreground">{formatPercent(data.assessment_completion_rate)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Average readiness trend</p>
            <p className="text-3xl font-semibold text-foreground">
              {data.average_readiness_trend !== null ? `${data.average_readiness_trend >= 0 ? "+" : ""}${(data.average_readiness_trend * 100).toFixed(1)}%` : "—"}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Cohort skill gaps</CardTitle>
          <CardDescription>Average readiness component score across the cohort&apos;s most recent Career Twin snapshots.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.cohort_skill_gaps.map((gap) => (
            <div key={gap.component_type}>
              <div className="mb-1 flex items-center justify-between text-xs text-muted">
                <span className="capitalize">{gap.component_type.replaceAll("_", " ")}</span>
                <span>
                  {gap.average_score !== null ? formatPercent(gap.average_score) : "insufficient data"} ({gap.scored_student_count} scored)
                </span>
              </div>
              <Progress value={(gap.average_score ?? 0) * 100} />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Students requiring human support</CardTitle>
          <CardDescription>Flagged by CARE for persistently low-confidence decisions -- a real signal for outreach, not a ranking.</CardDescription>
        </CardHeader>
        <CardContent>
          {data.students_needing_support.length === 0 ? (
            <EmptyState title="No students currently flagged" />
          ) : (
            <ul className="space-y-2">
              {data.students_needing_support.map((s) => (
                <li key={s.student_profile_id} className="flex items-center justify-between rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2 text-sm">
                  <span className="flex items-center gap-2 text-foreground">
                    <AlertTriangle className="h-3.5 w-3.5 text-warning" aria-hidden="true" />
                    {s.full_name}
                  </span>
                  <Badge variant="warning">{s.flagged_decision_count} flagged decision(s)</Badge>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function FacultyPage() {
  return (
    <Protected>
      <FacultyBody />
    </Protected>
  );
}
