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
import { PageHeader } from "@/components/ui/page-header";
import { Reveal } from "@/components/ui/reveal";
import { Section } from "@/components/ui/section";
import { Stat, StatGrid } from "@/components/ui/stat";
import { useCountUp } from "@/hooks/use-count-up";
import { useDashboard } from "@/hooks/use-dashboard";
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
  const firstName = data.student_name.split(" ")[0];

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      {twin && twin.milestones.length > 0 && <MilestoneBanner milestones={twin.milestones} />}

      <Reveal>
        <PageHeader
          eyebrow="Career OS"
          title={`Welcome back, ${firstName}`}
          description={
            data.target_role ? (
              <>
                Targeting <span className="font-medium text-foreground">{data.target_role.title}</span> ·{" "}
                {titleCase(data.target_role.seniority)} · Career Twin v{twin?.version ?? 0}
              </>
            ) : (
              "Set a target role to start building your Career Twin."
            )
          }
          actions={
            data.priority_weakness ? (
              <Badge variant="warning" className="px-3 py-1 text-xs">
                Priority: {titleCase(data.priority_weakness.component_type.replace("_readiness", ""))}
              </Badge>
            ) : undefined
          }
        />
      </Reveal>

      <Reveal delay={60}>
        <StatGrid className="lg:grid-cols-3">
          <Stat
            label="Overall readiness"
            value={<StatNumber value={twin?.overall_score} />}
            delta={twin?.score_delta ?? null}
            hint={
              twin?.score_delta === null || twin?.score_delta === undefined ? "first snapshot" : "since last update"
            }
            icon={Gauge}
          />
          <Stat
            label="Career Twin confidence"
            value={<StatNumber value={twin?.overall_confidence} />}
            hint={`version ${twin?.version ?? 0}`}
            icon={Sparkles}
            accent="var(--color-accent-2)"
          />
          <Stat
            label="Evidence collected"
            value={<CountNumber value={twin?.evidence_count ?? 0} />}
            hint="items across all components"
            icon={Layers}
            accent="var(--color-positive)"
          />
        </StatGrid>
      </Reveal>

      <Reveal delay={90}>
        <div className="grid gap-4 lg:grid-cols-2">
          <ReadinessTrendChart />
          {twin ? <EvidenceCompositionChart components={twin.components} /> : null}
        </div>
      </Reveal>

      <Reveal delay={120}>
        <Section eyebrow="Career Twin" title="Skill readiness overview">
          <div className="grid gap-4 lg:grid-cols-3">
            <Card variant="glow-brand" className="lg:col-span-2">
              <CardContent className="pt-5">
                {twin ? <ReadinessRadar components={twin.components} /> : null}
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {twin?.components.map((component) => (
                    <ComponentScoreCard key={component.component_type} component={component} compact />
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
        </Section>
      </Reveal>

      <Reveal delay={60}>
        <Section eyebrow="Inputs" title="Your material">
          <div className="grid gap-4 md:grid-cols-3">
            <ResumeStatusCard status={data.resume_status} />
            <JobDescriptionStatusCard status={data.job_description_status} />
            <QuickActions />
          </div>
        </Section>
      </Reveal>

      <Reveal delay={60}>
        <Section eyebrow="Activity" title="What changed recently">
          <div className="grid gap-4 lg:grid-cols-2">
            <EvidenceFeed evidence={data.recent_evidence} />
            <TwinTimeline updates={data.recent_twin_updates} />
          </div>
        </Section>
      </Reveal>
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
