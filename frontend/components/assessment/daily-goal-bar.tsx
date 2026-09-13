"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowRight, Check, Rocket, Sparkles, Target, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useDailyGoal, useSetDailyGoal } from "@/hooks/use-assessment";
import { cn } from "@/lib/utils";
import type { DifficultyBand } from "@/types/api";

const PLACEHOLDERS = [
  "I want to be placed in Microsoft",
  "Crack a data analyst role at Amazon",
  "Become a frontend engineer at Figma",
  "Land an SDE internship at Google",
  "Get into Goldman Sachs as a backend dev",
];

const DOT: Record<DifficultyBand, string> = {
  easy: "bg-positive",
  medium: "bg-warning",
  hard: "bg-danger",
};

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

/** Rotating typewriter placeholder -- types a phrase, holds, deletes, next.
 * Runs only while `active` and motion is allowed. */
function useTypewriter(active: boolean): string {
  const [text, setText] = useState("");
  const reduced = useReducedMotion();
  const state = useRef({ word: 0, char: 0, deleting: false });

  useEffect(() => {
    if (!active || reduced) return;
    let timer: ReturnType<typeof setTimeout>;
    const tick = () => {
      const s = state.current;
      const full = PLACEHOLDERS[s.word];
      if (!s.deleting) {
        s.char += 1;
        setText(full.slice(0, s.char));
        if (s.char >= full.length) {
          s.deleting = true;
          timer = setTimeout(tick, 1600);
          return;
        }
        timer = setTimeout(tick, 55);
      } else {
        s.char -= 1;
        setText(full.slice(0, Math.max(s.char, 0)));
        if (s.char <= 0) {
          s.deleting = false;
          s.word = (s.word + 1) % PLACEHOLDERS.length;
          timer = setTimeout(tick, 320);
          return;
        }
        timer = setTimeout(tick, 28);
      }
    };
    timer = setTimeout(tick, 1200);
    return () => clearTimeout(timer);
  }, [active, reduced]);

  return text || PLACEHOLDERS[0];
}

function ProgressDots({ done, total }: { done: number; total: number }) {
  return (
    <div className="flex items-center gap-1.5" aria-label={`${done} of ${total} practised today`}>
      {Array.from({ length: total }).map((_, i) => (
        <span
          key={i}
          className={cn(
            "h-2.5 w-2.5 rounded-full transition-all duration-500",
            i < done ? "bg-gradient-brand shadow-[var(--shadow-glow-brand)]" : "bg-surface-muted ring-1 ring-border",
          )}
        />
      ))}
    </div>
  );
}

