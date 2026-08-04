"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";
import { ComponentScoreCard } from "@/components/dashboard/component-score-card";
import { ReadinessRadar } from "@/components/dashboard/readiness-radar";
import { TwinTimeline } from "@/components/dashboard/twin-timeline";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useCareerTwin, useCareerTwinHistory } from "@/hooks/use-career-twin";
import { ApiError } from "@/lib/api-client";
import { formatDateTime, formatPercent } from "@/lib/utils";

function CareerTwinBody() {
  const { data: snapshot, isLoading, isError, error, refetch } = useCareerTwin();
  const { data: history } = useCareerTwinHistory();

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-56" />
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
    return <ErrorState message={error.message} onRetry={() => refetch()} />;
  }

  if (!snapshot) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Career Twin</h1>
          <p className="mt-1 text-sm text-muted">{snapshot.change_summary}</p>
        </div>
        <Badge>Formula {snapshot.formula_version}</Badge>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Overall score</p>
            <p className="text-3xl font-semibold text-foreground">{formatPercent(snapshot.overall_score)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Confidence</p>
            <p className="text-3xl font-semibold text-foreground">{formatPercent(snapshot.overall_confidence)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <p className="text-xs text-muted">Last updated</p>
            <p className="text-lg font-semibold text-foreground">{formatDateTime(snapshot.created_at)}</p>
            <p className="text-xs text-muted">Version {snapshot.version}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="pt-5">
          <h2 className="mb-2 text-sm font-semibold text-foreground">Readiness components</h2>
          <ReadinessRadar components={snapshot.components} />
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {snapshot.components.map((component) => (
              <ComponentScoreCard key={component.component_type} component={component} />
            ))}
          </div>
        </CardContent>
      </Card>

      <TwinTimeline updates={history ?? []} />
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
