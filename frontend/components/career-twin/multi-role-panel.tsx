"use client";

import { Layers } from "lucide-react";
import { AnimatedBar } from "@/components/ui/animated-bar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMultiRoleAlignment } from "@/hooks/use-career-twin";
import { useStaggerReveal } from "@/hooks/use-stagger-reveal";
import { formatPercent } from "@/lib/utils";

function alignmentColor(alignment: number) {
  if (alignment >= 0.7) return "var(--color-positive)";
  if (alignment >= 0.4) return "var(--color-warning)";
  return "var(--color-danger)";
}

export function MultiRolePanel() {
  const { data, isLoading } = useMultiRoleAlignment();
  const listRef = useStaggerReveal<HTMLDivElement>(data?.length, { delay: 80 });

  return (
    <Card className="animate-fade-up delay-2">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <Layers className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">How you align across roles</CardTitle>
          <CardDescription>The same evidence, scored against several common target roles at once.</CardDescription>
        </div>
      </CardHeader>
      <CardContent ref={listRef} className="space-y-3">
        {isLoading ? (
          <Skeleton className="h-40" />
        ) : (
          data?.map((role) => (
            <div key={role.role_title}>
              <div className="mb-1 flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-foreground">{role.role_title}</p>
                <span className="text-sm font-bold tabular-nums text-foreground">{formatPercent(role.alignment)}</span>
              </div>
              <AnimatedBar percent={role.alignment} color={alignmentColor(role.alignment)} />
              {role.missing_skills.length > 0 && (
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {role.missing_skills.slice(0, 4).map((s) => (
                    <Badge key={s} variant="muted" className="text-[10px]">
                      Missing: {s}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
