"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";
import { CareActivityCard } from "@/components/dashboard/care-activity-card";
import { ComponentScoreCard } from "@/components/dashboard/component-score-card";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { EvidenceFeed } from "@/components/dashboard/evidence-feed";
import { JobDescriptionStatusCard } from "@/components/dashboard/jd-status-card";
import { MissionCard } from "@/components/dashboard/mission-card";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { ReadinessRadar } from "@/components/dashboard/readiness-radar";
import { ResumeStatusCard } from "@/components/dashboard/resume-status-card";
import { TrustIndicator } from "@/components/dashboard/trust-indicator";
import { TwinTimeline } from "@/components/dashboard/twin-timeline";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useDashboard } from "@/hooks/use-dashboard";
import { formatPercent, titleCase } from "@/lib/utils";

function DashboardBody() {
  const { data, isLoading, isError, error, refetch } = useDashboard();

  if (isLoading) return <DashboardSkeleton />;

  if (isError) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : "Couldn't load your dashboard."}
        onRetry={() => refetch()}
        titleAs="h1"
      />
    );
  }

  if (!data) return null;

  if (!data.onboarding_completed) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Finish onboarding to unlock your Career OS"
        description="We need your target role and a bit of self-assessment before we can build your Career Twin."
        action={
          <Button asChild>
            <Link href="/onboarding">Complete onboarding</Link>
          </Button>
        }
      />
    );
  }

  const twin = data.career_twin;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Welcome back, {data.student_name.split(" ")[0]}</h1>
          {data.target_role ? (
            <p className="mt-1 text-sm text-muted">
              Targeting <span className="font-medium text-foreground">{data.target_role.title}</span> ·{" "}
              {titleCase(data.target_role.seniority)}
            </p>
          ) : null}
        </div>
        {data.priority_weakness ? (
          <Badge variant="warning">Priority: {titleCase(data.priority_weakness.component_type.replace("_readiness", ""))}</Badge>
        ) : null}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Overall readiness</p>
            <p className="text-3xl font-semibold text-foreground">{formatPercent(twin?.overall_score)}</p>
            {twin?.score_delta !== null && twin?.score_delta !== undefined ? (
              <p className="text-xs text-positive">
                {twin.score_delta >= 0 ? "+" : ""}
                {Math.round(twin.score_delta * 100)}% since last update
              </p>
            ) : (
              <p className="text-xs text-muted">First snapshot</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Career Twin confidence</p>
            <p className="text-3xl font-semibold text-foreground">{formatPercent(twin?.overall_confidence)}</p>
            <p className="text-xs text-muted">Version {twin?.version ?? 0}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Evidence collected</p>
            <p className="text-3xl font-semibold text-foreground">{twin?.evidence_count ?? 0}</p>
            <p className="text-xs text-muted">items across all components</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardContent className="pt-5">
            <h2 className="mb-2 text-sm font-semibold text-foreground">Skill readiness overview</h2>
            {twin ? <ReadinessRadar components={twin.components} /> : null}
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {twin?.components.map((component) => (
                <ComponentScoreCard key={component.component_type} component={component} />
              ))}
            </div>
          </CardContent>
        </Card>
        <div className="space-y-4">
          <MissionCard mission={data.mission} />
          <TrustIndicator trust={data.system_trust} />
          <CareActivityCard />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <ResumeStatusCard status={data.resume_status} />
        <JobDescriptionStatusCard status={data.job_description_status} />
        <QuickActions />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <EvidenceFeed evidence={data.recent_evidence} />
        <TwinTimeline updates={data.recent_twin_updates} />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Protected>
      <DashboardBody />
    </Protected>
  );
}
