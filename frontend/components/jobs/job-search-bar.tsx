"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, GraduationCap, Search, SlidersHorizontal, Wifi, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ClickSpark, Magnetic } from "@/components/ui/fx";
import { cn } from "@/lib/utils";
import type { LiveJobFilters } from "@/hooks/use-live-jobs";

export interface JobSearchState extends LiveJobFilters {
  raw: string;
}

const EMPTY: JobSearchState = { raw: "", q: "", sector: "", location: "", remote: false, skills: [], minPackage: 0 };

const PLACEHOLDERS = [
  "Amazon",
  "backend engineer",
  "data scientist at Databricks",
  "Stripe payments",
  "infrastructure Kubernetes",
  "frontend React",
];

const SECTORS = [
  { slug: "", label: "Any sector" },
  { slug: "faang", label: "FAANG / Big Tech" },
  { slug: "startup", label: "Startup" },
  { slug: "research", label: "Research" },
  { slug: "finance", label: "Finance" },
  { slug: "consulting", label: "Consulting" },
  { slug: "government", label: "Government" },
];

const PACKAGES = [
  { v: 0, label: "Any package" },
  { v: 10, label: "10+ LPA" },
  { v: 20, label: "20+ LPA" },
  { v: 30, label: "30+ LPA" },
  { v: 40, label: "40+ LPA" },
];

const SECTOR_WORDS: [RegExp, string][] = [
  [/\b(faang|big[\s-]?tech)\b/i, "faang"],
  [/\bstart[\s-]?ups?\b/i, "startup"],
  [/\bresearch\b/i, "research"],
  [/\b(gov(ernment|t)?|psu)\b/i, "government"],
  [/\bconsult(ing|ancy)?\b/i, "consulting"],
  [/\b(finance|fintech|bank(ing)?)\b/i, "finance"],
];

/** Pull sector / package hints out of free text; return the leftover query. */
function parseFreeText(raw: string): { q: string; sector: string; minPackage: number } {
  let rest = ` ${raw} `;
  let sector = "";
  for (const [re, slug] of SECTOR_WORDS) {
    if (re.test(rest)) {
      sector = slug;
      rest = rest.replace(re, " ");
    }
  }
  let minPackage = 0;
  const pkg = rest.match(/\b(\d{1,3})\s*\+?\s*(lpa|lakhs?)\b/i);
  if (pkg) {
    const n = Number(pkg[1]);
    if (n >= 5) minPackage = Math.min(40, Math.max(10, Math.floor(n / 10) * 10));
    rest = rest.replace(pkg[0], " ");
  }
  const q = rest.replace(/\b(at|in|for|jobs?|roles?|openings?)\b/gi, " ").replace(/\s+/g, " ").trim();
  return { q, sector, minPackage };
}

function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!mq) return;
    const sync = () => setReduced(mq.matches);
    sync();
    mq.addEventListener?.("change", sync);
    return () => mq.removeEventListener?.("change", sync);
  }, []);
  return reduced;
}

function useTypewriter(active: boolean): string {
  const [text, setText] = useState("");
  const reduced = useReducedMotion();
  const st = useRef({ w: 0, c: 0, del: false });
  useEffect(() => {
    if (!active || reduced) return;
    let timer: ReturnType<typeof setTimeout>;
    const tick = () => {
      const s = st.current;
      const full = PLACEHOLDERS[s.w];
      if (!s.del) {
        s.c += 1;
        setText(full.slice(0, s.c));
        if (s.c >= full.length) {
          s.del = true;
          timer = setTimeout(tick, 1500);
          return;
        }
        timer = setTimeout(tick, 60);
      } else {
        s.c -= 1;
        setText(full.slice(0, Math.max(s.c, 0)));
        if (s.c <= 0) {
          s.del = false;
          s.w = (s.w + 1) % PLACEHOLDERS.length;
          timer = setTimeout(tick, 300);
          return;
        }
        timer = setTimeout(tick, 26);
      }
    };
    timer = setTimeout(tick, 1100);
    return () => clearTimeout(timer);
  }, [active, reduced]);
  return text || PLACEHOLDERS[0];
}

