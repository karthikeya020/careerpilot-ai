"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TrendingUp } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { useCareerTwinHistory } from "@/hooks/use-career-twin";
import { Skeleton } from "@/components/ui/skeleton";

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: { version: number; score: number } }[] }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="font-medium text-foreground">Version {point.version}</p>
      <p className="text-muted">Overall readiness {point.score}%</p>
    </div>
  );
}

export function ReadinessTrendChart() {
  const { data: history, isLoading } = useCareerTwinHistory();

  const points = (history ?? [])
    .filter((s) => s.overall_score !== null)
    .slice()
    .reverse()
    .map((s) => ({ version: s.version, score: Math.round((s.overall_score ?? 0) * 100) }));

  return (
    <Card className="animate-fade-up delay-1">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <TrendingUp className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">Readiness over time</CardTitle>
          <CardDescription>Your overall Career Twin score across every real snapshot on file.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-56" />
        ) : points.length < 2 ? (
          <EmptyState
            icon={TrendingUp}
            title="Not enough history yet"
            description="Your trend line appears once your Career Twin has updated a couple of times."
          />
        ) : (
          <div className="h-56 w-full" role="img" aria-label="Line chart of overall readiness across Career Twin versions">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={points} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-brand)" stopOpacity={0.4} />
                    <stop offset="100%" stopColor="var(--color-brand)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="var(--color-border)" strokeDasharray="3 3" />
                <XAxis
                  dataKey="version"
                  tickFormatter={(v) => `v${v}`}
                  tick={{ fill: "var(--color-muted)", fontSize: 11 }}
                  axisLine={{ stroke: "var(--color-border)" }}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                  tick={{ fill: "var(--color-muted)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={44}
                />
                <Tooltip content={<ChartTooltip />} />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="var(--color-brand)"
                  strokeWidth={2.5}
                  fill="url(#trendFill)"
                  animationDuration={900}
                  animationEasing="ease-out"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
