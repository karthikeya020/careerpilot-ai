"use client";

import { Briefcase, Check, IndianRupee, Loader2, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn, formatPercent } from "@/lib/utils";
import type { JobListingMatchOut, JobSector } from "@/types/api";

const SECTOR_STYLE: Record<JobSector, { label: string; accent: string }> = {
  faang: { label: "FAANG", accent: "var(--color-brand)" },
  startup: { label: "Startup", accent: "var(--color-accent-2)" },
  research: { label: "Research", accent: "var(--color-brand-2)" },
  government: { label: "Government", accent: "var(--color-warning)" },
  consulting: { label: "Consulting", accent: "var(--color-accent)" },
  finance: { label: "Finance", accent: "var(--color-positive)" },
};

function ReadinessRing({ value }: { value: number | null }) {
  const pct = value !== null ? Math.round(value * 100) : null;
  const circumference = 2 * Math.PI * 16;
  const offset = pct !== null ? circumference * (1 - pct / 100) : circumference;
  const color = pct === null ? "var(--color-border-strong)" : pct >= 70 ? "var(--color-positive)" : pct >= 40 ? "var(--color-warning)" : "var(--color-danger)";

  return (
    <div className="relative flex h-11 w-11 shrink-0 items-center justify-center">
      <svg width="44" height="44" className="-rotate-90">
        <circle cx="22" cy="22" r="16" fill="none" stroke="var(--color-surface-muted)" strokeWidth="4" />
        <circle
          cx="22" cy="22" r="16" fill="none" stroke={color} strokeWidth="4" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 600ms ease-out" }}
        />
      </svg>
      <span className="absolute text-[10px] font-bold tabular-nums text-foreground">{pct !== null ? `${pct}%` : "—"}</span>
    </div>
  );
}

export function JobCard({
  match,
  onTrack,
  onUntrack,
  isPending,
}: {
  match: JobListingMatchOut;
  onTrack: (listingId: string) => void;
  onUntrack: (listingId: string) => void;
  isPending: boolean;
}) {
  const { listing } = match;
  const sectorStyle = SECTOR_STYLE[listing.sector];

  return (
    <div className="card-premium card-premium-hover flex w-72 shrink-0 snap-start flex-col gap-3 rounded-[var(--radius-lg)] p-4">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <span
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] text-sm font-bold text-white"
            style={{ background: `linear-gradient(135deg, ${sectorStyle.accent}, color-mix(in srgb, ${sectorStyle.accent} 60%, black))` }}
          >
            {listing.company.slice(0, 1)}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-foreground">{listing.company}</p>
            <p className="truncate text-xs text-muted">{listing.title}</p>
          </div>
        </div>
        <ReadinessRing value={match.readiness} />
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        <Badge variant="outline" style={{ color: sectorStyle.accent, borderColor: sectorStyle.accent }}>
          {sectorStyle.label}
        </Badge>
        <Badge variant="muted" className="gap-1">
          <IndianRupee className="h-3 w-3" aria-hidden="true" />
          {listing.package_min_lpa}-{listing.package_max_lpa} LPA
        </Badge>
      </div>

      <div className="min-h-[3rem] flex-1">
        {match.missing_skills.length > 0 ? (
          <>
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-muted">You're missing</p>
            <div className="flex flex-wrap gap-1">
              {match.missing_skills.slice(0, 3).map((s) => (
                <Badge key={s.id} variant="danger">
                  {s.name}
                </Badge>
              ))}
              {match.missing_skills.length > 3 && <Badge variant="muted">+{match.missing_skills.length - 3} more</Badge>}
            </div>
          </>
        ) : (
          <p className="flex items-center gap-1 text-xs font-medium text-positive">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" /> You match every required skill!
          </p>
        )}
      </div>

      <Button
        size="sm"
        variant={match.is_tracked ? "outline" : "primary"}
        disabled={isPending}
        onClick={() => (match.is_tracked ? onUntrack(listing.id) : onTrack(listing.id))}
        className="w-full"
      >
        {isPending ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        ) : match.is_tracked ? (
          <>
            <Check className="h-3.5 w-3.5" aria-hidden="true" /> Tracking this job
          </>
        ) : (
          <>
            <Briefcase className="h-3.5 w-3.5" aria-hidden="true" /> I want this job
          </>
        )}
      </Button>
    </div>
  );
}

export function JobCardSkeleton() {
  return (
    <div className={cn("card-premium flex w-72 shrink-0 flex-col gap-3 rounded-[var(--radius-lg)] p-4 animate-pulse")}>
      <div className="flex items-center gap-2.5">
        <div className="h-10 w-10 rounded-[var(--radius-md)] bg-surface-muted" />
        <div className="flex-1 space-y-1.5">
          <div className="h-3 w-24 rounded bg-surface-muted" />
          <div className="h-2.5 w-32 rounded bg-surface-muted" />
        </div>
      </div>
      <div className="h-5 w-full rounded bg-surface-muted" />
      <div className="h-8 w-full rounded bg-surface-muted" />
    </div>
  );
}
