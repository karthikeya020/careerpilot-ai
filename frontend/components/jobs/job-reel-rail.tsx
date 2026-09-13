"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { motion } from "framer-motion";
import {
  Briefcase,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Loader2,
  MapPin,
  Radio,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { JobRoadmap } from "@/components/jobs/job-roadmap";
import { LaptopBoot } from "@/components/jobs/laptop-boot";
import { CountUp, spotlightMove } from "@/components/ui/fx";
import { useLiveJobFeed, useSkillMatch, useTrackLiveJob, type LiveFeedKind } from "@/hooks/use-live-jobs";
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

function registerCard(map: { current: Map<number, HTMLElement> }, idx: number, el: HTMLElement | null) {
  if (el) map.current.set(idx, el);
  else map.current.delete(idx);
}

function SkillMatchLine({ skills }: { skills: string[] }) {
  const { data, isLoading } = useSkillMatch(skills);
  if (isLoading) return <div className="h-4 w-2/3 animate-pulse rounded bg-surface-muted" />;
  if (!data || data.readiness === null) return null;
  const total = data.matched.length + data.partial.length + data.missing.length;
  const pct = Math.round((data.readiness ?? 0) * 100);
  const tone = pct >= 70 ? "var(--color-positive)" : pct >= 40 ? "var(--color-warning)" : "var(--color-danger)";
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-[11px]">
        <span className="font-medium text-foreground">Skill match</span>
        <span className="tabular-nums" style={{ color: tone }}>
          {pct}% · {data.matched.length}/{total} you have
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-muted">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: tone }} />
      </div>
      {data.missing.length > 0 && (
        <p className="text-[10px] text-muted">
          Missing: <span className="text-danger">{data.missing.slice(0, 4).join(", ")}</span>
          {data.missing.length > 4 ? ` +${data.missing.length - 4}` : ""}
        </p>
      )}
    </div>
  );
}

function RailCard({
  job,
  focused,
  expanded,
  onFocus,
  onToggle,
  registerRef,
}: {
  job: LiveJobOut;
  focused: boolean;
  expanded: boolean;
  onFocus: () => void;
  onToggle: () => void;
  registerRef: (el: HTMLElement | null) => void;
}) {
  const accent = SECTOR_ACCENT[job.sector] ?? "var(--color-brand)";
  const [wanted, setWanted] = useState(false);
  const [burstKey, setBurstKey] = useState(0);
  const track = useTrackLiveJob();

  const want = () => {
    playGiftSound();
    setBurstKey((k) => k + 1);
    setWanted(true);
    if (!expanded) onToggle();
    track.mutate(job.id, {
      onSuccess: () => toast.success(`${job.company} added to your dream jobs — tracked from now on.`),
      onError: (err) => {
        setWanted(false);
        toast.error(err instanceof ApiError ? err.message : "Couldn't add that to your dream jobs.");
      },
    });
  };

  return (
    <article
      ref={registerRef}
      onMouseEnter={onFocus}
      onMouseMove={spotlightMove}
      className={cn(
        "js-card reel-card relative snap-start scroll-mt-3 mx-2 my-2 overflow-hidden rounded-[var(--radius-lg)] border p-3.5",
        focused
          ? "border-brand/50 bg-brand-soft/25 shadow-[var(--shadow-glow-brand)] ring-1 ring-inset ring-brand/30"
          : "border-border/60 bg-surface",
      )}
      style={{ minHeight: "calc((100dvh - 8rem) / 3)" }}
    >
      <span className="js-spot" aria-hidden="true" />
      <div className="flex items-start gap-2.5">
        <span
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] text-sm font-bold text-white"
          style={{ background: `linear-gradient(135deg, ${accent}, color-mix(in srgb, ${accent} 55%, black))` }}
        >
          {job.company.slice(0, 1)}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1">
            <span className="text-xs font-bold text-foreground">{job.company}</span>
            <Badge variant="outline" style={{ color: accent, borderColor: accent }} className="text-[9px]">
              {job.sector}
            </Badge>
            <Badge variant={job.is_live ? "positive" : "muted"} className="gap-0.5 text-[9px]">
              <Radio className="h-2 w-2" aria-hidden="true" /> {job.is_live ? "Live" : "Curated"}
            </Badge>
            {job.is_internship && (
              <Badge variant="warning" className="text-[9px]">Internship</Badge>
            )}
          </div>
          <h3 className="mt-0.5 line-clamp-2 text-sm font-semibold leading-tight text-foreground">{job.title}</h3>
          <p className="mt-0.5 flex items-center gap-1 text-[11px] text-muted">
            <MapPin className="h-3 w-3" aria-hidden="true" /> {job.location}
            {job.remote && <span className="ml-1 rounded bg-surface-muted px-1 text-[9px]">Remote</span>}
          </p>
        </div>
      </div>

      <div className="mt-2 flex flex-wrap gap-1">
        {job.skills.slice(0, 5).map((s) => (
          <Badge key={s.name} variant={IMPORTANCE_BADGE[s.importance]} className="text-[9px]">
            {s.name}
          </Badge>
        ))}
        {job.skills.length > 5 && <Badge variant="muted" className="text-[9px]">+{job.skills.length - 5}</Badge>}
      </div>

      <div className="mt-2">
        <SkillMatchLine skills={job.skills.map((s) => s.name)} />
      </div>

      <div className="mt-2.5 flex flex-wrap gap-1.5">
        <Button
          size="sm"
          onClick={want}
          disabled={wanted || track.isPending}
          className="h-7 bg-gradient-brand px-2 text-[11px]"
        >
          {track.isPending ? (
            <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
          ) : (
            <Briefcase className="h-3 w-3" aria-hidden="true" />
          )}
          {track.isPending ? "Adding…" : wanted ? "Tracking ✓" : "I want this job"}
        </Button>
        {job.url && (
          <Button size="sm" variant="outline" className="h-7 px-2 text-[11px]" asChild>
            <a href={job.url} target="_blank" rel="noreferrer">
              Apply <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
          </Button>
        )}
        <Button size="sm" variant="ghost" className="h-7 px-2 text-[11px]" onClick={onToggle}>
          {expanded ? (
            <>
              Less <ChevronUp className="h-3 w-3" aria-hidden="true" />
            </>
          ) : (
            <>
              JD &amp; roadmap <ChevronDown className="h-3 w-3" aria-hidden="true" />
            </>
          )}
        </Button>
      </div>

      {expanded && (
        <div className="animate-fade-in mt-3 space-y-3 border-t border-border pt-3 text-xs">
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
            <JobRoadmap
              company={job.company}
              title={job.title}
              sector={job.sector}
              skills={job.skills.map((s) => s.name)}
            />
          </div>
        </div>
      )}

      {burstKey > 0 && <GiftBurst key={burstKey} onDone={() => setBurstKey(0)} />}
    </article>
  );
}

