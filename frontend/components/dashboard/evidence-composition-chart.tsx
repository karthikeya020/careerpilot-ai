"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { PieChart as PieChartIcon } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { titleCase } from "@/lib/utils";
import type { ReadinessComponentOut } from "@/types/api";

const SLICE_COLORS = [
  "var(--color-brand)",
  "var(--color-accent-2)",
  "var(--color-positive)",
  "var(--color-warning)",
  "var(--color-accent)",
  "var(--color-danger)",
];

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { name: string; value: number }[] }) {
  if (!active || !payload?.length) return null;
  const slice = payload[0];
  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="font-medium text-foreground">{slice.name}</p>
      <p className="text-muted">{slice.value} evidence item{slice.value === 1 ? "" : "s"}</p>
    </div>
  );
}

export function EvidenceCompositionChart({ components }: { components: ReadinessComponentOut[] }) {
  const data = components
    .filter((c) => c.evidence_count > 0)
    .map((c) => ({ name: titleCase(c.component_type.replace("_readiness", "")), value: c.evidence_count }));

  const total = data.reduce((sum, d) => sum + d.value, 0);

  return (
    <Card className="animate-fade-up delay-2">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <PieChartIcon className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">Where your evidence comes from</CardTitle>
          <CardDescription>{total} real evidence item{total === 1 ? "" : "s"}, split across components.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <EmptyState
            icon={PieChartIcon}
            title="No evidence yet"
            description="Upload a resume or complete an assessment to start building evidence."
          />
        ) : (
          <div className="flex flex-col items-center gap-4 sm:flex-row">
            <div className="h-52 w-52 shrink-0" role="img" aria-label="Donut chart of evidence distribution across readiness components">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    dataKey="value"
                    nameKey="name"
                    innerRadius="62%"
                    outerRadius="90%"
                    paddingAngle={2}
                    animationDuration={900}
                    animationEasing="ease-out"
                  >
                    {data.map((_, i) => (
                      <Cell key={i} fill={SLICE_COLORS[i % SLICE_COLORS.length]} stroke="var(--color-background)" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex-1 space-y-2">
              {data.map((d, i) => (
                <div key={d.name} className="flex items-center justify-between gap-2 text-sm">
                  <span className="flex items-center gap-2 text-foreground">
                    <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: SLICE_COLORS[i % SLICE_COLORS.length] }} />
                    {d.name}
                  </span>
                  <span className="font-medium tabular-nums text-muted">
                    {d.value} · {Math.round((d.value / total) * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