export function JobSearchBar({ onSearch }: { onSearch: (s: JobSearchState) => void }) {
  const [text, setText] = useState("");
  const [sector, setSector] = useState("");
  const [location, setLocation] = useState("");
  const [remote, setRemote] = useState(false);
  const [minPackage, setMinPackage] = useState(0);
  const [skillsText, setSkillsText] = useState("");
  const [internshipsOnly, setInternshipsOnly] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [focused, setFocused] = useState(false);
  const typed = useTypewriter(!focused && text.length === 0);
  const debounce = useRef<ReturnType<typeof setTimeout> | null>(null);

  const state: JobSearchState = useMemo(() => {
    const parsed = parseFreeText(text);
    const skills = skillsText.split(",").map((s) => s.trim()).filter(Boolean);
    const raw = [
      text.trim(),
      sector,
      location.trim(),
      remote ? "remote" : "",
      minPackage ? `${minPackage}+LPA` : "",
      internshipsOnly ? "internships" : "",
      ...skills,
    ]
      .filter(Boolean)
      .join(" ");
    return {
      raw,
      q: parsed.q,
      sector: sector || parsed.sector,
      location: location.trim(),
      remote,
      skills,
      minPackage: minPackage || parsed.minPackage,
      kind: internshipsOnly ? "internships" : "all",
    };
  }, [text, sector, location, remote, minPackage, skillsText, internshipsOnly]);

  useEffect(() => {
    if (debounce.current) clearTimeout(debounce.current);
    debounce.current = setTimeout(() => onSearch(state), 320);
    return () => {
      if (debounce.current) clearTimeout(debounce.current);
    };
  }, [state, onSearch]);

  const clearAll = () => {
    setText("");
    setSector("");
    setLocation("");
    setRemote(false);
    setMinPackage(0);
    setSkillsText("");
    setInternshipsOnly(false);
    if (debounce.current) clearTimeout(debounce.current);
    onSearch(EMPTY);
  };

  const filterCount =
    (sector ? 1 : 0) +
    (location.trim() ? 1 : 0) +
    (remote ? 1 : 0) +
    (minPackage ? 1 : 0) +
    (skillsText.trim() ? 1 : 0) +
    (internshipsOnly ? 1 : 0);

  return (
    <div className="mx-auto max-w-2xl">
      <p className="mb-2 text-center text-[11px] font-medium uppercase tracking-[0.18em] text-muted">
        <Search className="mr-1 inline h-3 w-3 text-brand" aria-hidden="true" />
        find your role
      </p>
      <div
        className={cn(
          "border-glow-spin rounded-full transition-all duration-300",
          focused ? "shadow-[var(--shadow-glow-brand)]" : "shadow-lg",
        )}
      >
        <form
          role="search"
          onSubmit={(e) => {
            e.preventDefault();
            if (debounce.current) clearTimeout(debounce.current);
            onSearch(state);
          }}
          className={cn(
            "relative z-10 flex items-center gap-2 rounded-full border border-border bg-surface py-2 pl-4 pr-2 transition-transform",
            focused ? "scale-[1.015]" : "scale-100",
          )}
        >
          <Search
            className={cn("h-5 w-5 shrink-0 text-brand transition-transform", focused ? "-rotate-12" : "rotate-0")}
            aria-hidden="true"
          />
          <label htmlFor="job-search-input" className="sr-only">
            Search jobs
          </label>
          <input
            id="job-search-input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder={text.length === 0 && !focused ? `${typed} |` : "Company, role, skill — e.g. Amazon"}
            maxLength={120}
            autoComplete="off"
            className="min-w-0 flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted"
          />
          <button
            type="button"
            onClick={() => setShowFilters((s) => !s)}
            aria-label="Toggle filters"
            aria-pressed={showFilters}
            className={cn(
              "relative shrink-0 rounded-full p-1.5 transition-colors",
              showFilters || filterCount ? "bg-brand-soft text-brand" : "text-muted hover:bg-surface-muted hover:text-foreground",
            )}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" aria-hidden="true" />
            {filterCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-brand text-[8px] font-bold text-brand-foreground">
                {filterCount}
              </span>
            )}
          </button>
          {(text || filterCount > 0) && (
            <button
              type="button"
              onClick={clearAll}
              aria-label="Clear search"
              className="shrink-0 rounded-full p-1.5 text-muted transition-colors hover:bg-surface-muted hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" aria-hidden="true" />
            </button>
          )}
          <Magnetic strength={0.25} className="shrink-0">
            <ClickSpark>
              <Button type="submit" size="sm" className="rounded-full bg-gradient-brand">
                Search <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
              </Button>
            </ClickSpark>
          </Magnetic>
        </form>
      </div>

      {showFilters && (
        <div className="animate-fade-in mx-auto mt-3 grid max-w-2xl gap-2 rounded-[var(--radius-lg)] border border-border bg-surface p-3 sm:grid-cols-2">
          <div className="space-y-1">
            <label htmlFor="flt-sector" className="text-[11px] font-medium text-muted">Sector</label>
            <select
              id="flt-sector"
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="h-8 w-full rounded-[var(--radius-md)] border border-border bg-surface px-2 text-xs text-foreground"
            >
              {SECTORS.map((s) => (
                <option key={s.slug} value={s.slug}>{s.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label htmlFor="flt-location" className="text-[11px] font-medium text-muted">Location</label>
            <input
              id="flt-location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. New York, London, India"
              className="h-8 w-full rounded-[var(--radius-md)] border border-border bg-surface px-2 text-xs text-foreground placeholder:text-muted"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="flt-package" className="text-[11px] font-medium text-muted">Min package (best effort — from JD)</label>
            <select
              id="flt-package"
              value={minPackage}
              onChange={(e) => setMinPackage(Number(e.target.value))}
              className="h-8 w-full rounded-[var(--radius-md)] border border-border bg-surface px-2 text-xs text-foreground"
            >
              {PACKAGES.map((p) => (
                <option key={p.v} value={p.v}>{p.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label htmlFor="flt-skills" className="text-[11px] font-medium text-muted">Must have skills (comma-sep)</label>
            <input
              id="flt-skills"
              value={skillsText}
              onChange={(e) => setSkillsText(e.target.value)}
              placeholder="e.g. Python, Kubernetes"
              className="h-8 w-full rounded-[var(--radius-md)] border border-border bg-surface px-2 text-xs text-foreground placeholder:text-muted"
            />
          </div>
          <button
            type="button"
            onClick={() => setRemote((r) => !r)}
            aria-pressed={remote}
            className={cn(
              "flex h-8 items-center justify-center gap-1.5 rounded-[var(--radius-md)] border text-xs font-medium transition-colors",
              remote ? "border-brand bg-brand-soft text-brand" : "border-border text-muted hover:text-foreground",
            )}
          >
            <Wifi className="h-3.5 w-3.5" aria-hidden="true" /> {remote ? "Remote only" : "Remote only — off"}
          </button>
          <button
            type="button"
            onClick={() => setInternshipsOnly((v) => !v)}
            aria-pressed={internshipsOnly}
            className={cn(
              "flex h-8 items-center justify-center gap-1.5 rounded-[var(--radius-md)] border text-xs font-medium transition-colors",
              internshipsOnly ? "border-brand bg-brand-soft text-brand" : "border-border text-muted hover:text-foreground",
            )}
          >
            <GraduationCap className="h-3.5 w-3.5" aria-hidden="true" />{" "}
            {internshipsOnly ? "Internships only" : "Internships only — off"}
          </button>
        </div>
      )}
    </div>
  );
}
