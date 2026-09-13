"use client";

import { useMemo, useState } from "react";
import { ExternalLink, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ExplainModal } from "@/components/assessment/explain-modal";
import { useLeetCodeCompletions } from "@/hooks/use-leetcode-practice";
import { formatDate } from "@/lib/utils";
import type { LeetCodeCompletionOut } from "@/types/api";

const DIFF_BADGE: Record<string, "positive" | "warning" | "danger" | "muted"> = {
  Easy: "positive",
  Medium: "warning",
  Hard: "danger",
};

const WEEKS = 26;

function cellShade(count: number, max: number): number {
  if (count <= 0 || max <= 0) return 0.08;
  const ratio = count / max;
  if (ratio > 0.75) return 1;
  if (ratio > 0.5) return 0.72;
  if (ratio > 0.25) return 0.48;
  return 0.3;
}

function Heatmap({ completions }: { completions: LeetCodeCompletionOut[] }) {
  const byDay = useMemo(() => {
    const m = new Map<string, number>();
    for (const c of completions) {
      const key = c.completed_at.slice(0, 10);
      m.set(key, (m.get(key) ?? 0) + 1);
    }
    return m;
  }, [completions]);

  const today = new Date();
  const cells: { date: string; count: number }[] = [];
  for (let i = WEEKS * 7 - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    cells.push({ date: key, count: byDay.get(key) ?? 0 });
  }
  const max = cells.reduce((m, c) => Math.max(m, c.count), 0);

  return (
    <div>
      <div
        className="grid grid-flow-col grid-rows-7 gap-1"
        role="img"
        aria-label={`LeetCode problems completed over the last ${WEEKS} weeks`}
      >
        {cells.map((cell) => (
          <span
            key={cell.date}
            title={`${cell.date}: ${cell.count} completed`}
            className="h-2.5 w-2.5 rounded-sm"
            style={{
              background: `color-mix(in srgb, var(--color-brand) ${cellShade(cell.count, max) * 100}%, var(--color-surface-muted))`,
            }}
          />
        ))}
      </div>
      <p className="mt-2 text-[10px] text-muted">Last {WEEKS} weeks — each square is a day you marked a problem complete.</p>
    </div>
  );
}

const DIFF_COLOR: Record<string, string> = {
  Easy: "var(--color-positive)",
  Medium: "var(--color-warning)",
  Hard: "var(--color-danger)",
};

export function PracticeActivity() {
  const { data, isLoading } = useLeetCodeCompletions();
  const [explain, setExplain] = useState<{ slug: string; title: string; difficulty: string } | null>(null);

  const completions = useMemo(() => data ?? [], [data]);
  const { thisWeek, byDiff } = useMemo(() => {
    const weekAgo = new Date().getTime() - 7 * 24 * 60 * 60 * 1000;
    const counts: Record<string, number> = {};
    let week = 0;
    for (const c of completions) {
      counts[c.difficulty] = (counts[c.difficulty] ?? 0) + 1;
      if (new Date(c.completed_at).getTime() >= weekAgo) week += 1;
    }
    return { thisWeek: week, byDiff: counts };
  }, [completions]);

  if (isLoading) return <Skeleton className="h-40" />;

  if (completions.length === 0) {
    return (
      <EmptyState
        icon={Sparkles}
        title="No LeetCode problems marked complete yet"
        description="Mark problems complete in your LeetCode practice plan below and they'll show up here."
      />
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-5">
        <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3">
          <p className="text-[11px] text-muted">Total solved</p>
          <p className="text-xl font-bold tabular-nums text-foreground">{completions.length}</p>
        </div>
        <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3">
          <p className="text-[11px] text-muted">This week</p>
          <p className="text-xl font-bold tabular-nums text-foreground">{thisWeek}</p>
        </div>
        {(["Easy", "Medium", "Hard"] as const).map((d) => (
          <div key={d} className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3">
            <p className="text-[11px]" style={{ color: DIFF_COLOR[d] }}>
              {d}
            </p>
            <p className="text-xl font-bold tabular-nums text-foreground">{byDiff[d] ?? 0}</p>
          </div>
        ))}
      </div>

      <Heatmap completions={completions} />

      <div>
        <p className="mb-2 text-xs font-semibold text-foreground">Completed problems</p>
        <ul className="space-y-1.5">
          {completions.map((c) => (
            <li
              key={c.slug}
              className="flex items-center justify-between gap-2 rounded-[var(--radius-md)] border border-border px-3 py-2 text-xs"
            >
              <a
                href={`https://leetcode.com/problems/${c.slug}/`}
                target="_blank"
                rel="noreferrer"
                className="group flex min-w-0 items-center gap-1.5 truncate font-medium text-foreground hover:text-brand hover:underline"
              >
                {c.title}
                <ExternalLink className="h-3 w-3 shrink-0 text-muted group-hover:text-brand" aria-hidden="true" />
              </a>
              <div className="flex shrink-0 items-center gap-2">
                <span className="text-[10px] text-muted">{formatDate(c.completed_at)}</span>
                {c.difficulty && <Badge variant={DIFF_BADGE[c.difficulty] ?? "muted"}>{c.difficulty}</Badge>}
                <button
                  type="button"
                  onClick={() => setExplain({ slug: c.slug, title: c.title, difficulty: c.difficulty })}
                  className="flex items-center gap-1 rounded-full border border-border px-2 py-1 text-[11px] font-medium text-brand transition-colors hover:bg-brand-soft/40"
                >
                  <Sparkles className="h-3 w-3" aria-hidden="true" />
                  {c.has_analysis ? "Review" : "Explain"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {explain && (
        <ExplainModal
          slug={explain.slug}
          title={explain.title}
          difficulty={explain.difficulty}
          onClose={() => setExplain(null)}
        />
      )}
    </div>
  );
}
