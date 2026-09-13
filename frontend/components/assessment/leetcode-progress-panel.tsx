"use client";

import Link from "next/link";
import { Award, CalendarCheck, Code2, Flame, Zap } from "lucide-react";
import { AnimatedBar } from "@/components/ui/animated-bar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useLeetCodeProfile } from "@/hooks/use-leetcode-profile";
import { useStaggerReveal } from "@/hooks/use-stagger-reveal";
import { formatDate } from "@/lib/utils";
import type { LeetCodeActivityDayOut, LeetCodeContestOut, LeetCodeProfileOut } from "@/types/api";

const DIFFICULTY_ROWS = [
  { key: "easy", label: "Easy", color: "var(--color-positive)" },
  { key: "medium", label: "Medium", color: "var(--color-warning)" },
  { key: "hard", label: "Hard", color: "var(--color-danger)" },
] as const;

// Sequential single-hue scale (brand hue via opacity) for the activity
// heatmap -- a magnitude encoding, never a categorical rainbow. Mirrors the
// GitHub profile panel so the two widgets read as one system.
function activityOpacity(count: number, max: number): number {
  if (count <= 0 || max <= 0) return 0.08;
  const ratio = count / max;
  if (ratio > 0.75) return 1;
  if (ratio > 0.5) return 0.75;
  if (ratio > 0.25) return 0.5;
  return 0.3;
}

function ActivityHeatmap({ days }: { days: LeetCodeActivityDayOut[] }) {
  const byDate = new Map(days.map((d) => [d.date, d.count]));
  const max = days.reduce((m, d) => Math.max(m, d.count), 0);
  const today = new Date();
  const cells: { date: string; count: number }[] = [];
  for (let i = 89; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    cells.push({ date: key, count: byDate.get(key) ?? 0 });
  }
  const gridRef = useStaggerReveal<HTMLDivElement>(cells.length, { delay: 4, y: 0 });

  return (
    <div>
      <div
        ref={gridRef}
        className="grid grid-flow-col grid-rows-7 gap-1"
        role="img"
        aria-label="LeetCode submissions over the last 90 days"
      >
        {cells.map((cell) => (
          <span
            key={cell.date}
            title={`${cell.date}: ${cell.count} submission${cell.count === 1 ? "" : "s"}`}
            className="h-2.5 w-2.5 rounded-sm"
            style={{
              background: `color-mix(in srgb, var(--color-brand) ${activityOpacity(cell.count, max) * 100}%, var(--color-surface-muted))`,
            }}
          />
        ))}
      </div>
      <p className="mt-2 text-[10px] text-muted">Last ~90 days of LeetCode submissions.</p>
    </div>
  );
}

