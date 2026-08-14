"use client";

import { useState } from "react";
import { CheckCircle2, Loader2, Sparkles, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAnswerConceptPractice, useStartConceptPractice } from "@/hooks/use-graphrag";
import { cn } from "@/lib/utils";
import type { DifficultyBand, PracticeProgressOut } from "@/types/api";

const DIFFICULTY_STYLE: Record<DifficultyBand, { label: string; badge: "positive" | "warning" | "danger" }> = {
  easy: { label: "Easy", badge: "positive" },
  medium: { label: "Medium", badge: "warning" },
  hard: { label: "Hard", badge: "danger" },
};

export function ConceptPractice({
  conceptSlug,
  onCompleted,
}: {
  conceptSlug: string;
  onCompleted?: () => void;
}) {
  const startMutation = useStartConceptPractice();
  const answerMutation = useAnswerConceptPractice();
  const [progress, setProgress] = useState<PracticeProgressOut | null>(null);
  const [reveal, setReveal] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [text, setText] = useState("");

  const question = progress?.next_question ?? null;
  const isMultiSelect = question?.question_type === "multiple_selection";
  const isChoice = question?.question_type === "multiple_choice" || isMultiSelect;

  const handleStart = () => {
    startMutation.mutate(conceptSlug, {
      onSuccess: (data) => {
        setProgress(data);
        setReveal(false);
        setSelected([]);
        setText("");
      },
    });
  };

  const toggleOption = (optionId: string) => {
    if (isMultiSelect) {
      setSelected((prev) => (prev.includes(optionId) ? prev.filter((id) => id !== optionId) : [...prev, optionId]));
    } else {
      setSelected([optionId]);
    }
  };

  const handleSubmit = () => {
    if (!progress || !question) return;
    const payload = isChoice ? { selected_option_ids: selected } : { response_text: text };
    answerMutation.mutate(
      { conceptSlug, attemptId: progress.attempt_id, questionId: question.id, responsePayload: payload },
      {
        onSuccess: (data) => {
          setProgress(data);
          setReveal(true);
          setSelected([]);
          setText("");
          if (data.is_complete) onCompleted?.();
        },
      }
    );
  };

  const handleContinue = () => setReveal(false);

  if (!progress) {
    return (
      <Button onClick={handleStart} disabled={startMutation.isPending} size="sm">
        {startMutation.isPending ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> Loading...
          </>
        ) : (
          "Practice this concept"
        )}
      </Button>
    );
  }

  if (reveal) {
    return (
      <div className="animate-scale-in space-y-3 rounded-[var(--radius-md)] border border-border bg-surface p-3">
        <div
          className={cn(
            "flex items-center gap-2 rounded-[var(--radius-sm)] border p-2.5",
            progress.is_correct === true
              ? "border-positive/40 bg-positive/10"
              : progress.is_correct === false
                ? "border-warning/40 bg-warning/10"
                : "border-border bg-surface-muted",
          )}
        >
          {progress.is_correct === true ? (
            <CheckCircle2 className="h-5 w-5 shrink-0 text-positive" aria-hidden="true" />
          ) : progress.is_correct === false ? (
            <XCircle className="h-5 w-5 shrink-0 text-warning" aria-hidden="true" />
          ) : (
            <Sparkles className="h-5 w-5 shrink-0 text-brand" aria-hidden="true" />
          )}
          <p className="text-xs font-semibold text-foreground">
            {progress.is_correct === true ? "Correct!" : progress.is_correct === false ? "Not quite" : "Recorded"}
            {progress.score !== null && <span className="ml-1 font-normal text-muted">Score {Math.round(progress.score * 100)}%</span>}
          </p>
        </div>
        {progress.explanation && <p className="text-xs leading-relaxed text-muted">{progress.explanation}</p>}
        {progress.is_complete ? (
          <p className="flex items-center gap-1.5 text-xs font-medium text-brand">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" /> Practice complete -- this graph and your Career Twin now reflect it.
          </p>
        ) : (
          <Button onClick={handleContinue} size="sm" className="w-full">
            Next question ({progress.answered_in_concept}/{progress.total_in_concept})
          </Button>
        )}
      </div>
    );
  }

  if (!question) {
    return (
      <p className="flex items-center gap-1.5 text-xs font-medium text-brand">
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" /> You've answered every question available for this concept.
      </p>
    );
  }

  const style = DIFFICULTY_STYLE[question.difficulty_band];

  return (
    <div className="animate-fade-in space-y-3 rounded-[var(--radius-md)] border border-border bg-surface p-3">
      <div className="flex items-center justify-between gap-2">
        <Badge variant={style.badge}>{style.label}</Badge>
        <span className="text-[11px] text-muted">
          {progress.answered_in_concept}/{progress.total_in_concept} in this concept
        </span>
      </div>
      <p className="text-sm font-medium text-foreground whitespace-pre-wrap">{question.prompt}</p>

      {isChoice && question.options ? (
        <div className="space-y-1.5" role="group" aria-label="Answer options">
          {question.options.map((option) => (
            <label
              key={option.id}
              className={cn(
                "flex cursor-pointer items-center gap-2 rounded-[var(--radius-sm)] border p-2 text-xs transition-colors",
                selected.includes(option.id) ? "border-brand bg-brand-soft/60" : "border-border hover:bg-surface-muted",
              )}
            >
              <input
                type={isMultiSelect ? "checkbox" : "radio"}
                name={`practice-${conceptSlug}`}
                checked={selected.includes(option.id)}
                onChange={() => toggleOption(option.id)}
                className="h-3.5 w-3.5 accent-[var(--color-brand)]"
              />
              <span className="text-foreground">{option.text}</span>
            </label>
          ))}
        </div>
      ) : (
        <Textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Type your answer..." rows={3} aria-label="Your answer" />
      )}

      <Button
        onClick={handleSubmit}
        disabled={answerMutation.isPending || (isChoice ? selected.length === 0 : text.trim().length === 0)}
        size="sm"
        className="w-full"
      >
        {answerMutation.isPending ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" /> Grading...
          </>
        ) : (
          "Submit answer"
        )}
      </Button>
    </div>
  );
}
