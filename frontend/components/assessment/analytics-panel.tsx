"use client";

import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Flame, Target, Trophy, Zap } from "lucide-react";
import type { AssessmentAnalyticsOut, DifficultyBand } from "@/types/api";
import { formatPercent, titleCase } from "@/lib/utils";

const BAND_COLOR: Record<DifficultyBand, string> = {
  easy: "var(--color-positive)",
  medium: "var(--color-warning)",
  hard: "var(--color-danger)",
};

function StatTile({ icon: Icon, label, value, accent }: { icon: typeof Flame; label: string; value: string; accent?: string }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3">
      <div className="mb-1 flex items-center gap-1.5 text-[11px] text-muted">
        <Icon className="h-3.5 w-3.5" style={accent ? { color: accent } : undefined} aria-hidden="true" />
        {label}
      </div>
      <p className="text-xl font-bold tabular-nums text-foreground">{value}</p>
    </div>
  );
}

export function AssessmentAnalyticsPanel({ analytics }: { analytics: AssessmentAnalyticsOut }) {
  const domainData = analytics.accuracy_by_domain.map((d) => ({
    name: d.domain.length > 14 ? `${d.domain.slice(0, 13)}…` : d.domain,
    accuracy: Math.round(d.accuracy * 100),
    answered: d.answered,
  }));
  const trendData = analytics.score_trend.map((p) => ({
    date: p.date.slice(5),
    score: Math.round(p.avg_score * 100),
  }));

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        <StatTile icon={Target} label="Answered" value={String(analytics.total_answered)} />
        <StatTile
          icon={Trophy}
          label="Accuracy"
          value={analytics.overall_accuracy !== null ? formatPercent(analytics.overall_accuracy) : "—"}
          accent="var(--color-positive)"
        />
        <StatTile icon={Flame} label="Current streak" value={`${analytics.current_streak_days}d`} accent="var(--color-warning)" />
        <StatTile icon={Zap} label="Longest streak" value={`${analytics.longest_streak_days}d`} accent="var(--color-brand)" />
      </div>

      {analytics.accuracy_by_domain.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-foreground">Accuracy by topic</p>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={domainData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "var(--color-muted)", fontSize: 10 }} interval={0} angle={-25} textAnchor="end" height={40} />
                <YAxis tick={{ fill: "var(--color-muted)", fontSize: 10 }} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12 }}
                  formatter={(value) => [`${value}%`, "Accuracy"]}
                />
                <Bar dataKey="accuracy" fill="var(--color-brand)" radius={[4, 4, 0, 0]} animationDuration={700} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {analytics.accuracy_by_difficulty.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-foreground">Accuracy by difficulty</p>
          <div className="grid grid-cols-3 gap-2">
            {analytics.accuracy_by_difficulty.map((d) => (
              <div key={d.band} className="rounded-[var(--radius-md)] border border-border p-2.5 text-center">
                <p className="text-[11px] font-medium" style={{ color: BAND_COLOR[d.band] }}>
                  {titleCase(d.band)}
                </p>
                <p className="text-lg font-bold text-foreground">{formatPercent(d.accuracy)}</p>
                <p className="text-[10px] text-muted">{d.answered} answered</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {trendData.length > 1 && (
        <div>
          <p className="mb-2 text-xs font-medium text-foreground">Score trend</p>
          <div className="h-40 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: "var(--color-muted)", fontSize: 10 }} />
                <YAxis tick={{ fill: "var(--color-muted)", fontSize: 10 }} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                <Tooltip
                  contentStyle={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12 }}
                  formatter={(value) => [`${value}%`, "Avg score"]}
                />
                <Line type="monotone" dataKey="score" stroke="var(--color-brand)" strokeWidth={2.5} dot={false} animationDuration={700} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
