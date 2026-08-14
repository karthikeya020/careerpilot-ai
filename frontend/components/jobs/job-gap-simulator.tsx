"use client";

import { useState } from "react";
import { Clock, Target } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useJobGapPlan } from "@/hooks/use-job-catalog";
import { cn, formatPercent } from "@/lib/utils";

const HOUR_OPTIONS = [5, 10, 15, 20];

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-2.5 text-center">
      <p className="text-sm font-bold text-foreground">{value}</p>
      <p className="text-[10px] text-muted">{label}</p>
    </div>
  );
}

export function JobGapSimulator({ listingId }: { listingId: string }) {
  const [weeklyHours, setWeeklyHours] = useState(10);
  const { data: plan, isLoading } = useJobGapPlan(listingId, weeklyHours);

  if (isLoading || !plan) return <Skeleton className="h-48" />;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
          <Target className="h-3.5 w-3.5 text-brand" aria-hidden="true" /> Job Gap Simulator
        </p>
        <div className="flex items-center gap-1">
          <span className="text-[10px] text-muted">Hours/week you can commit:</span>
          {HOUR_OPTIONS.map((h) => (
            <button
              key={h}
              type="button"
              onClick={() => setWeeklyHours(h)}
              className={cn(
                "rounded-full px-2 py-0.5 text-[10px] font-medium transition-colors",
                weeklyHours === h ? "bg-brand text-brand-foreground" : "bg-surface-muted text-muted hover:text-foreground",
              )}
            >
              {h}h
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <StatTile label="Readiness today" value={formatPercent(plan.readiness)} />
        <StatTile label="Hours needed" value={`${Math.round(plan.total_estimated_hours)}h`} />
        <StatTile
          label="Time to ready"
          value={plan.estimated_weeks_to_ready > 0 ? `~${plan.estimated_weeks_to_ready}w` : "You're ready!"}
        />
      </div>

      {plan.items.length > 0 ? (
        <div className="space-y-1.5">
          <p className="text-xs font-medium text-foreground">What to work on, in priority order</p>
          {plan.items.map((item, i) => (
            <div key={i} className="flex flex-wrap items-center justify-between gap-2 rounded-[var(--radius-md)] border border-border p-2.5 text-xs">
              <div className="flex items-center gap-2">
                <Badge variant={item.status === "missing" ? "danger" : "warning"}>
                  {item.status === "missing" ? "Missing" : "Partial"}
                </Badge>
                <span className="font-medium text-foreground">{item.skill_name}</span>
              </div>
              <div className="flex items-center gap-2 text-muted">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" aria-hidden="true" /> {item.estimated_hours}h
                </span>
                {item.recommended_resource && (
                  <a
                    href={item.recommended_resource.url ?? "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand hover:underline"
                  >
                    {item.recommended_resource.title}
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs font-medium text-positive">Every required skill already has strong evidence -- keep it up!</p>
      )}

      <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-2.5">
        <ul className="list-inside list-disc space-y-1 text-[11px] text-muted">
          {plan.assumptions.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
