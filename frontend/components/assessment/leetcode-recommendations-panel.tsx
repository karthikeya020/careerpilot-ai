"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, Circle, ExternalLink, ListChecks, Sparkles, Target } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ExplainModal } from "@/components/assessment/explain-modal";
import { useLeetCodeRecommendations } from "@/hooks/use-assessment";
import { useLeetCodeCompletions, useMarkComplete, useUnmarkComplete } from "@/hooks/use-leetcode-practice";
import { cn } from "@/lib/utils";
import type {
  LeetCodeRecommendationSource,
  LeetCodeRecommendedProblemOut,
  WeaknessGroupOut,
} from "@/types/api";

const DIFFICULTY_BADGE: Record<"Easy" | "Medium" | "Hard", "positive" | "warning" | "danger"> = {
  Easy: "positive",
  Medium: "warning",
  Hard: "danger",
};

const SOURCE_LABEL: Record<LeetCodeRecommendationSource, string> = {
  assessment: "From your assessment results",
  profile: "Based on your profile",
  no_weaknesses: "Stretch goals",
};

type ExplainTarget = { slug: string; title: string; difficulty: string };

function ProblemRow({
  problem,
  group,
  completed,
  onExplain,
}: {
  problem: LeetCodeRecommendedProblemOut;
  group: WeaknessGroupOut;
  completed: boolean;
  onExplain: (t: ExplainTarget) => void;
}) {
  const mark = useMarkComplete();
  const unmark = useUnmarkComplete();
  const pending = mark.isPending || unmark.isPending;

  const toggle = () => {
    if (completed) {
      unmark.mutate(problem.slug);
    } else {
      mark.mutate({
        slug: problem.slug,
        title: problem.title,
        difficulty: problem.difficulty,
        concept_slug: group.concept_slug,
        domain_slug: group.domain_slug,
      });
    }
  };

  return (
    <li
      className={cn(
        "rounded-[var(--radius-md)] border px-3 py-2 text-xs transition-colors",
        completed ? "border-positive/40 bg-positive/5" : "border-border",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <a
          href={problem.url}
          target="_blank"
          rel="noreferrer"
          className="group flex min-w-0 items-center gap-1.5 truncate font-medium text-foreground hover:text-brand hover:underline"
        >
          {problem.title}
          <ExternalLink className="h-3 w-3 shrink-0 text-muted group-hover:text-brand" aria-hidden="true" />
        </a>
        <div className="flex shrink-0 items-center gap-2">
          <Badge variant={DIFFICULTY_BADGE[problem.difficulty]}>{problem.difficulty}</Badge>
          <button
            type="button"
            onClick={toggle}
            disabled={pending}
            className={cn(
              "flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-medium transition-colors disabled:opacity-60",
              completed
                ? "border-positive/50 bg-positive/10 text-positive"
                : "border-danger/50 bg-danger/10 text-danger hover:bg-danger/15",
            )}
            aria-pressed={completed}
          >
            {completed ? (
              <>
                <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> Completed
              </>
            ) : (
              <>
                <Circle className="h-3.5 w-3.5" aria-hidden="true" /> Mark complete
              </>
            )}
          </button>
        </div>
      </div>
      {completed && (
        <button
          type="button"
          onClick={() =>
            onExplain({ slug: problem.slug, title: problem.title, difficulty: problem.difficulty })
          }
          className="mt-1.5 flex items-center gap-1 text-[11px] font-medium text-brand hover:underline"
        >
          <Sparkles className="h-3 w-3" aria-hidden="true" /> Explain how you solved →
        </button>
      )}
    </li>
  );
}

function GroupCard({
  group,
  completedSlugs,
  onExplain,
}: {
  group: WeaknessGroupOut;
  completedSlugs: Set<string>;
  onExplain: (t: ExplainTarget) => void;
}) {
  const hasScore = group.accuracy !== null;
  return (
    <div className="rounded-[var(--radius-lg)] border border-border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-foreground">{group.concept_name}</span>
          <Badge variant="muted">{group.domain_name}</Badge>
        </div>
        {hasScore && (
          <Badge variant={group.accuracy! < 0.6 ? "danger" : "warning"} className="tabular-nums">
            {Math.round(group.accuracy! * 100)}% over {group.answered} answered
          </Badge>
        )}
      </div>
      {group.focus && <p className="mt-1.5 text-xs text-muted">{group.focus}</p>}
      <ul className="mt-3 space-y-1.5">
        {group.problems.map((problem) => (
          <ProblemRow
            key={problem.slug}
            problem={problem}
            group={group}
            completed={completedSlugs.has(problem.slug)}
            onExplain={onExplain}
          />
        ))}
      </ul>
    </div>
  );
}

export function LeetCodeRecommendationsPanel() {
  const { data, isLoading, isError, error, refetch } = useLeetCodeRecommendations();
  const { data: completions } = useLeetCodeCompletions();
  const [explain, setExplain] = useState<ExplainTarget | null>(null);

  const completedSlugs = useMemo(
    () => new Set((completions ?? []).map((c) => c.slug)),
    [completions],
  );

  return (
    <Card className="animate-fade-up">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <Target className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">LeetCode practice plan</CardTitle>
          <CardDescription>
            Problems mapped to the concepts your assessments show you are weakest on. Mark one complete, then explain
            how you solved it for a code review.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-48" />
        ) : isError ? (
          <ErrorState
            message={error instanceof Error ? error.message : "Couldn't load your practice plan."}
            onRetry={() => refetch()}
          />
        ) : !data || data.groups.length === 0 ? (
          <EmptyState
            icon={ListChecks}
            title="No recommendations yet"
            description="Answer a few assessment questions and we'll map LeetCode problems to whatever you struggle with."
          />
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant={data.source === "assessment" ? "danger" : "muted"}>{SOURCE_LABEL[data.source]}</Badge>
              <p className="text-xs text-muted">{data.summary}</p>
            </div>
            <div className="space-y-3">
              {data.groups.map((group) => (
                <GroupCard
                  key={group.concept_slug ?? group.domain_slug}
                  group={group}
                  completedSlugs={completedSlugs}
                  onExplain={setExplain}
                />
              ))}
            </div>
            <p className="text-[10px] text-muted">{data.disclaimer}</p>
          </div>
        )}
      </CardContent>

      {explain && (
        <ExplainModal
          slug={explain.slug}
          title={explain.title}
          difficulty={explain.difficulty}
          onClose={() => setExplain(null)}
        />
      )}
    </Card>
  );
}
