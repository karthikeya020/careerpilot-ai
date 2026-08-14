"use client";

import Link from "next/link";
import { Code2, Star, Users } from "lucide-react";
import { AnimatedBar } from "@/components/ui/animated-bar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useGithubProfile } from "@/hooks/use-github-profile";
import { useStaggerReveal } from "@/hooks/use-stagger-reveal";
import { formatDate } from "@/lib/utils";
import type { GithubActivityDayOut, GithubRepoOut } from "@/types/api";

// Sequential single-hue scale (brand hue, light -> dark via opacity) for the
// activity heatmap -- a magnitude encoding, never a categorical rainbow.
function activityOpacity(count: number, max: number): number {
  if (count <= 0 || max <= 0) return 0.08;
  const ratio = count / max;
  if (ratio > 0.75) return 1;
  if (ratio > 0.5) return 0.75;
  if (ratio > 0.25) return 0.5;
  return 0.3;
}

function ActivityHeatmap({ days }: { days: GithubActivityDayOut[] }) {
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
  const gridRef = useStaggerReveal<HTMLDivElement>(days.length, { delay: 4, y: 0 });

  return (
    <div>
      <div ref={gridRef} className="grid grid-flow-col grid-rows-7 gap-1" role="img" aria-label="Public GitHub activity over the last 90 days">
        {cells.map((cell) => (
          <span
            key={cell.date}
            title={`${cell.date}: ${cell.count} public event${cell.count === 1 ? "" : "s"}`}
            className="h-2.5 w-2.5 rounded-sm"
            style={{ background: `color-mix(in srgb, var(--color-brand) ${activityOpacity(cell.count, max) * 100}%, var(--color-surface-muted))` }}
          />
        ))}
      </div>
      <p className="mt-2 text-[10px] text-muted">Last ~90 days of public GitHub activity (GitHub&apos;s public events API retention window).</p>
    </div>
  );
}

function LanguageBreakdown({ breakdown }: { breakdown: Record<string, number> }) {
  const entries = Object.entries(breakdown).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const total = entries.reduce((sum, [, count]) => sum + count, 0);
  if (entries.length === 0) {
    return <p className="text-xs text-muted">No language data on public, non-fork repos yet.</p>;
  }
  return (
    <div className="space-y-2">
      {entries.map(([language, count]) => (
        <div key={language}>
          <div className="mb-1 flex items-center justify-between gap-2 text-xs">
            <span className="font-medium text-foreground">{language}</span>
            <span className="text-muted">{count} repo{count === 1 ? "" : "s"}</span>
          </div>
          <AnimatedBar percent={total > 0 ? count / total : 0} className="bg-brand" />
        </div>
      ))}
      <p className="text-[10px] text-muted">By repo count (non-fork), not lines of code.</p>
    </div>
  );
}

function TopRepos({ repos }: { repos: GithubRepoOut[] }) {
  if (repos.length === 0) return null;
  return (
    <ul className="space-y-1.5">
      {repos.map((repo) => (
        <li key={repo.name} className="flex items-center justify-between gap-2 text-xs">
          <a href={repo.html_url} target="_blank" rel="noreferrer" className="truncate font-medium text-foreground hover:text-brand hover:underline">
            {repo.name}
          </a>
          <span className="flex shrink-0 items-center gap-2 text-muted">
            {repo.language && <Badge variant="muted" className="text-[10px]">{repo.language}</Badge>}
            <span className="flex items-center gap-1">
              <Star className="h-3 w-3" aria-hidden="true" /> {repo.stargazers_count}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}

export function GithubProfilePanel() {
  const { data, isLoading, isError, error, refetch } = useGithubProfile();

  return (
    <Card className="animate-fade-up">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <Code2 className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">Verified coding profile</CardTitle>
          <CardDescription>Real, public GitHub activity — evidence a reviewer can check themselves.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-40" />
        ) : isError ? (
          <ErrorState message={error instanceof Error ? error.message : "Couldn't load your GitHub profile."} onRetry={() => refetch()} />
        ) : !data || data.status === "not_configured" ? (
          <EmptyState
            icon={Code2}
            title="Add your GitHub username"
            description="Link your GitHub account in Settings to show real repo, language, and activity evidence here."
            action={
              <Button asChild size="sm" variant="outline">
                <Link href="/settings">Go to Settings</Link>
              </Button>
            }
          />
        ) : data.status === "not_found" ? (
          <ErrorState
            title="GitHub user not found"
            message={`We couldn't find a public GitHub profile for "${data.username}". Double-check the username in Settings.`}
          />
        ) : data.status === "unavailable" ? (
          <ErrorState title="GitHub is unreachable right now" message="Couldn't reach GitHub's API. Try again in a bit." onRetry={() => refetch()} />
        ) : (
          <div className="space-y-5">
            <div className="flex items-center gap-3">
              {data.avatar_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={data.avatar_url} alt="" className="h-12 w-12 rounded-full border border-border" />
              )}
              <div className="min-w-0">
                <a href={data.html_url ?? "#"} target="_blank" rel="noreferrer" className="truncate text-sm font-semibold text-foreground hover:text-brand hover:underline">
                  {data.name || data.username}
                </a>
                {data.bio && <p className="truncate text-xs text-muted">{data.bio}</p>}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-2">
                <p className="text-sm font-semibold text-foreground">{data.public_repos}</p>
                <p className="text-[10px] text-muted">Public repos</p>
              </div>
              <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-2">
                <p className="flex items-center justify-center gap-1 text-sm font-semibold text-foreground">
                  <Users className="h-3 w-3" aria-hidden="true" /> {data.followers}
                </p>
                <p className="text-[10px] text-muted">Followers</p>
              </div>
              <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-2">
                <p className="text-sm font-semibold text-foreground">{formatDate(data.account_created_at)}</p>
                <p className="text-[10px] text-muted">On GitHub since</p>
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-semibold text-foreground">Language breakdown</p>
              <LanguageBreakdown breakdown={data.language_breakdown} />
            </div>

            <div>
              <p className="mb-2 text-xs font-semibold text-foreground">Recent activity</p>
              <ActivityHeatmap days={data.activity_heatmap} />
            </div>

            {data.top_repos.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-semibold text-foreground">Top repos</p>
                <TopRepos repos={data.top_repos} />
              </div>
            )}

            {data.last_synced_at && <p className="text-[10px] text-muted">Last synced {formatDate(data.last_synced_at)}.</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
