"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  Brain,
  CheckCircle2,
  ChevronRight,
  Flame,
  ListChecks,
  Loader2,
  Network,
  Sparkles,
  Trophy,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { JobFxStyles, spotlightMove } from "@/components/ui/fx";
import { PageHeader } from "@/components/ui/page-header";
import { Progress } from "@/components/ui/progress";
import { Reveal } from "@/components/ui/reveal";
import { SectionHeader } from "@/components/ui/section";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { DailyGoalBar } from "@/components/assessment/daily-goal-bar";
import { LeetCodeProgressPanel } from "@/components/assessment/leetcode-progress-panel";
import { LeetCodeRecommendationsPanel } from "@/components/assessment/leetcode-recommendations-panel";
import { PracticeActivity } from "@/components/assessment/practice-activity";
import { useAssessmentDomains, useStartAttempt, useSubmitResponse } from "@/hooks/use-assessment";
import { ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";
import type { AssessmentDomainOut, AttemptProgressOut, DifficultyBand, QuestionOut, QuestionResponseOut } from "@/types/api";

const DIFFICULTY_STYLE: Record<DifficultyBand, { label: string; badge: "positive" | "warning" | "danger"; dot: string }> = {
  easy: { label: "Easy", badge: "positive", dot: "bg-positive" },
  medium: { label: "Medium", badge: "warning", dot: "bg-warning" },
  hard: { label: "Hard", badge: "danger", dot: "bg-danger" },
};

function useElapsedSeconds(active: boolean): number {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    if (!active) return;
    const start = Date.now();
    const id = setInterval(() => setSeconds(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => clearInterval(id);
  }, [active]);
  return seconds;
}

function DomainCard({
  domain,
  onStart,
  isStarting,
}: {
  domain: AssessmentDomainOut;
  onStart: (slug: string) => void;
  isStarting: boolean;
}) {
  return (
    <div
      onMouseMove={spotlightMove}
      className="js-card ds-panel ds-raise group relative flex flex-col overflow-hidden p-5"
    >
      <span className="js-spot" aria-hidden="true" />
      {domain.recommended && (
        <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-brand" aria-hidden="true" />
      )}
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-base font-semibold tracking-tight text-foreground">{domain.name}</h3>
        <Badge variant="muted">{domain.question_count} Qs</Badge>
      </div>
      <p className="mt-1.5 text-sm leading-relaxed text-muted">{domain.description}</p>

      <div className="mt-auto space-y-2.5 pt-4">
        {domain.recommended && domain.matched_skills.length > 0 && (
          <p className="flex items-start gap-1.5 text-[11px] text-brand">
            <Sparkles className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
            Recommended from your resume: {domain.matched_skills.join(", ")}
          </p>
        )}
        <Button
          onClick={() => onStart(domain.slug)}
          disabled={isStarting}
          className="ds-press w-full"
          size="sm"
        >
          Start practicing
          <ChevronRight
            className="h-3.5 w-3.5 transition-transform duration-200 ease-out group-hover:translate-x-0.5"
            aria-hidden="true"
          />
        </Button>
      </div>
    </div>
  );
}

function QuestionForm({
  question,
  onSubmit,
  isSubmitting,
  sessionStreak,
  answeredInDomain,
  totalInDomain,
}: {
  question: QuestionOut;
  onSubmit: (payload: Record<string, unknown>, timeSpentSeconds: number) => void;
  isSubmitting: boolean;
  sessionStreak: number;
  answeredInDomain: number;
  totalInDomain: number;
}) {
  const isMultiSelect = question.question_type === "multiple_selection";
  const isChoice = question.question_type === "multiple_choice" || isMultiSelect;
  const [selected, setSelected] = useState<string[]>([]);
  const [text, setText] = useState("");
  const elapsed = useElapsedSeconds(true);

  const toggleOption = (optionId: string) => {
    if (isMultiSelect) {
      setSelected((prev) => (prev.includes(optionId) ? prev.filter((id) => id !== optionId) : [...prev, optionId]));
    } else {
      setSelected([optionId]);
    }
  };

  const handleSubmit = () => {
    const payload = isChoice ? { selected_option_ids: selected } : { response_text: text };
    onSubmit(payload, elapsed);
  };

  const style = DIFFICULTY_STYLE[question.difficulty_band];
  const progressPercent = totalInDomain > 0 ? (answeredInDomain / totalInDomain) * 100 : 0;

  return (
    <div className="space-y-4">
      <div className="space-y-1.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <Badge variant="muted">{question.concept_name}</Badge>
            <Badge variant={style.badge} className="gap-1">
              <span className={cn("h-1.5 w-1.5 rounded-full", style.dot)} aria-hidden="true" />
              {style.label}
            </Badge>
          </div>
          {sessionStreak >= 2 && (
            <Badge variant="warning" className="animate-fade-in gap-1">
              <Flame className="h-3 w-3" aria-hidden="true" /> {sessionStreak} in a row
            </Badge>
          )}
        </div>
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px] text-muted">
            <span>
              {answeredInDomain} / {totalInDomain} questions in this topic
            </span>
            <span className="font-mono tabular-nums">{elapsed}s</span>
          </div>
          <Progress value={progressPercent} aria-label={`${answeredInDomain} of ${totalInDomain} questions answered`} />
        </div>
      </div>

      <p className="text-sm font-medium leading-relaxed text-foreground whitespace-pre-wrap">{question.prompt}</p>

      {isChoice && question.options ? (
        <div className="space-y-2" role="group" aria-label="Answer options">
          {question.options.map((option) => (
            <label
              key={option.id}
              className={cn(
                "flex cursor-pointer items-center gap-2 rounded-[var(--radius-md)] border p-3 text-sm transition-all duration-150 ease-out active:scale-[0.99]",
                selected.includes(option.id)
                  ? "border-brand bg-brand-soft/60"
                  : "border-border hover:border-brand/40 hover:bg-surface-muted",
              )}
            >
              <input
                type={isMultiSelect ? "checkbox" : "radio"}
                name="option"
                checked={selected.includes(option.id)}
                onChange={() => toggleOption(option.id)}
                className="h-4 w-4 accent-[var(--color-brand)]"
              />
              <span className="text-foreground">{option.text}</span>
            </label>
          ))}
        </div>
      ) : (
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Type your answer..."
          rows={4}
          aria-label="Your answer"
        />
      )}

      <Button
        onClick={handleSubmit}
        disabled={isSubmitting || (isChoice ? selected.length === 0 : text.trim().length === 0)}
        size="lg"
        className="ds-press"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Grading...
          </>
        ) : (
          "Submit answer"
        )}
      </Button>
    </div>
  );
}

