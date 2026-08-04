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
    <div className="h-64 w-full" role="img" aria-label="Radar chart of six readiness components">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} outerRadius="75%">
          <PolarGrid stroke="var(--color-border)" />
          <PolarAngleAxis
            dataKey="label"
            tick={{ fill: "var(--color-muted)", fontSize: 11 }}
          />
          <Radar
            name="Readiness"
            dataKey="score"
            stroke="var(--color-brand)"
            fill="var(--color-brand)"
            fillOpacity={0.35}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
