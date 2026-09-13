"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ArrowUpRight, Check, ExternalLink, Lightbulb, Loader2, Sparkles, TrendingUp, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalyzeCode, useLeetCodeAnalysis } from "@/hooks/use-leetcode-practice";
import { ApiError } from "@/lib/api-client";

const DIFF_BADGE: Record<string, "positive" | "warning" | "danger"> = {
  Easy: "positive",
  Medium: "warning",
  Hard: "danger",
};

const LANGUAGES = ["Python", "Java", "C++", "JavaScript", "Go", "Other"];

function problemUrl(slug: string) {
  return `https://leetcode.com/problems/${slug}/`;
}

export function ExplainModal({
  slug,
  title,
  difficulty,
  onClose,
}: {
  slug: string;
  title: string;
  difficulty?: string;
  onClose: () => void;
}) {
  const { data, isLoading } = useLeetCodeAnalysis(slug);
  const analyze = useAnalyzeCode(slug);
  const codeRef = useRef<HTMLTextAreaElement>(null);
  const langRef = useRef<HTMLSelectElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const [hasCode, setHasCode] = useState(false);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [onClose]);

  const review = data?.review ?? null;
  // Uncontrolled editor: it seeds from any previously-saved solution once the
  // analysis GET resolves, via `key` remount -- no setState-in-effect.
  const seedKey = data === undefined ? "loading" : data.code ? "seeded" : "empty";

  const runAnalyze = () => {
    const code = codeRef.current?.value ?? "";
    if (code.trim().length === 0) return;
    analyze.mutate({ code, language: langRef.current?.value ?? "Python" });
  };

  const modal = (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-foreground/30 p-4 backdrop-blur-[2px] sm:p-6"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`How to solve ${title}`}
        className="animate-scale-in mt-[5vh] flex max-h-[88vh] w-full max-w-2xl flex-col overflow-hidden rounded-[var(--radius-xl)] border border-border bg-surface shadow-2xl"
      >
        <div className="h-1 w-full bg-gradient-brand" aria-hidden="true" />
        <div className="flex items-start justify-between gap-3 border-b border-border px-5 py-3.5">
          <div className="flex min-w-0 items-center gap-2">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
              <Sparkles className="h-4 w-4 text-brand" aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <a
                href={problemUrl(slug)}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 truncate text-sm font-semibold text-foreground hover:text-brand hover:underline"
              >
                {title}
                <ExternalLink className="h-3 w-3 shrink-0" aria-hidden="true" />
              </a>
              {difficulty && (
                <Badge variant={DIFF_BADGE[difficulty] ?? "muted"} className="mt-0.5 text-[10px]">
                  {difficulty}
                </Badge>
              )}
            </div>
          </div>
          <button
            ref={closeRef}
            onClick={onClose}
            aria-label="Close"
            className="shrink-0 rounded-full p-1.5 text-muted transition-colors hover:bg-surface-muted hover:text-foreground"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <div className="flex-1 space-y-6 overflow-y-auto p-5">
          {isLoading ? (
            <Skeleton className="h-40" />
          ) : (
            <>
              <section>
                <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
                  <Lightbulb className="h-3.5 w-3.5 text-brand" aria-hidden="true" /> How to think to solve this
                </h3>
                <p className="rounded-[var(--radius-md)] border border-brand/20 bg-brand-soft/40 p-3 text-sm leading-relaxed text-foreground">
                  {data?.how_to_think}
                </p>
              </section>

              <section>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Explain how you solved it</h3>
                <div className="mb-2 flex items-center gap-2">
                  <label htmlFor="explain-lang" className="text-xs text-muted">
                    Language
                  </label>
                  <select
                    id="explain-lang"
                    ref={langRef}
                    key={`lang-${seedKey}`}
                    defaultValue={data?.language ?? "Python"}
                    className="h-8 rounded-[var(--radius-md)] border border-border bg-surface px-2 text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                  >
                    {LANGUAGES.map((l) => (
                      <option key={l} value={l}>
                        {l}
                      </option>
                    ))}
                  </select>
                </div>
                <textarea
                  ref={codeRef}
                  key={`code-${seedKey}`}
                  defaultValue={data?.code ?? ""}
                  onInput={(e) => setHasCode(e.currentTarget.value.trim().length > 0)}
                  placeholder="Paste or type your solution here…"
                  spellCheck={false}
                  rows={8}
                  className="w-full resize-y rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 font-mono text-xs text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                />
                {analyze.isError && (
                  <p className="mt-1 text-xs text-danger" role="alert">
                    {analyze.error instanceof ApiError ? analyze.error.message : "Couldn't analyse that. Try again."}
                  </p>
                )}
                <Button
                  onClick={runAnalyze}
                  disabled={analyze.isPending || (!hasCode && !data?.code)}
                  size="sm"
                  className="mt-2"
                >
                  {analyze.isPending ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> Analysing…
                    </>
                  ) : review ? (
                    "Re-analyse"
                  ) : (
                    "Explain"
                  )}
                </Button>
              </section>

              {review && (
                <section className="animate-fade-up space-y-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">Analysis</h3>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 text-center">
                      <p className="text-[10px] uppercase tracking-wide text-muted">Time complexity</p>
                      <p className="mt-1 font-mono text-lg font-bold text-foreground">{review.time_complexity || "—"}</p>
                    </div>
                    <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 text-center">
                      <p className="text-[10px] uppercase tracking-wide text-muted">Space complexity</p>
                      <p className="mt-1 font-mono text-lg font-bold text-foreground">{review.space_complexity || "—"}</p>
                    </div>
                  </div>
                  {review.complexity_explanation && (
                    <p className="text-xs leading-relaxed text-muted">{review.complexity_explanation}</p>
                  )}
                  {review.summary && <p className="text-sm leading-relaxed text-foreground">{review.summary}</p>}
                  {review.strengths.length > 0 && (
                    <div>
                      <p className="mb-1.5 text-xs font-semibold text-foreground">What&apos;s working</p>
                      <ul className="space-y-1">
                        {review.strengths.map((s, i) => (
                          <li key={i} className="flex gap-2 text-xs text-muted">
                            <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-positive" aria-hidden="true" />
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {review.improvements.length > 0 && (
                    <div>
                      <p className="mb-1.5 text-xs font-semibold text-foreground">How to improve</p>
                      <ul className="space-y-1">
                        {review.improvements.map((s, i) => (
                          <li key={i} className="flex gap-2 text-xs text-muted">
                            <TrendingUp className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" aria-hidden="true" />
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <p className="text-[10px] text-muted">
                    {review.ai_generated ? "AI-generated review." : "Static heuristic review — no AI key configured."}
                  </p>
                </section>
              )}

              {data && data.similar_problems.length > 0 && (
                <section>
                  <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Similar questions</h3>
                  <ul className="space-y-1.5">
                    {data.similar_problems.map((p) => (
                      <li key={p.slug}>
                        <a
                          href={p.url}
                          target="_blank"
                          rel="noreferrer"
                          className="group flex items-center justify-between gap-2 rounded-[var(--radius-md)] border border-border px-3 py-2 text-xs transition-colors hover:border-brand hover:bg-brand-soft/40"
                        >
                          <span className="flex items-center gap-1.5 truncate font-medium text-foreground">
                            {p.title}
                            <ArrowUpRight className="h-3 w-3 shrink-0 text-muted group-hover:text-brand" aria-hidden="true" />
                          </span>
                          <Badge variant={DIFF_BADGE[p.difficulty] ?? "muted"} className="shrink-0">
                            {p.difficulty}
                          </Badge>
                        </a>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );

  if (typeof document === "undefined") return null;
  return createPortal(modal, document.body);
}