function ResultReveal({
  response,
  domainExhausted,
  onContinue,
}: {
  response: QuestionResponseOut;
  domainExhausted: boolean;
  onContinue: () => void;
}) {
  const isCorrect = response.is_correct;
  return (
    <div className="animate-scale-in space-y-4">
      <div
        className={cn(
          "flex items-center gap-3 rounded-[var(--radius-lg)] border p-4",
          isCorrect === true
            ? "border-positive/40 bg-positive/10"
            : isCorrect === false
              ? "border-warning/40 bg-warning/10"
              : "border-border bg-surface-muted",
        )}
      >
        {isCorrect === true ? (
          <CheckCircle2 className="h-7 w-7 shrink-0 text-positive" aria-hidden="true" />
        ) : isCorrect === false ? (
          <XCircle className="h-7 w-7 shrink-0 text-warning" aria-hidden="true" />
        ) : (
          <Sparkles className="h-7 w-7 shrink-0 text-brand" aria-hidden="true" />
        )}
        <div>
          <p className="text-sm font-semibold text-foreground">
            {isCorrect === true ? "Correct!" : isCorrect === false ? "Not quite" : "Recorded for review"}
          </p>
          {response.score !== null && <p className="text-xs text-muted">Score: {Math.round(response.score * 100)}%</p>}
        </div>
      </div>

      {response.explanation && (
        <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3">
          <p className="mb-1 text-xs font-medium text-foreground">Explanation</p>
          <p className="text-xs leading-relaxed text-muted">{response.explanation}</p>
        </div>
      )}

      {isCorrect === false && (
        <Button variant="outline" size="sm" className="ds-press" asChild>
          <Link href={`/graphrag?question=${response.question_id}`}>
            <Network className="h-3.5 w-3.5" /> See root cause in GraphRAG
          </Link>
        </Button>
      )}

      <Button onClick={onContinue} size="lg" className="ds-press w-full">
        {domainExhausted ? "See results" : "Next question"}
      </Button>
    </div>
  );
}

function AssessmentHome({ onStart, isStarting }: { onStart: (slug: string) => void; isStarting: boolean }) {
  const { data: domains, isLoading, isError, error, refetch } = useAssessmentDomains();

  const recommended = domains?.filter((d) => d.recommended) ?? [];
  const others = domains?.filter((d) => !d.recommended) ?? [];

  return (
    <div className="mx-auto max-w-5xl space-y-10">
      <JobFxStyles />

      <Reveal>
        <PageHeader
          icon={Brain}
          eyebrow="Practice"
          title="Assessment Arena"
          description="Questions picked from your actual resume skills, ranked easy to hard, never repeated. Every answer becomes real, evidence-backed Career Twin proficiency."
        />
      </Reveal>

      <Reveal delay={60}>
        <DailyGoalBar onStart={onStart} />
      </Reveal>

      {isLoading ? (
        <Skeleton className="h-40" />
      ) : isError ? (
        <ErrorState message={error instanceof Error ? error.message : "Couldn't load assessment topics."} onRetry={() => refetch()} />
      ) : !domains || domains.length === 0 ? (
        <EmptyState title="No assessment topics available" />
      ) : (
        <>
          {recommended.length > 0 && (
            <Reveal delay={90}>
              <section className="space-y-4">
                <SectionHeader eyebrow="Matched to your resume" title="Recommended for you" />
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {recommended.map((d, i) => (
                    <Reveal key={d.id} delay={i * 45}>
                      <DomainCard domain={d} onStart={onStart} isStarting={isStarting} />
                    </Reveal>
                  ))}
                </div>
              </section>
            </Reveal>
          )}
          <Reveal delay={90}>
            <section className="space-y-4">
              <SectionHeader title={recommended.length > 0 ? "All topics" : "Choose a topic"} />
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {(recommended.length > 0 ? others : domains).map((d, i) => (
                  <Reveal key={d.id} delay={i * 40}>
                    <DomainCard domain={d} onStart={onStart} isStarting={isStarting} />
                  </Reveal>
                ))}
              </div>
            </section>
          </Reveal>
        </>
      )}

      <Reveal delay={60}>
        <section className="space-y-4">
          <SectionHeader
            eyebrow="Activity"
            title={
              <span className="inline-flex items-center gap-1.5">
                <Activity className="h-4 w-4 text-brand" aria-hidden="true" /> Practice activity
              </span>
            }
            description="Every LeetCode problem you've marked complete from your practice plan."
          />
          <PracticeActivity />
        </section>
      </Reveal>

      <Reveal delay={60}>
        <LeetCodeProgressPanel />
      </Reveal>

      <Reveal delay={60}>
        <LeetCodeRecommendationsPanel />
      </Reveal>
    </div>
  );
}

