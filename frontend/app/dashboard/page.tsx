"use client";

import Link from "next/link";
import { Gauge, Layers, Sparkles } from "lucide-react";
import { CareActivityCard } from "@/components/dashboard/care-activity-card";
import { MilestoneBanner } from "@/components/career-twin/milestone-banner";
import { ComponentScoreCard } from "@/components/dashboard/component-score-card";
import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";
import { EvidenceCompositionChart } from "@/components/dashboard/evidence-composition-chart";
import { EvidenceFeed } from "@/components/dashboard/evidence-feed";
import { JobDescriptionStatusCard } from "@/components/dashboard/jd-status-card";
import { MissionCard } from "@/components/dashboard/mission-card";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { ReadinessRadar } from "@/components/dashboard/readiness-radar";
import { ReadinessTrendChart } from "@/components/dashboard/readiness-trend-chart";
import { ResumeStatusCard } from "@/components/dashboard/resume-status-card";
import { TrustIndicator } from "@/components/dashboard/trust-indicator";
import { TwinTimeline } from "@/components/dashboard/twin-timeline";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { useCountUp } from "@/hooks/use-count-up";
import { useDashboard } from "@/hooks/use-dashboard";
import { useStaggerReveal } from "@/hooks/use-stagger-reveal";
import { titleCase } from "@/lib/utils";

function StatNumber({ value, className }: { value: number | null | undefined; className?: string }) {
  const animated = useCountUp(value !== null && value !== undefined ? value * 100 : null);
  return <span className={className}>{value === null || value === undefined ? "—" : `${animated}%`}</span>;
}

function CountNumber({ value }: { value: number }) {
  return <>{useCountUp(value)}</>;
}

function DashboardBody() {
  const { data, isLoading, isError, error, refetch } = useDashboard();
  const statsRef = useStaggerReveal<HTMLDivElement>(data?.student_name, { delay: 90 });

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
      {twin && twin.milestones.length > 0 && <MilestoneBanner milestones={twin.milestones} />}

      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand text-lg font-bold text-brand-foreground shadow-[var(--shadow-glow-brand)]">
                {data.student_name.slice(0, 1)}
              </span>
              <h1 className="text-h1 text-foreground">Welcome back, {data.student_name.split(" ")[0]}</h1>
            </div>
            {data.target_role ? (
              <p className="relative mt-3 max-w-2xl text-sm text-muted">
                Targeting <span className="font-medium text-foreground">{data.target_role.title}</span> ·{" "}
                {titleCase(data.target_role.seniority)} · Career Twin version {twin?.version ?? 0}
              </p>
            ) : null}
          </div>
          {data.priority_weakness ? (
            <Badge variant="warning" className="animate-pulse-glow px-3 py-1 text-xs">
              Priority: {titleCase(data.priority_weakness.component_type.replace("_readiness", ""))}
            </Badge>
          ) : null}
        </div>

        <div ref={statsRef} className="relative mt-6 grid gap-4 sm:grid-cols-3">
          <div className="rounded-[var(--radius-lg)] border border-border bg-surface/70 p-4 backdrop-blur">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted">Overall readiness</p>
                <p className="text-metric text-gradient-brand">
                  <StatNumber value={twin?.overall_score} />
                </p>
                {twin?.score_delta !== null && twin?.score_delta !== undefined ? (
                  <p className="mt-1 text-xs font-medium text-positive">
                    {twin.score_delta >= 0 ? "+" : ""}
                    {Math.round(twin.score_delta * 100)}% since last update
                  </p>
                ) : (
                  <p className="mt-1 text-xs text-muted">First snapshot</p>
                )}
              </div>
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-sm)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
                <Gauge className="h-4 w-4 text-brand-foreground" aria-hidden="true" />
              </span>
            </div>
          </div>
          <div className="rounded-[var(--radius-lg)] border border-border bg-surface/70 p-4 backdrop-blur">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted">Career Twin confidence</p>
                <p className="text-metric text-foreground">
                  <StatNumber value={twin?.overall_confidence} />
                </p>
                <p className="mt-1 text-xs text-muted">Version {twin?.version ?? 0}</p>
              </div>
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-sm)] bg-accent-2/15 text-accent-2">
                <Sparkles className="h-4 w-4" aria-hidden="true" />
              </span>
            </div>
          </div>
          <div className="rounded-[var(--radius-lg)] border border-border bg-surface/70 p-4 backdrop-blur">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-muted">Evidence collected</p>
                <p className="text-metric text-foreground">
                  <CountNumber value={twin?.evidence_count ?? 0} />
                </p>
                <p className="mt-1 text-xs text-muted">items across all components</p>
              </div>
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-sm)] bg-positive/15 text-positive">
                <Layers className="h-4 w-4" aria-hidden="true" />
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ReadinessTrendChart />
        {twin ? <EvidenceCompositionChart components={twin.components} /> : null}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card variant="glow-brand" className="animate-fade-up delay-2 lg:col-span-2">
          <CardContent className="pt-5">
            <h2 className="mb-3 text-h3 text-foreground">Skill readiness overview</h2>
            {twin ? <ReadinessRadar components={twin.components} /> : null}
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {twin?.components.map((component) => (
                <ComponentScoreCard key={component.component_type} component={component} compact />
              ))}
            </div>
          </CardContent>
        </Card>
        <div className="animate-fade-up delay-3 space-y-4">
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
