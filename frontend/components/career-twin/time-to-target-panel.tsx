"use client";

import { Hourglass } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTimeToTarget } from "@/hooks/use-career-twin";
import { titleCase } from "@/lib/utils";
import type { ProjectionStatus } from "@/types/api";

const STATUS_BADGE: Record<ProjectionStatus, { label: string; variant: "positive" | "warning" | "muted" | "danger" }> = {
  already_at_target: { label: "At target", variant: "positive" },
  projected: { label: "On track", variant: "warning" },
  not_improving: { label: "No positive trend yet", variant: "danger" },
  insufficient_history: { label: "Not enough history", variant: "muted" },
};

export function TimeToTargetPanel() {
  const { data, isLoading } = useTimeToTarget();
  const projectable = data?.filter((p) => p.status === "projected") ?? [];

  return (
    <Card className="animate-fade-up delay-3">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <Hourglass className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">Time to 70% readiness</CardTitle>
          <CardDescription>
            Projected from your own historical rate of change -- a heuristic estimate, never a guarantee.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {isLoading ? (
          <Skeleton className="h-40" />
        ) : (
          data?.map((p) => {
            const status = STATUS_BADGE[p.status];
            const label = titleCase(p.component_type.replace("_readiness", ""));
            return (
              <div key={p.component_type} className="flex items-center justify-between gap-2 rounded-[var(--radius-md)] border border-border p-3">
                <div>
                  <p className="text-sm font-medium text-foreground">{label}</p>
                  {p.status === "projected" && p.weeks_to_target !== null ? (
                    <p className="text-xs text-muted">
                      ~{p.weeks_to_target}w (range {p.weeks_to_target_low}-{p.weeks_to_target_high}w)
                    </p>
                  ) : (
                    <p className="text-xs text-muted">{p.note}</p>
                  )}
                </div>
                <Badge variant={status.variant}>{status.label}</Badge>
              </div>
            );
          })
        )}
        {!isLoading && projectable.length === 0 && (
          <p className="text-xs text-muted">
            No components have enough historical snapshots yet to project a rate -- check back after a few more
            Career Twin updates.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