function StatTile({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: typeof Flame;
  label: string;
  value: string;
  accent?: string;
}) {
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

function ContestSection({ data }: { data: LeetCodeProfileOut }) {
  if (data.contests_attended <= 0) {
    return (
      <div>
        <p className="mb-2 text-xs font-semibold text-foreground">Contests</p>
        <p className="text-xs text-muted">No rated contests attended yet.</p>
      </div>
    );
  }
  return (
    <div>
      <p className="mb-2 text-xs font-semibold text-foreground">Contests</p>
      <div className="grid grid-cols-2 gap-2 text-center sm:grid-cols-4">
        <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-2">
          <p className="text-sm font-semibold text-foreground">{data.contests_attended}</p>
          <p className="text-[10px] text-muted">Attended</p>
        </div>
        <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-2">
          <p className="text-sm font-semibold text-foreground">{data.contest_rating ?? "—"}</p>
          <p className="text-[10px] text-muted">Rating</p>
        </div>
        <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-2">
          <p className="text-sm font-semibold text-foreground">
            {data.contest_global_ranking ? `#${data.contest_global_ranking.toLocaleString()}` : "—"}
          </p>
          <p className="text-[10px] text-muted">Global rank</p>
        </div>
        <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-2">
          <p className="text-sm font-semibold text-foreground">
            {data.contest_top_percentage != null ? `Top ${data.contest_top_percentage.toFixed(1)}%` : "—"}
          </p>
          <p className="text-[10px] text-muted">Percentile</p>
        </div>
      </div>
      {data.recent_contests.length > 0 && (
        <ul className="mt-2.5 space-y-1.5">
          {data.recent_contests.map((contest: LeetCodeContestOut) => (
            <li key={`${contest.title}-${contest.start_time ?? ""}`} className="flex items-center justify-between gap-2 text-xs">
              <span className="truncate text-foreground">{contest.title}</span>
              <span className="flex shrink-0 items-center gap-2 text-muted">
                {contest.problems_solved != null && contest.total_problems != null && (
                  <span>
                    {contest.problems_solved}/{contest.total_problems} solved
                  </span>
                )}
                {contest.ranking != null && contest.ranking > 0 && (
                  <Badge variant="muted" className="text-[10px]">
                    rank {contest.ranking.toLocaleString()}
                  </Badge>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function LanguageStats({ data }: { data: LeetCodeProfileOut }) {
  if (data.language_stats.length === 0) return null;
  const max = data.language_stats.reduce((m, l) => Math.max(m, l.problems_solved), 0);
  return (
    <div>
      <p className="mb-2 text-xs font-semibold text-foreground">Languages used</p>
      <div className="space-y-2">
        {data.language_stats.map((lang) => (
          <div key={lang.language}>
            <div className="mb-1 flex items-center justify-between gap-2 text-xs">
              <span className="font-medium text-foreground">{lang.language}</span>
              <span className="text-muted">
                {lang.problems_solved} problem{lang.problems_solved === 1 ? "" : "s"}
              </span>
            </div>
            <AnimatedBar percent={max > 0 ? lang.problems_solved / max : 0} className="bg-brand" />
          </div>
        ))}
      </div>
      <p className="text-[10px] text-muted">Distinct problems solved per language (LeetCode&apos;s own count).</p>
    </div>
  );
}

export function LeetCodeProgressPanel() {
  const { data, isLoading, isError, error, refetch } = useLeetCodeProfile();

  return (
    <Card className="animate-fade-up">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <Code2 className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">LeetCode progress</CardTitle>
          <CardDescription>Live public data from your LeetCode profile — real practice evidence.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-48" />
        ) : isError ? (
          <ErrorState
            message={error instanceof Error ? error.message : "Couldn't load your LeetCode profile."}
            onRetry={() => refetch()}
          />
        ) : !data || data.status === "not_configured" ? (
          <EmptyState
            icon={Code2}
            title="Add your LeetCode username"
            description="Link your LeetCode handle in Settings to track solved problems, streaks, and contests here — real public data, no login needed."
            action={
              <Button asChild size="sm" variant="outline">
                <Link href="/settings">Go to Settings</Link>
              </Button>
            }
          />
        ) : data.status === "not_found" ? (
          <ErrorState
            title="LeetCode user not found"
            message={`We couldn't find a public LeetCode profile for "${data.username}". Double-check the username in Settings.`}
          />
        ) : data.status === "unavailable" ? (
          <ErrorState
            title="LeetCode is unreachable right now"
            message="Couldn't reach LeetCode. Try again in a bit."
            onRetry={() => refetch()}
          />
        ) : (
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              {data.avatar_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={data.avatar_url} alt="" className="h-12 w-12 rounded-full border border-border" />
              )}
              <div className="min-w-0">
                <a
                  href={data.profile_url ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="truncate text-sm font-semibold text-foreground hover:text-brand hover:underline"
                >
                  {data.real_name || data.username}
                </a>
                <p className="text-xs text-muted">
                  {data.ranking ? `Global rank #${data.ranking.toLocaleString()}` : `@${data.username}`}
                </p>
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-baseline justify-between gap-2">
                <p className="text-xs font-semibold text-foreground">Problems solved</p>
                <p className="text-sm text-muted">
                  <span className="text-lg font-bold tabular-nums text-foreground">{data.total_solved}</span>
                  {data.total_questions > 0 && <span> / {data.total_questions}</span>}
                  {data.acceptance_rate != null && (
                    <span className="ml-2 text-[11px]">{data.acceptance_rate.toFixed(1)}% acceptance</span>
                  )}
                </p>
              </div>
              <div className="space-y-2">
                {DIFFICULTY_ROWS.map((row) => {
                  const solved = data[`${row.key}_solved`];
                  const total = data[`${row.key}_total`];
                  return (
                    <div key={row.key}>
                      <div className="mb-1 flex items-center justify-between gap-2 text-xs">
                        <span className="font-medium" style={{ color: row.color }}>
                          {row.label}
                        </span>
                        <span className="text-muted tabular-nums">
                          {solved}
                          {total > 0 ? ` / ${total}` : ""} solved
                        </span>
                      </div>
                      <AnimatedBar percent={total > 0 ? solved / total : 0} color={row.color} />
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
              <StatTile icon={Flame} label="Current streak" value={`${data.current_streak_days}d`} accent="var(--color-warning)" />
              <StatTile icon={Zap} label="Longest streak" value={`${data.longest_streak_days}d`} accent="var(--color-brand)" />
              <StatTile
                icon={CalendarCheck}
                label="Active days / yr"
                value={String(data.active_days_last_year)}
                accent="var(--color-positive)"
              />
              <StatTile icon={Award} label="Badges" value={String(data.badges_count)} />
            </div>

            <div>
              <p className="mb-2 text-xs font-semibold text-foreground">Recent activity</p>
              <ActivityHeatmap days={data.activity_heatmap} />
            </div>

            <ContestSection data={data} />

            <LanguageStats data={data} />

            <p className="text-[10px] text-muted">
              {data.last_synced_at ? `Synced ${formatDate(data.last_synced_at)}. ` : ""}
              Public data read from LeetCode&apos;s GraphQL endpoint — nothing is written to your account.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
