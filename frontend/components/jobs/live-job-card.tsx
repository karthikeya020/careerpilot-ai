"use client";

import { useState } from "react";
import { Check, ChevronDown, ChevronUp, ExternalLink, Loader2, MapPin, Radio } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { JobRoadmap } from "@/components/jobs/job-roadmap";
import { spotlightMove } from "@/components/ui/fx";
import { useSkillMatch, useTrackLiveJob } from "@/hooks/use-live-jobs";
import { GiftBurst, playGiftSound } from "@/lib/gift-fx";
import { ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { LiveJobOut, LiveJobSkillOut } from "@/types/api";

const SECTOR_ACCENT: Record<string, string> = {
  faang: "var(--color-brand)",
  startup: "var(--color-accent-2)",
  research: "var(--color-brand-2)",
  government: "var(--color-warning)",
  consulting: "var(--color-accent)",
  finance: "var(--color-positive)",
};

const IMPORTANCE_BADGE: Record<LiveJobSkillOut["importance"], "danger" | "warning" | "muted"> = {
  core: "danger",
  strong: "warning",
  familiar: "muted",
};

function SkillMatch({ skills }: { skills: string[] }) {
  const { data, isLoading } = useSkillMatch(skills);
  if (isLoading) return <div className="h-3.5 w-2/3 animate-pulse rounded bg-surface-muted" />;
  if (!data || data.readiness === null) return null;
  const total = data.matched.length + data.partial.length + data.missing.length;
  const pct = Math.round((data.readiness ?? 0) * 100);
  const tone = pct >= 70 ? "var(--color-positive)" : pct >= 40 ? "var(--color-warning)" : "var(--color-danger)";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-[11px]">
        <span className="font-medium text-foreground">Skill match</span>
        <span className="tabular-nums" style={{ color: tone }}>
          {pct}% · {data.matched.length}/{total}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-muted">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: tone }} />
      </div>
      {data.missing.length > 0 && (
        <p className="text-[10px] text-muted">
          Missing: <span className="text-danger">{data.missing.slice(0, 4).join(", ")}</span>
        </p>
      )}
    </div>
  );
}

export function LiveJobCard({ job }: { job: LiveJobOut }) {
  const accent = SECTOR_ACCENT[job.sector] ?? "var(--color-brand)";
  const [expanded, setExpanded] = useState(false);
  const [burstKey, setBurstKey] = useState(0);
  const track = useTrackLiveJob();
  const skillNames = job.skills.map((s) => s.name);

  const want = () => {
    playGiftSound();
    setBurstKey((k) => k + 1);
    track.mutate(job.id, {
      onSuccess: () => toast.success(`${job.company} added to your dream jobs — tracked from now on.`),
      onError: (err) =>
        toast.error(err instanceof ApiError ? err.message : "Couldn't add that to your dream jobs."),
    });
  };

  return (
    <div
      onMouseMove={spotlightMove}
      className="js-card ds-raise group relative flex w-full flex-col gap-2.5 overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface p-4 hover:border-brand/40 hover:shadow-[var(--shadow-glow-brand)]"
    >
      <span className="js-spot" aria-hidden="true" />
      <div className="relative flex items-start gap-2.5">
        <span
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] text-sm font-bold text-white"
          style={{ background: `linear-gradient(135deg, ${accent}, color-mix(in srgb, ${accent} 55%, black))` }}
        >
          {job.company.slice(0, 1)}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1">
            <span className="text-sm font-bold text-foreground">{job.company}</span>
            <Badge variant="outline" style={{ color: accent, borderColor: accent }} className="text-[10px]">
              {job.sector}
            </Badge>
            <Badge variant={job.is_live ? "positive" : "muted"} className="gap-0.5 text-[10px]">
              <Radio className="h-2.5 w-2.5" aria-hidden="true" /> {job.is_live ? "Live" : "Curated"}
            </Badge>
            {job.is_internship && <Badge variant="warning" className="text-[10px]">Internship</Badge>}
          </div>
          <p className="mt-0.5 line-clamp-2 text-sm font-semibold leading-tight text-foreground">{job.title}</p>
          <p className="mt-0.5 flex items-center gap-1 text-[11px] text-muted">
            <MapPin className="h-3 w-3" aria-hidden="true" /> {job.location}
            {job.remote && <span className="ml-1 rounded bg-surface-muted px-1 text-[9px]">Remote</span>}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-1">
        {job.skills.slice(0, 6).map((s) => (
          <Badge key={s.name} variant={IMPORTANCE_BADGE[s.importance]} className="text-[10px]">
            {s.name}
          </Badge>
        ))}
        {job.skills.length > 6 && <Badge variant="muted" className="text-[10px]">+{job.skills.length - 6}</Badge>}
      </div>

      <SkillMatch skills={skillNames} />

      <div className="flex flex-wrap gap-1.5">
        <Button size="sm" onClick={want} disabled={track.isPending} className="ds-press bg-gradient-brand">
          {track.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          ) : (
            <Check className="h-3.5 w-3.5" aria-hidden="true" />
          )}
          I want this job
        </Button>
        {job.url && (
          <Button size="sm" variant="outline" asChild className="ds-press">
            <a href={job.url} target="_blank" rel="noreferrer">
              Apply <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
          </Button>
        )}
        <Button size="sm" variant="ghost" onClick={() => setExpanded((e) => !e)} className="ds-press">
          {expanded ? (
            <>
              Less <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
            </>
          ) : (
            <>
              JD &amp; roadmap <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
            </>
          )}
        </Button>
      </div>

      {expanded && (
        <div className="animate-fade-in space-y-3 border-t border-border pt-3 text-xs">
          <p className="leading-relaxed text-muted">{job.summary}</p>
          {job.responsibilities.length > 0 && (
            <div>
              <p className="mb-1 font-semibold text-foreground">What you&apos;d do</p>
              <ul className="space-y-1">
                {job.responsibilities.slice(0, 6).map((r, i) => (
                  <li key={i} className="flex gap-1.5 text-muted">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand" aria-hidden="true" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {job.requirements.length > 0 && (
            <div>
              <p className="mb-1 font-semibold text-foreground">Requirements</p>
              <ul className="space-y-1">
                {job.requirements.slice(0, 6).map((r, i) => (
                  <li key={i} className="flex gap-1.5 text-muted">
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-danger" aria-hidden="true" />
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div>
            <p className="mb-1.5 font-semibold text-foreground">How to crack it</p>
            <JobRoadmap company={job.company} title={job.title} sector={job.sector} skills={skillNames} />
          </div>
        </div>
      )}

      {burstKey > 0 && <GiftBurst key={burstKey} onDone={() => setBurstKey(0)} />}
    </div>
  );
}

export function LiveJobCardSkeleton() {
  return (
    <div className={cn("flex w-full flex-col gap-3 rounded-[var(--radius-lg)] border border-border p-4 animate-pulse")}>
      <div className="flex items-center gap-2.5">
        <div className="h-10 w-10 rounded-[var(--radius-md)] bg-surface-muted" />
        <div className="flex-1 space-y-1.5">
          <div className="h-3 w-24 rounded bg-surface-muted" />
          <div className="h-2.5 w-40 rounded bg-surface-muted" />
        </div>
      </div>
      <div className="h-4 w-full rounded bg-surface-muted" />
      <div className="h-8 w-1/2 rounded bg-surface-muted" />
    </div>
  );
}
