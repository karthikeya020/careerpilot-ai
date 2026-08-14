"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Activity,
  BarChart3,
  Brain,
  CheckCircle2,
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ActivityHeatmap } from "@/components/assessment/activity-heatmap";
import { AssessmentAnalyticsPanel } from "@/components/assessment/analytics-panel";
import {
  useActivityCalendar,
  useActivityDay,
  useAssessmentAnalytics,
  useAssessmentDomains,
  useStartAttempt,
  useSubmitResponse,
} from "@/hooks/use-assessment";
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
  const startRef = useRef<number | null>(null);
  useEffect(() => {
    if (!active) return;
    startRef.current = Date.now();
    setSeconds(0);
    const id = setInterval(() => setSeconds(startRef.current ? Math.floor((Date.now() - startRef.current) / 1000) : 0), 1000);
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
    <Card interactive className="relative flex flex-col overflow-hidden">
      {domain.recommended && (
        <div className="absolute inset-x-0 top-0 h-1 bg-gradient-brand" aria-hidden="true" />
      )}
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle as="h3" className="text-base">
            {domain.name}
          </CardTitle>
          <Badge variant="muted">{domain.question_count} Qs</Badge>
        </div>
        <CardDescription>{domain.description}</CardDescription>
      </CardHeader>
      <CardContent className="mt-auto space-y-2.5">
        {domain.recommended && domain.matched_skills.length > 0 && (
          <p className="flex items-start gap-1.5 text-[11px] text-brand">
            <Sparkles className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
            Recommended from your resume: {domain.matched_skills.join(", ")}
          </p>
        )}
        <Button onClick={() => onStart(domain.slug)} disabled={isStarting} className="w-full" size="sm">
          Start practicing
        </Button>
      </CardContent>
    </Card>
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
                "flex cursor-pointer items-center gap-2 rounded-[var(--radius-md)] border p-3 text-sm transition-colors",
                selected.includes(option.id)
                  ? "border-brand bg-brand-soft/60"
                  : "border-border hover:bg-surface-muted",
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
        <Button variant="outline" size="sm" asChild>
          <Link href={`/graphrag?question=${response.question_id}`}>
            <Network className="h-3.5 w-3.5" /> See root cause in GraphRAG
          </Link>
        </Button>
      )}

      <Button onClick={onContinue} size="lg" className="w-full">
        {domainExhausted ? "See results" : "Next question"}
      </Button>
    </div>
  );
}

function DayDetailPanel({ date, onClose }: { date: string; onClose: () => void }) {
  const { data, isLoading } = useActivityDay(date);
  return (
    <Card className="animate-fade-up">
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle as="h3" className="text-sm">
          {new Date(`${date}T00:00:00`).toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric", year: "numeric" })}
        </CardTitle>
        <Button variant="ghost" size="sm" onClick={onClose}>
          Close
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-24" />
        ) : !data || data.length === 0 ? (
          <p className="text-xs text-muted">No questions solved this day.</p>
        ) : (
          <ul className="space-y-2">
            {data.map((item) => {
              const style = DIFFICULTY_STYLE[item.difficulty_band];
              return (
                <li
                  key={item.response_id}
                  className="flex items-start gap-2 rounded-[var(--radius-md)] border border-border p-2.5 text-xs"
                >
                  {item.is_correct === true ? (
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-positive" aria-hidden="true" />
                  ) : item.is_correct === false ? (
                    <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" aria-hidden="true" />
                  ) : (
                    <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" aria-hidden="true" />
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="mb-1 flex flex-wrap items-center gap-1.5">
                      <Badge variant="muted">{item.domain_name}</Badge>
                      <Badge variant={style.badge}>{style.label}</Badge>
                      <span className="text-[10px] text-muted">
                        {new Date(item.submitted_at).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <p className="truncate text-foreground">{item.prompt}</p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

function AssessmentHome({ onStart, isStarting }: { onStart: (slug: string) => void; isStarting: boolean }) {
  const { data: domains, isLoading, isError, error, refetch } = useAssessmentDomains();
  const year = new Date().getFullYear();
  const { data: activity } = useActivityCalendar(year);
  const { data: analytics } = useAssessmentAnalytics();
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const recommended = domains?.filter((d) => d.recommended) ?? [];
  const others = domains?.filter((d) => !d.recommended) ?? [];

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
            <Brain className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Assessment Arena</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Practice questions picked from your actual resume skills, ranked easy to hard, never repeated. Every
          answer builds real, evidence-backed Career Twin proficiency.
        </p>
      </div>

      {isLoading ? (
        <Skeleton className="h-40" />
      ) : isError ? (
        <ErrorState message={error instanceof Error ? error.message : "Couldn't load assessment topics."} onRetry={() => refetch()} />
      ) : !domains || domains.length === 0 ? (
        <EmptyState title="No assessment topics available" />
      ) : (
        <>
          {recommended.length > 0 && (
            <div className="space-y-3">
              <h2 className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
                <Sparkles className="h-4 w-4 text-brand" aria-hidden="true" /> Recommended for you
              </h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {recommended.map((d) => (
                  <DomainCard key={d.id} domain={d} onStart={onStart} isStarting={isStarting} />
                ))}
              </div>
            </div>
          )}
          <div className="space-y-3">
            <h2 className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
              <ListChecks className="h-4 w-4 text-muted" aria-hidden="true" />
              {recommended.length > 0 ? "All topics" : "Choose a topic"}
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {(recommended.length > 0 ? others : domains).map((d) => (
                <DomainCard key={d.id} domain={d} onStart={onStart} isStarting={isStarting} />
              ))}
            </div>
          </div>
        </>
      )}

      <Card>
        <CardHeader>
          <CardTitle as="h2" className="flex items-center gap-1.5 text-base">
            <Activity className="h-4 w-4 text-brand" aria-hidden="true" /> Practice activity
          </CardTitle>
          <CardDescription>Every day you practiced this year. Click a day to see exactly what you solved.</CardDescription>
        </CardHeader>
        <CardContent>
          <ActivityHeatmap year={year} data={activity ?? []} selectedDate={selectedDate} onSelectDay={setSelectedDate} />
        </CardContent>
      </Card>

      {selectedDate && <DayDetailPanel date={selectedDate} onClose={() => setSelectedDate(null)} />}

      {analytics && analytics.total_answered > 0 && (
        <Card>
          <CardHeader>
            <CardTitle as="h2" className="flex items-center gap-1.5 text-base">
              <BarChart3 className="h-4 w-4 text-brand" aria-hidden="true" /> Your results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AssessmentAnalyticsPanel analytics={analytics} />
          </CardContent>
        </Card>
      )}
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
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-h1 text-foreground">
          <ListChecks className="h-5 w-5 text-brand" aria-hidden="true" />
          Assessment Arena
        </h1>
        <p className="mt-1 text-sm text-muted">
          An adaptive educational assessment prototype — not a psychometric evaluation.
        </p>
      </div>

      <Card>
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
                    You've answered every question available in this topic. New questions get added over time — check
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
              <Button variant="outline" size="sm" onClick={() => setProgress(null)}>
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
