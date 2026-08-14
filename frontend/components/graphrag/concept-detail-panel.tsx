"use client";

import { ArrowDownRight, ArrowUpRight, Briefcase, ExternalLink, Sparkles, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { ConceptPractice } from "@/components/graphrag/concept-practice";
import { useConceptInsight } from "@/hooks/use-graphrag";
import { formatPercent } from "@/lib/utils";
import type { ConceptStatus } from "@/types/api";

const STATUS_META: Record<ConceptStatus, { label: string; badge: "positive" | "warning" | "danger" | "muted" }> = {
  strong: { label: "Strong", badge: "positive" },
  developing: { label: "Developing", badge: "warning" },
  weak: { label: "Needs work", badge: "danger" },
  unknown: { label: "Not assessed yet", badge: "muted" },
};

export function ConceptDetailPanel({
  slug,
  onClose,
  onDataChanged,
}: {
  slug: string;
  onClose: () => void;
  onDataChanged?: () => void;
}) {
  const { data: insight, isLoading, refetch } = useConceptInsight(slug);

  if (isLoading || !insight) {
    return (
      <Card className="animate-fade-up">
        <CardContent className="pt-6">
          <Skeleton className="h-40" />
        </CardContent>
      </Card>
    );
  }

  const meta = STATUS_META[insight.status];

  return (
    <Card variant="glow-brand" className="animate-fade-up relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-radial-brand opacity-20" aria-hidden="true" />
      <CardHeader className="relative flex-row items-start justify-between gap-2">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle as="h3" className="text-base">
              {insight.concept_name}
            </CardTitle>
            <Badge variant={meta.badge}>{meta.label}</Badge>
            {insight.target_role_relevant && (
              <Badge variant="outline" className="gap-1">
                <Briefcase className="h-3 w-3" aria-hidden="true" /> Target role
              </Badge>
            )}
          </div>
          <p className="mt-0.5 text-xs text-muted">{insight.domain_name}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-[var(--radius-sm)] p-1 text-muted transition-colors hover:bg-surface-muted hover:text-foreground"
          aria-label="Close concept detail"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </CardHeader>
      <CardContent className="relative space-y-4">
        {insight.mastery !== null && (
          <div>
            <div className="mb-1 flex items-center justify-between text-xs text-muted">
              <span>Mastery</span>
              <span className="font-medium text-foreground">
                {formatPercent(insight.mastery)} &middot; confidence {formatPercent(insight.confidence)}
              </span>
            </div>
            <Progress value={insight.mastery * 100} aria-label={`Mastery: ${formatPercent(insight.mastery)}`} />
          </div>
        )}

        <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3">
          <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-foreground">
            <Sparkles className="h-3.5 w-3.5 text-brand" aria-hidden="true" /> Why
          </p>
          <p className="text-xs leading-relaxed text-muted">{insight.reasoning}</p>
        </div>

        {(insight.depends_on.length > 0 || insight.blocks.length > 0) && (
          <div className="grid gap-3 sm:grid-cols-2">
            {insight.depends_on.length > 0 && (
              <div>
                <p className="mb-1 flex items-center gap-1 text-xs font-medium text-foreground">
                  <ArrowDownRight className="h-3.5 w-3.5 text-muted" aria-hidden="true" /> Depends on
                </p>
                <ul className="space-y-0.5 text-xs text-muted">
                  {insight.depends_on.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
            {insight.blocks.length > 0 && (
              <div>
                <p className="mb-1 flex items-center gap-1 text-xs font-medium text-foreground">
                  <ArrowUpRight className="h-3.5 w-3.5 text-muted" aria-hidden="true" /> Unlocks next
                </p>
                <ul className="space-y-0.5 text-xs text-muted">
                  {insight.blocks.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {insight.recommended_resource && (
          <a
            href={insight.recommended_resource.url ?? "#"}
            target="_blank"
            rel="noreferrer"
            className="card-premium card-premium-hover flex items-center justify-between gap-2 rounded-[var(--radius-md)] p-3 text-xs"
          >
            <span className="text-foreground">{insight.recommended_resource.title}</span>
            <ExternalLink className="h-3.5 w-3.5 shrink-0 text-muted" aria-hidden="true" />
          </a>
        )}

        {insight.practice_available ? (
          <ConceptPractice
            conceptSlug={slug}
            onCompleted={() => {
              refetch();
              onDataChanged?.();
            }}
          />
        ) : insight.questions_total > 0 ? (
          <p className="text-xs text-muted">You've answered every question we have for this concept -- nice work.</p>
        ) : null}
      </CardContent>
    </Card>
  );
}
