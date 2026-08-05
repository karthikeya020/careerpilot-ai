"use client";

import { useState } from "react";
import { CheckCircle2, ListChecks } from "lucide-react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useAssessmentDomains, useStartAttempt, useSubmitResponse } from "@/hooks/use-assessment";
import { ApiError } from "@/lib/api-client";
import type { AttemptProgressOut, QuestionOut } from "@/types/api";

function QuestionForm({
  question,
  onSubmit,
  isSubmitting,
}: {
  question: QuestionOut;
  onSubmit: (payload: Record<string, unknown>) => void;
  isSubmitting: boolean;
}) {
  const isMultiSelect = question.question_type === "multiple_selection";
  const isChoice = question.question_type === "multiple_choice" || isMultiSelect;
  const [selected, setSelected] = useState<string[]>([]);
  const [text, setText] = useState("");

  const toggleOption = (optionId: string) => {
    if (isMultiSelect) {
      setSelected((prev) => (prev.includes(optionId) ? prev.filter((id) => id !== optionId) : [...prev, optionId]));
    } else {
      setSelected([optionId]);
    }
  };

  const handleSubmit = () => {
    if (isChoice) {
      onSubmit({ selected_option_ids: selected });
    } else {
      onSubmit({ response_text: text });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Badge variant="muted">{question.concept_name}</Badge>
        <Badge variant="muted">Difficulty {question.difficulty}/5</Badge>
      </div>
      <p className="text-sm font-medium text-foreground whitespace-pre-wrap">{question.prompt}</p>

      {isChoice && question.options ? (
        <div className="space-y-2" role="group" aria-label="Answer options">
          {question.options.map((option) => (
            <label
              key={option.id}
              className="flex cursor-pointer items-center gap-2 rounded-[var(--radius-md)] border border-border p-3 text-sm hover:bg-surface-muted"
            >
              <input
                type={isMultiSelect ? "checkbox" : "radio"}
                name="option"
                checked={selected.includes(option.id)}
                onChange={() => toggleOption(option.id)}
                className="h-4 w-4"
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
      >
        {isSubmitting ? "Submitting..." : "Submit answer"}
      </Button>
    </div>
  );
}

function AssessmentBody() {
  const { data: domains, isLoading, isError, error, refetch } = useAssessmentDomains();
  const startAttempt = useStartAttempt();
  const submitResponse = useSubmitResponse();
  const [progress, setProgress] = useState<AttemptProgressOut | null>(null);
  const [answeredCount, setAnsweredCount] = useState(0);

  const handleStart = (domainSlug: string) => {
    startAttempt.mutate(domainSlug, {
      onSuccess: (data) => {
        setProgress(data);
        setAnsweredCount(0);
      },
      onError: (err) => {
        toast.error(err instanceof ApiError ? err.message : "Couldn't start the assessment.");
      },
    });
  };

  const handleAnswer = (payload: Record<string, unknown>) => {
    if (!progress?.next_question) return;
    submitResponse.mutate(
      { attemptId: progress.attempt_id, questionId: progress.next_question.id, responsePayload: payload },
      {
        onSuccess: (data) => {
          setProgress(data);
          setAnsweredCount((c) => c + 1);
          if (data.is_complete) {
            toast.success("Assessment complete! Your Career Twin has been updated.");
          }
        },
        onError: (err) => {
          toast.error(err instanceof ApiError ? err.message : "Couldn't submit your answer.");
        },
      }
    );
  };

  if (progress) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
            <ListChecks className="h-5 w-5 text-brand" aria-hidden="true" />
            Adaptive assessment
          </h1>
          <p className="mt-1 text-sm text-muted">
            An adaptive educational assessment prototype -- not a psychometric evaluation. Question {answeredCount + 1}.
          </p>
        </div>
        <Card>
          <CardContent className="pt-6">
            {progress.is_complete || !progress.next_question ? (
              <div className="flex flex-col items-center gap-3 py-6 text-center">
                <CheckCircle2 className="h-10 w-10 text-positive" aria-hidden="true" />
                <p className="text-sm font-medium text-foreground">Assessment complete</p>
                <p className="text-xs text-muted">
                  Your responses were recorded as evidence and your Career Twin has been updated. Check the dashboard
                  or Trust Center to see what changed.
                </p>
                <Button variant="outline" size="sm" onClick={() => setProgress(null)}>
                  Take another assessment
                </Button>
              </div>
            ) : (
              <QuestionForm
                key={progress.next_question.id}
                question={progress.next_question}
                onSubmit={handleAnswer}
                isSubmitting={submitResponse.isPending}
              />
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
          <ListChecks className="h-5 w-5 text-brand" aria-hidden="true" />
          Adaptive assessment
        </h1>
        <p className="mt-1 text-sm text-muted">
          Take a short adaptive assessment to build real technical-readiness evidence for your Career Twin.
        </p>
      </div>

      {isLoading ? (
        <Skeleton className="h-40" />
      ) : isError ? (
        <ErrorState message={error instanceof Error ? error.message : "Couldn't load assessment domains."} onRetry={() => refetch()} />
      ) : !domains || domains.length === 0 ? (
        <EmptyState title="No assessment domains available" />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {domains.map((domain) => (
            <Card key={domain.id}>
              <CardHeader>
                <CardTitle as="h2">{domain.name}</CardTitle>
                <CardDescription>{domain.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <Button onClick={() => handleStart(domain.slug)} disabled={startAttempt.isPending}>
                  {startAttempt.isPending ? "Starting..." : "Start assessment"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
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
