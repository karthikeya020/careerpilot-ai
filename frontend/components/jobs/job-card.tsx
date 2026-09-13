"use client";

import { useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Briefcase, Check, IndianRupee, Loader2, Map as MapIcon, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { JobRoadmap } from "@/components/jobs/job-roadmap";
import { spotlightMove } from "@/components/ui/fx";
import { GiftBurst, playGiftSound } from "@/lib/gift-fx";
import { cn } from "@/lib/utils";
import type { JobListingMatchOut, JobSector, SkillOut } from "@/types/api";

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

function SkillChips({ skills, tone }: { skills: SkillOut[]; tone: "positive" | "warning" | "danger" }) {
  if (skills.length === 0) return <span className="text-[11px] text-muted">none</span>;
  return (
    <div className="flex flex-wrap gap-1">
      {skills.map((s) => (
        <Badge key={s.id} variant={tone} className="text-[10px]">
          {s.name}
        </Badge>
      ))}
    </div>
  );
}

interface HoverAnchor {
  rect: DOMRect;
  vw: number;
  vh: number;
}

function HoverPanel({
  match,
  anchor,
  onRoadmap,
}: {
  match: JobListingMatchOut;
  anchor: HoverAnchor;
  onRoadmap: () => void;
}) {
  const { listing } = match;
  const { rect, vw, vh } = anchor;
  const below = rect.bottom + 340 < vh;
  const style: React.CSSProperties = {
    position: "fixed",
    left: Math.min(Math.max(rect.left + rect.width / 2 - 180, 12), vw - 372),
    top: below ? rect.bottom + 8 : undefined,
    bottom: below ? undefined : vh - rect.top + 8,
    width: 360,
  };
  return createPortal(
    <div
      style={style}
      className="z-[70] rounded-[var(--radius-lg)] border border-border bg-surface p-4 shadow-2xl"
    >
      <p className="text-sm font-semibold text-foreground">{listing.company} — {listing.title}</p>
      <p className="mt-1 text-xs leading-relaxed text-muted">{listing.description}</p>
      <div className="mt-3 space-y-2">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-positive">You have</p>
          <SkillChips skills={match.matched_skills} tone="positive" />
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-warning">Partial</p>
          <SkillChips skills={match.partial_skills} tone="warning" />
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-danger">Missing — build these</p>
          <SkillChips skills={match.missing_skills} tone="danger" />
        </div>
        {listing.emphasis_domains.length > 0 && (
          <p className="text-[11px] text-muted">
            Leans hardest on:{" "}
            {listing.emphasis_domains.map((d) => (
              <Badge key={d} variant="muted" className="ml-1 text-[10px] uppercase">
                {d}
              </Badge>
            ))}
          </p>
        )}
      </div>
      <button onClick={onRoadmap} className="mt-3 text-xs font-medium text-brand hover:underline">
        See the full roadmap to crack it →
      </button>
    </div>,
    document.body,
  );
}

function RoadmapModal({ listingId, company, onClose }: { listingId: string; company: string; onClose: () => void }) {
  return createPortal(
    <div
      className="fixed inset-0 z-[80] flex items-start justify-center overflow-y-auto bg-foreground/30 p-4 backdrop-blur-[2px] sm:p-6"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="animate-scale-in mt-[5vh] w-full max-w-2xl overflow-hidden rounded-[var(--radius-xl)] border border-border bg-surface shadow-2xl">
        <div className="h-1 w-full bg-gradient-brand" aria-hidden="true" />
        <div className="flex items-center justify-between border-b border-border px-5 py-3">
          <p className="text-sm font-semibold text-foreground">How to crack {company}</p>
          <button onClick={onClose} aria-label="Close" className="rounded-full p-1.5 text-muted hover:bg-surface-muted hover:text-foreground">
            ✕
          </button>
        </div>
        <div className="max-h-[80vh] overflow-y-auto p-5">
          <JobRoadmap listingId={listingId} />
        </div>
      </div>
    </div>,
    document.body,
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
  const cardRef = useRef<HTMLDivElement>(null);
  const hoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [anchor, setAnchor] = useState<HoverAnchor | null>(null);
  const [roadmapOpen, setRoadmapOpen] = useState(false);
  const [burstKey, setBurstKey] = useState(0);

  const openHover = () => {
    if (hoverTimer.current) clearTimeout(hoverTimer.current);
    hoverTimer.current = setTimeout(() => {
      if (cardRef.current) {
        setAnchor({
          rect: cardRef.current.getBoundingClientRect(),
          vw: window.innerWidth,
          vh: window.innerHeight,
        });
      }
    }, 140);
  };
  const closeHover = () => {
    if (hoverTimer.current) clearTimeout(hoverTimer.current);
    setAnchor(null);
  };

  const wantJob = () => {
    playGiftSound();
    setBurstKey((k) => k + 1);
    onTrack(listing.id);
  };

  return (
    <div
      ref={cardRef}
      onMouseEnter={openHover}
      onMouseLeave={closeHover}
      onMouseMove={spotlightMove}
      onFocusCapture={openHover}
      onBlurCapture={closeHover}
      className="js-card card-premium card-premium-hover group relative flex w-72 shrink-0 snap-start flex-col gap-3 overflow-hidden rounded-[var(--radius-lg)] p-4"
    >
      <span className="js-spot" aria-hidden="true" />
      <div className="relative flex items-start justify-between gap-2">
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
            <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-muted">You&apos;re missing</p>
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
        <button
          onClick={() => setRoadmapOpen(true)}
          className="group/rm mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-brand"
        >
          <MapIcon className="h-3 w-3" aria-hidden="true" />
          <span className="ds-underline">Roadmap</span>
          <span
            aria-hidden="true"
            className="transition-transform duration-200 ease-out group-hover/rm:translate-x-0.5"
          >
            →
          </span>
        </button>
      </div>

      <Button
        size="sm"
        variant={match.is_tracked ? "outline" : "primary"}
        disabled={isPending}
        onClick={() => (match.is_tracked ? onUntrack(listing.id) : wantJob())}
        className="ds-press w-full"
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

      {anchor && !roadmapOpen && <HoverPanel match={match} anchor={anchor} onRoadmap={() => setRoadmapOpen(true)} />}
      {roadmapOpen && <RoadmapModal listingId={listing.id} company={listing.company} onClose={() => setRoadmapOpen(false)} />}
      {burstKey > 0 && <GiftBurst key={burstKey} onDone={() => setBurstKey(0)} />}
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
