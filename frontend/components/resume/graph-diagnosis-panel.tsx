"use client";

import { Network, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { formatPercent } from "@/lib/utils";
import type { ConceptInsightOut, ConceptStatus } from "@/types/api";

const STATUS_BADGE: Record<ConceptStatus, "positive" | "warning" | "danger" | "muted"> = {
  strong: "positive",
  developing: "warning",
  weak: "danger",
  unknown: "muted",
};

const STATUS_LABEL: Record<ConceptStatus, string> = {
  strong: "Strong depth",
  developing: "Developing",
  weak: "Shallow depth",
  unknown: "No depth evidence",
};

export function GraphDiagnosisPanel({ insights }: { insights: ConceptInsightOut[] }) {
  return (
    <Card className="animate-fade-up delay-4">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <Network className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">Resume vs. knowledge graph</CardTitle>
          <CardDescription>
            A keyword hit isn&apos;t depth. Each skill your resume claims, checked against real mastery evidence in
            the concept graph.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {insights.length === 0 ? (
          <EmptyState
            icon={Network}
            title="No graph-mapped skills yet"
            description="None of your resume's detected skills map to a knowledge-graph concept yet."
          />
        ) : (
          <div className="space-y-2.5">
            {insights.map((node) => (
              <div key={node.concept_slug} className="rounded-[var(--radius-md)] border border-border p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                      {node.concept_name}
                      {node.target_role_relevant && (
                        <Badge variant="outline" className="gap-1">
                          <Sparkles className="h-3 w-3" aria-hidden="true" /> Target role
                        </Badge>
                      )}
                    </p>
                    <p className="text-xs text-muted">{node.domain_name}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {node.mastery !== null && (
                      <span className="text-xs font-semibold tabular-nums text-foreground">
                        {formatPercent(node.mastery)}
                      </span>
                    )}
                    <Badge variant={STATUS_BADGE[node.status]}>{STATUS_LABEL[node.status]}</Badge>
                  </div>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-muted">{node.reasoning}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
