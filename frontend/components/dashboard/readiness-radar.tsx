"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import type { ReadinessComponentOut } from "@/types/api";
import { titleCase } from "@/lib/utils";

interface ReadinessRadarProps {
  components: ReadinessComponentOut[];
}

export function ReadinessRadar({ components }: ReadinessRadarProps) {
  const data = components.map((component) => ({
    label: titleCase(component.component_type.replace("_readiness", "")),
    score: component.status === "scored" ? Math.round((component.score ?? 0) * 100) : 0,
  }));

  return (
    <div className="h-72 w-full" role="img" aria-label="Radar chart of six readiness components">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="72%">
          <defs>
            <linearGradient id="readinessFill" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="var(--color-brand)" stopOpacity={0.55} />
              <stop offset="100%" stopColor="var(--color-accent-2)" stopOpacity={0.25} />
            </linearGradient>
          </defs>
          <PolarGrid stroke="var(--color-border)" />
          <PolarAngleAxis
            dataKey="label"
            tick={{ fill: "var(--color-muted)", fontSize: 11, fontWeight: 500 }}
          />
          <Radar
            name="Readiness"
            dataKey="score"
            stroke="var(--color-brand)"
            strokeWidth={2}
            fill="url(#readinessFill)"
            fillOpacity={1}
            animationDuration={900}
            animationEasing="ease-out"
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