export function JobReelRail({ onClose }: { onClose: () => void }) {
  const [kind, setKind] = useState<LiveFeedKind>("jobs");
  const { data, fetchNextPage, isFetchingNextPage, isLoading } = useLiveJobFeed(kind);
  const jobs = useMemo(() => (data?.pages ?? []).flatMap((p) => p.jobs), [data]);
  const live = data?.pages?.[0]?.live;

  const [focusIdx, setFocusIdx] = useState(0);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const cardRefs = useRef<Map<number, HTMLElement>>(new Map());
  const sentinelRef = useRef<HTMLDivElement>(null);
  const scrollerRef = useRef<HTMLDivElement>(null);

  const close = () => {
    window.dispatchEvent(new CustomEvent("careerpilot:reel", { detail: false }));
    onClose();
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (document.activeElement?.tagName ?? "").toLowerCase();
      if (["input", "textarea", "select"].includes(tag)) return;
      if (e.key === "Escape") {
        close();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setFocusIdx((i) => Math.min(i + 1, Math.max(jobs.length - 1, 0)));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setFocusIdx((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter") {
        setExpandedIdx((x) => (x === focusIdx ? null : focusIdx));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobs.length, focusIdx]);

  useEffect(() => {
    cardRefs.current.get(focusIdx)?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [focusIdx]);

  // Entrance reveal: each card fades + rises into place the first time it
  // scrolls into view. One-shot per card -- no per-frame work, can't glitch.
  useEffect(() => {
    const scroller = scrollerRef.current;
    if (!scroller) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            e.target.classList.add("reel-in");
            io.unobserve(e.target);
          }
        }
      },
      { root: scroller, threshold: 0.12 },
    );
    for (const el of cardRefs.current.values()) io.observe(el);
    return () => io.disconnect();
  }, [jobs.length]);

  useEffect(() => {
    if (!sentinelRef.current) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !isFetchingNextPage) fetchNextPage();
      },
      { rootMargin: "400px" },
    );
    obs.observe(sentinelRef.current);
    return () => obs.disconnect();
  }, [fetchNextPage, isFetchingNextPage, jobs.length]);

  if (typeof document === "undefined") return null;

  return createPortal(
    <motion.aside
      initial={{ x: "100%", opacity: 0.5 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 34 }}
      className="fixed right-0 bottom-0 top-14 z-40 flex w-[min(42vw,560px)] flex-col overflow-hidden rounded-l-[var(--radius-xl)] border-l border-border/60 bg-surface/95 shadow-2xl backdrop-blur-sm"
    >
      <style>{`
        /* Scroll-driven reveal: cards blur/shrink/fade at the viewport edges
           and are crisp in the middle -- animates as you scroll, cannot glitch. */
        @media (prefers-reduced-motion: no-preference) {
          @supports (animation-timeline: view()) {
            .reel-card {
              animation: reel-through linear both;
              animation-timeline: view(block);
              animation-range: cover 0% cover 100%;
            }
            @keyframes reel-through {
              0%   { opacity: 0; transform: translateY(26px) scale(.9);  filter: blur(6px); }
              14%  { opacity: 1; transform: none;                        filter: blur(0); }
              86%  { opacity: 1; transform: none;                        filter: blur(0); }
              100% { opacity: .12; transform: translateY(-22px) scale(.92); filter: blur(5px); }
            }
          }
          @supports not (animation-timeline: view()) {
            .reel-card { opacity: 0; transform: translateY(16px); transition: opacity .5s ease, transform .5s cubic-bezier(.22,1,.36,1); }
            .reel-card.reel-in { opacity: 1; transform: translateY(0); }
          }
        }
      `}</style>
      <div className="flex items-center justify-between gap-2 border-b border-border/60 px-3 py-2.5">
        <div className="flex items-center gap-2">
          <div className="flex rounded-full border border-border p-0.5 text-[11px] font-medium">
            {(["jobs", "internships"] as const).map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => {
                  setKind(k);
                  setFocusIdx(0);
                  setExpandedIdx(null);
                }}
                className={cn(
                  "relative rounded-full px-2.5 py-0.5 capitalize transition-colors",
                  kind === k ? "text-brand-foreground" : "text-muted hover:text-foreground",
                )}
              >
                {kind === k && (
                  <motion.span
                    layoutId="reel-kind-pill"
                    className="absolute inset-0 -z-10 rounded-full bg-gradient-brand"
                    transition={{ type: "spring", stiffness: 400, damping: 32 }}
                  />
                )}
                {k}
              </button>
            ))}
          </div>
          <Badge variant={live ? "positive" : "muted"} className="gap-0.5 text-[9px]">
            <Radio className="h-2 w-2" aria-hidden="true" /> {live ? "Live" : "Curated"}
          </Badge>
        </div>
        <button
          onClick={close}
          aria-label="Close job reel"
          className="rounded-full p-1.5 text-muted transition-colors hover:bg-surface-muted hover:text-foreground"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {isLoading ? (
        <div className="flex flex-1 items-center justify-center">
          <LaptopBoot />
        </div>
      ) : jobs.length === 0 ? (
        <div className="flex flex-1 items-center justify-center px-6 text-center text-xs text-muted">
          No {kind === "internships" ? "internships" : "openings"} in the feed right now — check back soon,
          or switch tabs.
        </div>
      ) : (
        <div
          ref={scrollerRef}
          className="flex-1 snap-y snap-proximity overflow-y-auto overscroll-contain scroll-smooth"
        >
          {jobs.map((job, idx) => (
            <RailCard
              key={`${idx}-${job.id}`}
              job={job}
              focused={idx === focusIdx}
              expanded={expandedIdx === idx}
              onFocus={() => setFocusIdx(idx)}
              onToggle={() => setExpandedIdx((x) => (x === idx ? null : idx))}
              registerRef={(el) => registerCard(cardRefs, idx, el)}
            />
          ))}
          <div ref={sentinelRef} className="h-2" />
          {isFetchingNextPage && (
            <div className="flex justify-center py-4">
              <Loader2 className="h-4 w-4 animate-spin text-muted" aria-hidden="true" />
            </div>
          )}
        </div>
      )}

      <div className="flex items-center justify-between border-t border-border/60 px-3 py-1.5 text-[10px] text-muted">
        <span>↑ ↓ move · Enter expand · Esc close</span>
        {jobs.length > 0 && (
          <span className="tabular-nums">
            <CountUp value={focusIdx + 1} duration={350} /> / {jobs.length}+
          </span>
        )}
      </div>
    </motion.aside>,
    document.body,
  );
}
