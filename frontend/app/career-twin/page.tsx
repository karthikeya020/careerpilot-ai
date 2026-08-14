"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { FileDown, Sparkles } from "lucide-react";
import { ComponentScoreCard } from "@/components/dashboard/component-score-card";
import { ReadinessRadar } from "@/components/dashboard/readiness-radar";
import { TwinTimeline } from "@/components/dashboard/twin-timeline";
import { GithubProfilePanel } from "@/components/career-twin/github-profile-panel";
import { MilestoneBanner } from "@/components/career-twin/milestone-banner";
import { MultiRolePanel } from "@/components/career-twin/multi-role-panel";
import { StrengthChainsPanel } from "@/components/career-twin/strength-chains-panel";
import { TimeToTargetPanel } from "@/components/career-twin/time-to-target-panel";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useCareerTwin, useCareerTwinHistory } from "@/hooks/use-career-twin";
import { useCountUp } from "@/hooks/use-count-up";
import { useStaggerReveal } from "@/hooks/use-stagger-reveal";
import { ApiError } from "@/lib/api-client";
import { formatPercent, titleCase } from "@/lib/utils";
import type { ReadinessComponentOut } from "@/types/api";

const RING_RADIUS = 84;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;
const NODE_RADIUS = 84;

function scoreColor(score: number | null, isScored: boolean): string {
  if (!isScored || score === null) return "var(--color-muted)";
  if (score >= 0.7) return "var(--color-positive)";
  if (score >= 0.4) return "var(--color-warning)";
  return "var(--color-danger)";
}

