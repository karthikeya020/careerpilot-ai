"use client";

import { AlertTriangle, GraduationCap, TrendingUp, Users } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useFacultyDashboard } from "@/hooks/use-role-dashboards";
import { ApiError } from "@/lib/api-client";
import { cn, formatPercent } from "@/lib/utils";

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
        titleAs="h1"
      />
    );
  }

  const isCohortOfOne = data.total_students <= 1;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border p-8 md:p-10" style={{ background: "radial-gradient(circle at 15% 20%, color-mix(in srgb, var(--accent-2) 18%, transparent), transparent 45%), var(--color-background)" }}>
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)]" style={{ background: "linear-gradient(135deg, var(--accent-2), var(--accent))" }}>
            <GraduationCap className="h-5 w-5 text-white" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Faculty Dashboard</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Cohort-level, privacy-safe aggregates — {data.total_students} student(s). No individual scores or rankings
          are shown here.
        </p>
        {isCohortOfOne && (
          <div className="relative mt-3 flex items-start gap-2 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-3 text-xs text-warning">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            Cohort of one: these aggregates currently reflect a single active student, not a statistically meaningful
            cohort. Treat every number below as anecdotal until more students onboard.
          </div>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card className="animate-fade-up delay-1">
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Mission completion rate</p>
            <p className="text-metric text-foreground">{formatPercent(data.mission_completion_rate)}</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-up delay-2">
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Assessment completion rate</p>
            <p className="text-metric text-foreground">{formatPercent(data.assessment_completion_rate)}</p>
          </CardContent>
        </Card>
        <Card className="animate-fade-up delay-3">
          <CardContent className="pt-5">
            <p className="flex items-center gap-1 text-xs text-muted">
              <TrendingUp className="h-3 w-3" aria-hidden="true" /> Average readiness trend
            </p>
            <p className="text-metric text-foreground">
              {data.average_readiness_trend !== null ? `${data.average_readiness_trend >= 0 ? "+" : ""}${(data.average_readiness_trend * 100).toFixed(1)}%` : "—"}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="animate-fade-up delay-4">
        <CardHeader>
          <CardTitle as="h2">Cohort skill gaps</CardTitle>
          <CardDescription>Average readiness component score across the cohort&apos;s most recent Career Twin snapshots.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.cohort_skill_gaps.map((gap, i) => (
            <div key={gap.component_type} className={cn("animate-fade-up", `delay-${Math.min(i + 1, 8)}`)}>
              <div className="mb-1 flex items-center justify-between text-xs text-muted">
                <span className="capitalize">{gap.component_type.replaceAll("_", " ")}</span>
                <span>
                  {gap.average_score !== null ? formatPercent(gap.average_score) : "insufficient data"} ({gap.scored_student_count} scored)
                </span>
              </div>
              <Progress
                value={(gap.average_score ?? 0) * 100}
                aria-label={`${gap.component_type.replaceAll("_", " ")}: ${gap.average_score !== null ? formatPercent(gap.average_score) : "insufficient data"}`}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="animate-fade-up delay-5">
        <CardHeader>
          <CardTitle as="h2" className="flex items-center gap-2">
            <Users className="h-4 w-4 text-accent-2" aria-hidden="true" /> Students requiring human support
          </CardTitle>
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
