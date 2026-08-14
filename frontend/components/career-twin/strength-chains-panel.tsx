"use client";

import { Trophy } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useStudentGraphOverview } from "@/hooks/use-graphrag";
import { formatPercent } from "@/lib/utils";

export function StrengthChainsPanel() {
  const { data, isLoading } = useStudentGraphOverview();
  const strengths = data?.strengths ?? [];

  return (
    <Card className="animate-fade-up delay-4">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-positive/15">
          <Trophy className="h-4 w-4 text-positive" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">What to lean into</CardTitle>
          <CardDescription>
            Your strongest verified concept chains -- what to emphasize in interviews and on your resume, not just
            what to fix.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-32" />
        ) : strengths.length === 0 ? (
          <EmptyState
            icon={Trophy}
            title="No strong concepts yet"
            description="Once you have solid evidence for a concept, it'll show up here as something to lean into."
          />
        ) : (
          <div className="space-y-2.5">
            {strengths.map((node) => (
              <div key={node.concept_slug} className="rounded-[var(--radius-md)] border border-positive/30 bg-positive/5 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-foreground">{node.concept_name}</p>
                  <div className="flex items-center gap-2">
                    {node.mastery !== null && (
                      <span className="text-xs font-semibold tabular-nums text-foreground">{formatPercent(node.mastery)}</span>
                    )}
                    {node.target_role_relevant && <Badge variant="positive">Target role</Badge>}
                  </div>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted">{node.reasoning}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