function TwinCenterpiece({
  overallScore,
  overallConfidence,
  version,
  components,
}: {
  overallScore: number | null;
  overallConfidence: number | null;
  version: number;
  components: ReadinessComponentOut[];
}) {
  const [animated, setAnimated] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 80);
    return () => clearTimeout(t);
  }, []);

  const scorePct = overallScore ?? 0;
  const confidencePct = overallConfidence ?? 0;
  const animatedScore = useCountUp(scorePct * 100);
  const scoreOffset = RING_CIRCUMFERENCE * (1 - (animated ? scorePct : 0));

  const angleStep = (2 * Math.PI) / Math.max(components.length, 1);

  return (
    <Card variant="glow-brand" className="relative overflow-hidden">
      <div
        className="absolute inset-0 bg-gradient-radial-brand opacity-60"
        aria-hidden="true"
      />
      <CardContent className="relative flex flex-col items-center gap-6 py-10 md:flex-row md:justify-between md:gap-10">
        <div className="relative mx-auto h-64 w-64 shrink-0 md:mx-0">
          <svg viewBox="0 0 200 200" className="h-full w-full -rotate-90">
            <circle cx="100" cy="100" r={RING_RADIUS + 14} fill="none" stroke="var(--color-border)" strokeWidth="1" strokeDasharray="1 6" />
            <circle
              cx="100"
              cy="100"
              r={RING_RADIUS + 14}
              fill="none"
              stroke="var(--color-accent-2)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeDasharray={2 * Math.PI * (RING_RADIUS + 14)}
              strokeDashoffset={2 * Math.PI * (RING_RADIUS + 14) * (1 - (animated ? confidencePct : 0))}
              style={{ transition: "stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)" }}
            />
            <circle cx="100" cy="100" r={RING_RADIUS} fill="none" stroke="var(--color-surface-muted)" strokeWidth="10" />
            <circle
              cx="100"
              cy="100"
              r={RING_RADIUS}
              fill="none"
              stroke="var(--color-brand)"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={RING_CIRCUMFERENCE}
              strokeDashoffset={scoreOffset}
              style={{ transition: "stroke-dashoffset 1.4s cubic-bezier(0.16,1,0.3,1)" }}
            />
            {components.map((c, i) => {
              const angle = i * angleStep - Math.PI / 2;
              const cx = 100 + NODE_RADIUS * Math.cos(angle);
              const cy = 100 + NODE_RADIUS * Math.sin(angle);
              const isScored = c.status === "scored";
              return (
                <g key={c.component_type} className="rotate-90" style={{ transformOrigin: "100px 100px" }}>
                  <circle
                    cx={cx}
                    cy={cy}
                    r={isScored ? 5 + c.evidence_diversity : 4}
                    fill={scoreColor(c.score, isScored)}
                    stroke="var(--color-background)"
                    strokeWidth="2"
                    opacity={animated ? 1 : 0}
                    style={{ transition: `opacity 500ms ease ${300 + i * 90}ms` }}
                  >
                    <title>
                      {titleCase(c.component_type.replace("_readiness", ""))}
                      {isScored
                        ? ` — ${formatPercent(c.score)}, confidence ${formatPercent(c.confidence)}, ${c.evidence_count} evidence item(s)`
                        : " — insufficient evidence"}
                    </title>
                  </circle>
                </g>
              );
            })}
          </svg>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-metric-lg text-gradient-brand">{overallScore === null ? "—" : `${animatedScore}%`}</span>
            <span className="mt-1 text-xs font-medium uppercase tracking-widest text-muted">Overall readiness</span>
          </div>
        </div>

        <div className="flex flex-1 flex-col gap-4 text-center md:text-left">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-muted">Career Twin · Version {version}</p>
            <h1 className="mt-1 text-h1 text-foreground">Your evidence-backed self</h1>
          </div>
          <div className="flex flex-wrap justify-center gap-3 md:justify-start">
            <div className="rounded-[var(--radius-md)] border border-border bg-surface/70 px-4 py-2 backdrop-blur">
              <p className="text-[11px] text-muted">Confidence</p>
              <p className="text-lg font-bold text-foreground">{formatPercent(overallConfidence)}</p>
            </div>
            <div className="rounded-[var(--radius-md)] border border-border bg-surface/70 px-4 py-2 backdrop-blur">
              <p className="text-[11px] text-muted">Components scored</p>
              <p className="text-lg font-bold text-foreground">
                {components.filter((c) => c.status === "scored").length}/{components.length}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-muted md:justify-start">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ background: "var(--color-brand)" }} /> Score ring
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full border border-dashed" style={{ borderColor: "var(--color-accent-2)" }} /> Confidence ring
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ background: "var(--color-muted)" }} /> Insufficient evidence
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function CareerTwinBody() {
  const { data: snapshot, isLoading, isError, error, refetch } = useCareerTwin();
  const { data: history } = useCareerTwinHistory();
  const componentsRef = useStaggerReveal<HTMLDivElement>(snapshot?.version, { delay: 70 });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-56" />
        <Skeleton className="h-72" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (isError) {
    if (error instanceof ApiError && error.status === 404) {
      return (
        <EmptyState
          icon={Sparkles}
          title="No Career Twin snapshot yet"
          description="Complete onboarding to generate your first evidence-backed snapshot."
          action={
            <Button asChild>
              <Link href="/onboarding">Complete onboarding</Link>
            </Button>
          }
        />
      );
    }
    return <ErrorState message={error.message} onRetry={() => refetch()} titleAs="h1" />;
  }

  if (!snapshot) return null;

  return (
    <div className="space-y-6">
      {snapshot.milestones.length > 0 && <MilestoneBanner milestones={snapshot.milestones} />}

      <div className="animate-fade-up flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-2xl text-sm text-muted">{snapshot.change_summary}</p>
        <div className="flex items-center gap-2">
          <Badge>Formula {snapshot.formula_version}</Badge>
          <Button size="sm" variant="outline" asChild>
            <Link href={`/career-twin/proof/${snapshot.id}`}>
              <FileDown className="h-3.5 w-3.5" aria-hidden="true" /> Export proof
            </Link>
          </Button>
        </div>
      </div>

      <div className="animate-scale-in">
        <TwinCenterpiece
          overallScore={snapshot.overall_score}
          overallConfidence={snapshot.overall_confidence}
          version={snapshot.version}
          components={snapshot.components}
        />
      </div>

      <GithubProfilePanel />

      <Card className="animate-fade-up delay-2">
        <CardContent className="pt-5">
          <h2 className="mb-3 text-h3 text-foreground">Readiness components</h2>
          <ReadinessRadar components={snapshot.components} />
          <div ref={componentsRef} className="mt-4 grid gap-3 sm:grid-cols-2">
            {snapshot.components.map((component) => (
              <ComponentScoreCard key={component.component_type} component={component} />
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <MultiRolePanel />
        <TimeToTargetPanel />
      </div>

      <StrengthChainsPanel />

      <div className="animate-fade-up delay-3">
        <TwinTimeline updates={history ?? []} />
      </div>
    </div>
  );
}

export default function CareerTwinPage() {
  return (
    <Protected>
      <CareerTwinBody />
    </Protected>
  );
}