export function DailyGoalBar({ onStart }: { onStart: (domainSlug: string) => void }) {
  const { data, isLoading } = useDailyGoal();
  const setGoal = useSetDailyGoal();
  const reduced = useReducedMotion();

  const [value, setValue] = useState("");
  const [focused, setFocused] = useState(false);
  const [burst, setBurst] = useState(false);
  const dirtyRef = useRef(false);

  // Keep the field in sync with the saved goal until the user edits it.
  useEffect(() => {
    if (!dirtyRef.current) setValue(data?.goal ?? "");
  }, [data?.goal]);

  const typed = useTypewriter(!focused && value.length === 0);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const next = value.trim();
    if (next === (data?.goal ?? "")) return;
    setGoal.mutate(next, {
      onSuccess: () => {
        dirtyRef.current = false;
        if (next && !reduced) {
          setBurst(true);
          setTimeout(() => setBurst(false), 700);
        }
      },
    });
  };

  const clear = () => {
    dirtyRef.current = false;
    setValue("");
    setGoal.mutate("");
  };

  const goal = data?.goal ?? null;

  return (
    <div className="mx-auto max-w-2xl">
      <style>{`
        @keyframes dgb-spark {
          0% { transform: translate(0,0) scale(0.4); opacity: 1; }
          100% { transform: translate(var(--dx), var(--dy)) scale(1); opacity: 0; }
        }
        .dgb-spark-piece { animation: dgb-spark 650ms cubic-bezier(0.22,1,0.36,1) forwards; }
      `}</style>

      <p className="mb-2 text-center text-[11px] font-medium uppercase tracking-[0.18em] text-muted">
        <Sparkles className="mr-1 inline h-3 w-3 text-brand" aria-hidden="true" />
        your north star
      </p>

      {isLoading ? (
        <Skeleton className="h-14 rounded-full" />
      ) : (
        <div
          className={cn(
            "border-glow-spin rounded-full transition-all duration-300",
            focused ? "shadow-[var(--shadow-glow-brand)]" : "shadow-lg",
          )}
        >
          <form
            role="search"
            onSubmit={submit}
            className={cn(
              "relative z-10 flex items-center gap-2 rounded-full border border-border bg-surface py-2 pl-4 pr-2 transition-transform",
              focused ? "scale-[1.015]" : "scale-100",
            )}
          >
            <Rocket
              className={cn("h-5 w-5 shrink-0 text-brand transition-transform", focused ? "-rotate-12 -translate-y-0.5" : "rotate-0")}
              aria-hidden="true"
            />
            <label htmlFor="daily-goal-input" className="sr-only">
              Your placement goal
            </label>
            <input
              id="daily-goal-input"
              value={value}
              onChange={(e) => {
                dirtyRef.current = true;
                setValue(e.target.value);
              }}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder={value.length === 0 && !focused ? `${typed} |` : "e.g. I want to be placed in Microsoft"}
              maxLength={200}
              autoComplete="off"
              className="min-w-0 flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted"
            />
            {goal && !setGoal.isPending && (
              <button
                type="button"
                onClick={clear}
                className="shrink-0 rounded-full p-1.5 text-muted transition-colors hover:bg-surface-muted hover:text-foreground"
                aria-label="Clear goal"
              >
                <X className="h-3.5 w-3.5" aria-hidden="true" />
              </button>
            )}
            <div className="relative shrink-0">
              <Button
                type="submit"
                size="sm"
                disabled={setGoal.isPending || value.trim() === (goal ?? "")}
                className="rounded-full bg-gradient-brand"
              >
                {setGoal.isPending ? "Saving…" : goal ? "Update" : "Set goal"}
                <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
              </Button>
              {burst && (
                <span className="pointer-events-none absolute inset-0 flex items-center justify-center" aria-hidden="true">
                  {[
                    { dx: "-26px", dy: "-20px" },
                    { dx: "22px", dy: "-24px" },
                    { dx: "28px", dy: "16px" },
                    { dx: "-24px", dy: "18px" },
                    { dx: "0px", dy: "-30px" },
                  ].map((p, i) => (
                    <span
                      key={i}
                      className="dgb-spark-piece absolute h-1.5 w-1.5 rounded-full bg-brand"
                      style={{ "--dx": p.dx, "--dy": p.dy } as React.CSSProperties}
                    />
                  ))}
                </span>
              )}
            </div>
          </form>
        </div>
      )}

      {!isLoading && !goal && (
        <p className="mt-2 text-center text-xs text-muted">
          Name a company or role and I&apos;ll line up{" "}
          <span className="font-semibold text-foreground">5 questions a day</span> to get you there.
        </p>
      )}

      {goal && data && (
        <div className="animate-fade-up mt-5 rounded-[var(--radius-xl)] border border-border bg-surface p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-brand" aria-hidden="true" />
                <span className="relative text-sm font-bold text-foreground">
                  Daily goal:
                  <svg
                    className="absolute -bottom-1 left-0 w-full text-brand"
                    viewBox="0 0 120 8"
                    fill="none"
                    aria-hidden="true"
                  >
                    <path
                      d="M2 5 Q 20 1, 38 5 T 74 5 T 118 4"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      className="animate-draw-line"
                      style={{ strokeDasharray: 130, "--line-length": 130 } as React.CSSProperties}
                    />
                  </svg>
                </span>
              </div>
              <p className="mt-1.5 truncate text-sm text-foreground">{goal}</p>
              {data.matched_domains.length > 0 && (
                <p className="mt-1 flex flex-wrap items-center gap-1 text-[11px] text-muted">
                  Tuned to:
                  {data.matched_domains.map((d) => (
                    <Badge key={d} variant="muted" className="text-[10px]">
                      {d}
                    </Badge>
                  ))}
                </p>
              )}
            </div>
            <div className="flex flex-col items-end gap-1">
              <ProgressDots done={data.completed_today} total={data.target_per_day} />
              <span className="text-[11px] tabular-nums text-muted">
                {data.completed_today} / {data.target_per_day} practised today
              </span>
            </div>
          </div>

          {data.completed_today >= data.target_per_day ? (
            <p className="mt-4 rounded-[var(--radius-md)] border border-positive/40 bg-positive/10 p-3 text-center text-xs font-medium text-foreground">
              🔥 Daily goal smashed. Come back tomorrow for a fresh set.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {data.questions.map((q) => (
                <li
                  key={q.question_id}
                  className={cn(
                    "flex items-start gap-3 rounded-[var(--radius-md)] border p-3 text-xs transition-colors",
                    q.done_today ? "border-positive/40 bg-positive/5" : "border-border",
                  )}
                >
                  {q.done_today ? (
                    <span
                      className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-positive text-white"
                      aria-hidden="true"
                    >
                      <Check className="h-2.5 w-2.5" />
                    </span>
                  ) : (
                    <span
                      className={cn("mt-1 h-2.5 w-2.5 shrink-0 rounded-full", DOT[q.difficulty_band])}
                      aria-hidden="true"
                    />
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex flex-wrap items-center gap-1.5">
                      <Badge variant="muted" className="text-[10px]">
                        {q.domain_name}
                      </Badge>
                      <span className="text-[10px] text-muted">{q.concept_name}</span>
                    </div>
                    <p className="line-clamp-2 text-foreground">{q.prompt}</p>
                  </div>
                  {!q.done_today && (
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      className="shrink-0"
                      onClick={() => onStart(q.domain_slug)}
                    >
                      Practise
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}

          <p className="mt-3 text-[10px] text-muted">
            Fresh set every day. Practising any question in a topic ticks it off.
          </p>
        </div>
      )}
    </div>
  );
}