function AssessmentBody() {
  const startAttempt = useStartAttempt();
  const submitResponse = useSubmitResponse();
  const [progress, setProgress] = useState<AttemptProgressOut | null>(null);
  const [revealOpen, setRevealOpen] = useState(false);
  const [sessionStreak, setSessionStreak] = useState(0);

  const handleStart = (domainSlug: string) => {
    startAttempt.mutate(domainSlug, {
      onSuccess: (data) => {
        setProgress(data);
        setSessionStreak(0);
      },
      onError: (err) => {
        toast.error(err instanceof ApiError ? err.message : "Couldn't start the assessment.");
      },
    });
  };

  const handleAnswer = (payload: Record<string, unknown>, timeSpentSeconds: number) => {
    if (!progress?.next_question) return;
    submitResponse.mutate(
      { attemptId: progress.attempt_id, questionId: progress.next_question.id, responsePayload: payload, timeSpentSeconds },
      {
        onSuccess: (data) => {
          setProgress(data);
          setRevealOpen(true);
          setSessionStreak((s) => (data.response?.is_correct ? s + 1 : 0));
          if (data.is_complete) {
            queueMicrotask(() => {
              if (data.domain_exhausted) {
                toast.success("You've answered every question in this topic! Career Twin updated.");
              } else {
                toast.success("Assessment complete! Your Career Twin has been updated.");
              }
            });
          }
        },
        onError: (err) => {
          toast.error(err instanceof ApiError ? err.message : "Couldn't submit your answer.");
        },
      }
    );
  };

  if (!progress) {
    return <AssessmentHome onStart={handleStart} isStarting={startAttempt.isPending} />;
  }

  return (
    <div className="animate-fade-up mx-auto max-w-2xl space-y-6">
      <div>
        <p className="ds-eyebrow mb-1">Session in progress</p>
        <h1 className="flex items-center gap-2 text-h2 text-foreground">
          <ListChecks className="h-5 w-5 text-brand" aria-hidden="true" />
          Assessment Arena
        </h1>
        <p className="mt-1 text-sm text-muted">
          An adaptive educational assessment prototype — not a psychometric evaluation.
        </p>
      </div>

      <Card className="ds-panel">
        <CardContent className="pt-6">
          {revealOpen && progress.response ? (
            <ResultReveal
              response={progress.response}
              domainExhausted={progress.domain_exhausted}
              onContinue={() => setRevealOpen(false)}
            />
          ) : progress.is_complete || !progress.next_question ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              {progress.domain_exhausted ? (
                <>
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
                    <Trophy className="h-7 w-7 text-brand-foreground" aria-hidden="true" />
                  </div>
                  <p className="text-h3 text-foreground">Topic mastered!</p>
                  <p className="max-w-sm text-xs text-muted">
                    You&apos;ve answered every question available in this topic. New questions get added over time — check
                    back soon, or practice a different topic now.
                  </p>
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-10 w-10 text-positive" aria-hidden="true" />
                  <p className="text-sm font-medium text-foreground">Assessment complete</p>
                  <p className="text-xs text-muted">
                    Your responses were recorded as evidence and your Career Twin has been updated.
                  </p>
                </>
              )}
              <Button variant="outline" size="sm" className="ds-press" onClick={() => setProgress(null)}>
                Back to Assessment Arena
              </Button>
            </div>
          ) : (
            <QuestionForm
              key={progress.next_question.id}
              question={progress.next_question}
              onSubmit={handleAnswer}
              isSubmitting={submitResponse.isPending}
              sessionStreak={sessionStreak}
              answeredInDomain={progress.answered_in_domain}
              totalInDomain={progress.total_in_domain}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AssessmentPage() {
  return (
    <Protected>
      <AssessmentBody />
    </Protected>
  );
}
