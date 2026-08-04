"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ShieldCheck } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnswerAudioUrl, useInterviewReplay } from "@/hooks/use-interview";
import type { InterviewReplayItemOut } from "@/types/api";

const MARKER_COLORS: Record<string, string> = {
  strong_introduction: "bg-positive",
  strong_example: "bg-positive",
  excessive_filler_words: "bg-warning",
  unsupported_claim: "bg-warning",
  missing_conclusion: "bg-warning",
  technical_error: "bg-danger",
};

function Timeline({ item }: { item: InterviewReplayItemOut }) {
  const markers = item.evaluation?.timeline_markers ?? [];
  if (markers.length === 0) return null;
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-foreground">Answer timeline</p>
      <div className="relative h-2 w-full rounded-full bg-surface-muted">
        {markers.map((marker, i) => (
          <div
            key={i}
            title={marker.label}
            className={`absolute top-0 h-2 w-2 -translate-x-1/2 rounded-full ${MARKER_COLORS[marker.type] ?? "bg-brand"}`}
            style={{ left: `${marker.position_percent}%` }}
          />
        ))}
      </div>
      <ul className="space-y-0.5 text-xs text-muted">
        {markers.map((marker, i) => (
          <li key={i}>
            <span className={`mr-1.5 inline-block h-2 w-2 rounded-full ${MARKER_COLORS[marker.type] ?? "bg-brand"}`} />
            {marker.label}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ReplayItem({ item, index }: { item: InterviewReplayItemOut; index: number }) {
  const audioUrl = useAnswerAudioUrl(item.answer.has_audio ? item.answer.id : null);
  const evaluation = item.evaluation;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Badge variant="muted">Question {index + 1}</Badge>
          <Badge variant="default">{item.question.mode.replaceAll("_", " ")}</Badge>
        </div>
        <CardTitle className="text-base font-medium">{item.question.prompt}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {audioUrl && (
          <audio controls src={audioUrl} className="w-full">
            Your browser does not support audio playback.
          </audio>
        )}

        <div>
          <p className="mb-1 text-xs font-medium text-foreground">
            Transcript{" "}
            <span className="font-normal text-muted">
              (
              {item.answer.transcript_source === "typed"
                ? "typed answer"
                : item.answer.transcript_source === "deterministic_demo"
                  ? "deterministic demo transcription"
                  : item.answer.transcript_source === "live_stt"
                    ? "live speech-to-text"
                    : "unavailable"}
              )
            </span>
          </p>
          <p className="whitespace-pre-wrap rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 text-sm text-foreground">
            {item.answer.transcript}
          </p>
        </div>

        <Timeline item={item} />

        {evaluation && (
          <>
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

            <div className="grid gap-3 sm:grid-cols-2">
              {evaluation.strengths.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-positive">Strengths</p>
                  <ul className="list-inside list-disc space-y-0.5 text-xs text-foreground">
                    {evaluation.strengths.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
              {evaluation.improvements.length > 0 && (
                <div>
                  <p className="mb-1 text-xs font-medium text-warning">Improve</p>
                  <ul className="list-inside list-disc space-y-0.5 text-xs text-foreground">
                    {evaluation.improvements.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {evaluation.evidence_checks.map((check, i) => (
              <div key={i} className="rounded border border-border p-2 text-xs">
                <Badge variant="muted">{check.classification.replaceAll("_", " ")}</Badge>
                <p className="mt-1 text-muted">{check.explanation}</p>
              </div>
            ))}

            <p className="text-xs text-muted">
              <span className="font-medium text-foreground">Better-answer framework: </span>
              {evaluation.better_answer_framework}
            </p>

            {evaluation.care_execution_id && (
              <Link
                href={`/trust-center?execution=${evaluation.care_execution_id}`}
                className="inline-flex items-center gap-1 text-xs text-brand hover:underline"
              >
                <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                View full decision trace in Trust Center
              </Link>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

function ReplayBody() {
  const params = useParams<{ sessionId: string }>();
  const { data, isLoading, isError, error, refetch } = useInterviewReplay(params.sessionId);

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) {
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load this interview replay."} onRetry={() => refetch()} />;
  }
  if (data.items.length === 0) {
    return <EmptyState title="No answered questions in this interview yet" />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Interview Replay</h1>
        <p className="mt-1 text-sm text-muted">
          {data.session.mode.replaceAll("_", " ")} interview &middot;{" "}
          {data.session.overall_score !== null ? `overall ${(data.session.overall_score * 100).toFixed(0)}%` : "in progress"}
          {data.session.overall_confidence !== null && ` · confidence ${(data.session.overall_confidence * 100).toFixed(0)}%`}
        </p>
      </div>
      <div className="space-y-6">
        {data.items.map((item, i) => (
          <ReplayItem key={item.answer.id} item={item} index={i} />
        ))}
      </div>
    </div>
  );
}

export default function InterviewReplayPage() {
  return (
    <Protected>
      <ReplayBody />
    </Protected>
  );
}
