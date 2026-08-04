"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertTriangle, CheckCircle2, Mic, Square, ThumbsDown, ThumbsUp } from "lucide-react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useAudioRecorder } from "@/hooks/use-audio-recorder";
import { useInterviewSession, useSubmitInterviewAnswer } from "@/hooks/use-interview";
import { ApiError } from "@/lib/api-client";
import type { InterviewEvaluationOut, InterviewProgressOut, InterviewQuestionOut } from "@/types/api";

function EvidenceCheckBadge({ classification }: { classification: string }) {
  const variant =
    classification === "supported_by_resume_evidence"
      ? "positive"
      : classification === "not_currently_supported" || classification === "contradicted_by_uploaded_evidence"
        ? "warning"
        : "muted";
  return <Badge variant={variant}>{classification.replaceAll("_", " ")}</Badge>;
}

function EvaluationPanel({ evaluation }: { evaluation: InterviewEvaluationOut }) {
  return (
    <div className="space-y-4 rounded-[var(--radius-md)] border border-border bg-surface-muted p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-foreground">Evaluation</p>
        <div className="flex items-center gap-2 text-xs text-muted">
          <span>Overall {(evaluation.overall_score * 100).toFixed(0)}%</span>
          <span>&middot;</span>
          <span>Confidence {(evaluation.confidence * 100).toFixed(0)}%</span>
          {evaluation.agreement !== null && (
            <>
              <span>&middot;</span>
              <span>Agent agreement {(evaluation.agreement * 100).toFixed(0)}%</span>
            </>
          )}
        </div>
      </div>

      {evaluation.requires_human_review && (
        <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2 text-xs text-warning">
          <AlertTriangle className="h-4 w-4" aria-hidden="true" />
          CARE flagged this evaluation for human review due to persistently low confidence.
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {Object.entries(evaluation.dimension_scores).map(([dim, score]) => (
          <div key={dim}>
            <div className="mb-1 flex items-center justify-between text-xs text-muted">
              <span className="capitalize">{dim.replaceAll("_", " ")}</span>
              <span>{(score * 100).toFixed(0)}%</span>
            </div>
            <Progress value={score * 100} />
          </div>
        ))}
      </div>

      {evaluation.strengths.length > 0 && (
        <div>
          <p className="mb-1 flex items-center gap-1 text-xs font-medium text-positive">
            <ThumbsUp className="h-3.5 w-3.5" aria-hidden="true" /> Strengths
          </p>
          <ul className="list-inside list-disc space-y-0.5 text-xs text-foreground">
            {evaluation.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {evaluation.improvements.length > 0 && (
        <div>
          <p className="mb-1 flex items-center gap-1 text-xs font-medium text-warning">
            <ThumbsDown className="h-3.5 w-3.5" aria-hidden="true" /> Improve
          </p>
          <ul className="list-inside list-disc space-y-0.5 text-xs text-foreground">
            {evaluation.improvements.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {evaluation.evidence_checks.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs font-medium text-foreground">Resume-claim evidence check</p>
          {evaluation.evidence_checks.map((check, i) => (
            <div key={i} className="space-y-1 rounded border border-border p-2">
              <EvidenceCheckBadge classification={check.classification} />
              <p className="text-xs text-muted">{check.explanation}</p>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-muted">
        <span className="font-medium text-foreground">Better-answer framework: </span>
        {evaluation.better_answer_framework}
      </p>
    </div>
  );
}

function QuestionPanel({
  question,
  onSubmit,
  isSubmitting,
}: {
  question: InterviewQuestionOut;
  onSubmit: (typedText: string, audioBlob: Blob | null, durationSeconds: number) => void;
  isSubmitting: boolean;
}) {
  const [typedText, setTypedText] = useState("");
  const { status, audioBlob, durationSeconds, start, stop, reset } = useAudioRecorder();

  const canSubmit = typedText.trim().length > 0 || audioBlob !== null;

  const handleSubmit = () => {
    onSubmit(typedText.trim(), audioBlob, durationSeconds);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Badge variant="muted">{question.mode.replaceAll("_", " ")}</Badge>
      </div>
      <p className="text-sm font-medium text-foreground whitespace-pre-wrap">{question.prompt}</p>

      {status === "unsupported" ? (
        <p className="text-xs text-muted">Voice recording isn&apos;t supported in this browser -- use the typed answer below.</p>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          {status === "idle" || status === "permission_denied" ? (
            <Button type="button" variant="outline" size="sm" onClick={start}>
              <Mic className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" /> Record answer
            </Button>
          ) : status === "requesting_permission" ? (
            <Badge variant="muted">Requesting microphone permission...</Badge>
          ) : status === "recording" ? (
            <Button type="button" variant="destructive" size="sm" onClick={stop}>
              <Square className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" /> Stop recording
            </Button>
          ) : (
            <>
              <Badge variant="positive">Recorded {durationSeconds.toFixed(0)}s</Badge>
              <Button type="button" variant="outline" size="sm" onClick={reset}>
                Re-record
              </Button>
            </>
          )}
          {status === "permission_denied" && (
            <p className="text-xs text-warning">
              Microphone access was denied. Type your answer below instead -- it won&apos;t block your interview.
            </p>
          )}
        </div>
      )}

      <Textarea
        value={typedText}
        onChange={(e) => setTypedText(e.target.value)}
        placeholder="Type your answer (used as a fallback if the recording can't be transcribed, or as your primary answer)..."
        rows={5}
        aria-label="Your answer"
      />

      <Button onClick={handleSubmit} disabled={!canSubmit || isSubmitting}>
        {isSubmitting ? "Evaluating..." : "Submit answer"}
      </Button>
      {!canSubmit && <p className="text-xs text-muted">Record an answer or type one to continue.</p>}
    </div>
  );
}

function InterviewSessionBody() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const { data, isLoading, isError, error, refetch } = useInterviewSession(sessionId);
  const submitAnswer = useSubmitInterviewAnswer();
  const [localProgress, setLocalProgress] = useState<InterviewProgressOut | null>(null);
  const [answeredCount, setAnsweredCount] = useState(0);

  const progress = localProgress ?? data;

  const handleSubmit = (typedText: string, audioBlob: Blob | null, durationSeconds: number) => {
    if (!progress?.next_question) return;
    submitAnswer.mutate(
      {
        sessionId,
        questionId: progress.next_question.id,
        typedAnswerText: typedText || undefined,
        audioBlob,
        audioDurationSeconds: audioBlob ? durationSeconds : undefined,
      },
      {
        onSuccess: (result) => {
          setLocalProgress(result);
          setAnsweredCount((c) => c + 1);
          if (result.is_complete) {
            toast.success("Interview complete! Open Interview Replay to review everything.");
          }
        },
        onError: (err) => {
          toast.error(err instanceof ApiError ? err.message : "Couldn't submit your answer.");
        },
      }
    );
  };

  if (isLoading && !progress) return <Skeleton className="h-64" />;
  if (isError && !progress) {
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load this interview."} onRetry={() => refetch()} />;
  }
  if (!progress) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Mock interview</h1>
        <p className="mt-1 text-sm text-muted">
          {progress.session.mode.replaceAll("_", " ")} interview &middot; question {answeredCount + (progress.is_complete ? 0 : 1)}
        </p>
      </div>

      {progress.evaluation && <EvaluationPanel evaluation={progress.evaluation} />}

      <Card>
        <CardContent className="pt-6">
          {progress.is_complete || !progress.next_question ? (
            <div className="flex flex-col items-center gap-3 py-6 text-center">
              <CheckCircle2 className="h-10 w-10 text-positive" aria-hidden="true" />
              <p className="text-sm font-medium text-foreground">Interview complete</p>
              <p className="text-xs text-muted">
                Your answers were evaluated by CARE-routed specialist agents and recorded as Career Twin evidence
                where justified.
              </p>
              <div className="flex gap-2">
                <Button asChild size="sm">
                  <Link href={`/interview/${sessionId}/replay`}>Open Interview Replay</Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link href="/interview">Start another interview</Link>
                </Button>
              </div>
            </div>
          ) : (
            <QuestionPanel key={progress.next_question.id} question={progress.next_question} onSubmit={handleSubmit} isSubmitting={submitAnswer.isPending} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function InterviewSessionPage() {
  return (
    <Protected>
      <InterviewSessionBody />
    </Protected>
  );
}
