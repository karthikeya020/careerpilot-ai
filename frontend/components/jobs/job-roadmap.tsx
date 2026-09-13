"use client";

import Link from "next/link";
import { AlertTriangle, ArrowUpRight, CheckCircle2, Flag, Skull, Target } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useJobRoadmap } from "@/hooks/use-live-jobs";
import { cn } from "@/lib/utils";
import type { JobRoadmapOut, RoadmapAction, RoadmapDifficulty } from "@/types/api";

const DIFF: Record<RoadmapDifficulty, { label: string; badge: "danger" | "warning" | "positive"; icon: typeof Skull }> = {
  brutal: { label: "Brutal", badge: "danger", icon: Skull },
  hard: { label: "Hard", badge: "warning", icon: AlertTriangle },
  achievable: { label: "Achievable", badge: "positive", icon: Target },
};

function ActionItem({ action }: { action: RoadmapAction }) {
  const isInternal = action.link?.startsWith("/");
  return (
    <li className="flex gap-2 text-xs leading-relaxed text-muted">
      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand" aria-hidden="true" />
      <span>
        {action.text}
        {action.link &&
          (isInternal ? (
            <Link href={action.link} className="ml-1 font-medium text-brand hover:underline">
              open →
            </Link>
          ) : (
            <a
              href={action.link}
              target="_blank"
              rel="noreferrer"
              className="ml-1 inline-flex items-center font-medium text-brand hover:underline"
            >
              link <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
            </a>
          ))}
      </span>
    </li>
  );
}

export function RoadmapView({ roadmap }: { roadmap: JobRoadmapOut }) {
  const diff = DIFF[roadmap.difficulty];
  const DiffIcon = diff.icon;
  return (
    <div className="space-y-4">
      <div className="rounded-[var(--radius-lg)] border border-border bg-surface-muted p-4">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Badge variant={diff.badge} className="gap-1">
            <DiffIcon className="h-3 w-3" aria-hidden="true" /> {diff.label}
          </Badge>
          <Badge variant="muted">~{roadmap.total_weeks} weeks</Badge>
          <Badge variant="muted">{roadmap.phases.length} phases</Badge>
        </div>
        <p className="text-xs font-semibold text-foreground">The bar you&apos;re clearing</p>
        <p className="mt-1 text-xs leading-relaxed text-danger">{roadmap.bar}</p>
        <p className="mt-2 text-xs leading-relaxed text-muted">{roadmap.summary}</p>
      </div>

      <ol className="relative space-y-4 border-l border-border pl-5">
        {roadmap.phases.map((phase, i) => (
          <li key={phase.title} className="relative">
            <span
              className={cn(
                "absolute -left-[26px] flex h-5 w-5 items-center justify-center rounded-full border-2 border-surface text-[10px] font-bold text-white",
                "bg-gradient-brand",
              )}
              aria-hidden="true"
            >
              {i + 1}
            </span>
            <div className="rounded-[var(--radius-md)] border border-border p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-semibold text-foreground">{phase.title}</p>
                <Badge variant="outline" className="text-[10px]">
                  {phase.weeks}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-muted">{phase.why}</p>
              <ul className="mt-2 space-y-1.5">
                {phase.actions.map((a, j) => (
                  <ActionItem key={j} action={a} />
                ))}
              </ul>
              <p className="mt-2 flex items-start gap-1.5 rounded-[var(--radius-sm)] bg-positive/10 px-2 py-1.5 text-[11px] text-foreground">
                <Flag className="mt-0.5 h-3 w-3 shrink-0 text-positive" aria-hidden="true" />
                <span>
                  <span className="font-semibold">Done when:</span> {phase.milestone}
                </span>
              </p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}

export function JobRoadmap(props: {
  listingId?: string | null;
  company?: string;
  title?: string;
  sector?: string;
  seniority?: string | null;
  skills?: string[];
}) {
  const { data, isLoading, isError, error, refetch } = useJobRoadmap(props);

  if (isLoading) return <Skeleton className="h-64" />;
  if (isError || !data)
    return (
      <ErrorState
        message={error instanceof Error ? error.message : "Couldn't build a roadmap for this role."}
        onRetry={() => refetch()}
      />
    );
  return <RoadmapView roadmap={data} />;
}

export function RoadmapUnlockedNote() {
  return (
    <p className="flex items-center gap-1.5 text-xs font-medium text-positive">
      <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> Roadmap unlocked below — now go earn it.
    </p>
  );
}
