"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useRef, useState } from "react";
import {
  AlertCircle,
  BarChart3,
  ChevronDown,
  Clock,
  FileCheck2,
  Gauge,
  MessageSquareText,
  Mic,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import { AnimatedBar } from "@/components/ui/animated-bar";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnswerAudioUrl, useInterviewReplay } from "@/hooks/use-interview";
import { useStaggerReveal } from "@/hooks/use-stagger-reveal";
import { cn, formatPercent } from "@/lib/utils";
import type { InterviewReplayItemOut, InterviewRoundSummaryOut } from "@/types/api";

function difficultyColor(difficulty: string): string {
  if (difficulty === "easy") return "var(--color-positive)";
  if (difficulty === "hard") return "var(--color-danger)";
  return "var(--color-warning)";
}

function RoundSummaryPanel({ summary }: { summary: InterviewRoundSummaryOut }) {
  const rollup = summary.communication_rollup;
  const tiersRef = useStaggerReveal<HTMLDivElement>(summary.overall_score, { delay: 100 });
  const statsRef = useStaggerReveal<HTMLDivElement>(summary.overall_score, { delay: 60 });
  return (
    <Card variant="glow-brand" className="animate-fade-up">
      <CardHeader>
        <CardTitle as="h2">Round summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-foreground">{summary.narrative_summary}</p>

        <div ref={tiersRef} className="grid gap-3 sm:grid-cols-3">
          {summary.difficulty_breakdown.map((tier) => (
            <div key={tier.difficulty} className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3">
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="capitalize text-muted">{tier.difficulty}</span>
                <span className="font-semibold text-foreground">{formatPercent(tier.average_score)}</span>
              </div>
              <AnimatedBar percent={tier.average_score ?? 0} color={difficultyColor(tier.difficulty)} trackClassName="bg-surface" />
              <p className="mt-1 text-[10px] text-muted">{tier.question_count} question{tier.question_count === 1 ? "" : "s"}</p>
            </div>
          ))}
        </div>

        <div ref={statsRef} className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            { label: "Filler words", value: formatPercent(rollup.average_filler_ratio) },
            { label: "Clarity", value: formatPercent(rollup.average_clarity_score) },
            { label: "Pace", value: rollup.average_speaking_rate_wpm ? `${Math.round(rollup.average_speaking_rate_wpm)} wpm` : "—" },
            { label: "Camera on", value: rollup.average_camera_on_ratio !== null ? formatPercent(rollup.average_camera_on_ratio) : "—" },
          ].map((s) => (
            <div key={s.label} className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-2 text-center">
              <p className="text-sm font-semibold text-foreground">{s.value}</p>
              <p className="text-[10px] text-muted">{s.label}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

const MARKER_STYLE: Record<string, { dot: string; badge: "positive" | "warning" | "danger" | "muted" }> = {
  strong_introduction: { dot: "bg-positive", badge: "positive" },
  strong_example: { dot: "bg-positive", badge: "positive" },
  excessive_filler_words: { dot: "bg-warning", badge: "warning" },
  unsupported_claim: { dot: "bg-warning", badge: "warning" },
  missing_conclusion: { dot: "bg-warning", badge: "warning" },
  technical_error: { dot: "bg-danger", badge: "danger" },
};

function ReplayTimeline({
  item,
  progressPercent,
  onSeek,
}: {
  item: InterviewReplayItemOut;
  progressPercent: number;
  onSeek: (percent: number) => void;
}) {
  const markers = item.evaluation?.timeline_markers ?? [];
  if (markers.length === 0) return null;
  return (
    <div className="space-y-2">
      <p className="flex items-center gap-1.5 text-xs font-medium text-foreground">
        <Clock className="h-3.5 w-3.5 text-muted" aria-hidden="true" /> Answer timeline
      </p>
      <div
        className="relative h-3 w-full cursor-pointer rounded-full bg-surface-muted"
        role="slider"
        aria-label="Seek answer timeline"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progressPercent)}
        tabIndex={0}
        onClick={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          onSeek(((e.clientX - rect.left) / rect.width) * 100);
        }}
      >
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-gradient-brand opacity-70"
          style={{ width: `${progressPercent}%`, transition: "width 100ms linear" }}
        />
        {markers.map((marker, i) => {
          const style = MARKER_STYLE[marker.type] ?? { dot: "bg-brand", badge: "muted" as const };
          return (
            <button
              key={i}
              type="button"
              title={marker.label}
              onClick={(e) => {
                e.stopPropagation();
                onSeek(marker.position_percent);
              }}
              className={cn(
                "absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-background transition-transform hover:scale-125",
                style.dot,
              )}
              style={{ left: `${marker.position_percent}%` }}
            />
          );
        })}
        <div
          className="absolute top-1/2 h-4 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-foreground shadow"
          style={{ left: `${progressPercent}%` }}
          aria-hidden="true"
        />
      </div>
      <ul className="flex flex-wrap gap-1.5">
        {markers.map((marker, i) => {
          const style = MARKER_STYLE[marker.type] ?? { dot: "bg-brand", badge: "muted" as const };
          return (
            <li key={i}>
              <button
                type="button"
                onClick={() => onSeek(marker.position_percent)}
                className="inline-flex"
              >
                <Badge variant={style.badge} className="cursor-pointer">
                  {marker.label}
                </Badge>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function CommunicationMetrics({ item }: { item: InterviewReplayItemOut }) {
  const metrics = item.evaluation?.communication_metrics;
  if (!metrics) return null;
  const stats: { label: string; value: string }[] = [
    { label: "Words", value: String(metrics.word_count) },
    { label: "Filler ratio", value: formatPercent(metrics.filler_ratio) },
    { label: "Speaking rate", value: metrics.speaking_rate_wpm ? `${Math.round(metrics.speaking_rate_wpm)} wpm` : "—" },
    { label: "Clarity", value: formatPercent(metrics.clarity_score) },
    { label: "Conciseness", value: formatPercent(metrics.conciseness_score) },
    { label: "Professionalism", value: formatPercent(metrics.professional_communication_score) },
    ...(metrics.camera_on_ratio !== null ? [{ label: "Camera on", value: formatPercent(metrics.camera_on_ratio) }] : []),
  ];
  return (
    <div className="space-y-2">
      <p className="flex items-center gap-1.5 text-xs font-medium text-foreground">
        <BarChart3 className="h-3.5 w-3.5 text-muted" aria-hidden="true" /> Communication metrics
      </p>
      <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
        {stats.map((s) => (
          <div key={s.label} className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-1.5 text-center">
            <p className="text-sm font-semibold text-foreground">{s.value}</p>
            <p className="text-[10px] text-muted">{s.label}</p>
          </div>
        ))}
      </div>
      {metrics.star_components_found.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {metrics.star_components_found.map((c) => (
            <Badge key={c} variant="outline">
              STAR: {c}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

function ReplayItem({ item, index }: { item: InterviewReplayItemOut; index: number }) {
  const audioUrl = useAnswerAudioUrl(item.answer.has_audio ? item.answer.id : null);
  const isVideo = item.answer.audio_mime_type?.startsWith("video/") ?? false;
  const evaluation = item.evaluation;
  const audioRef = useRef<HTMLAudioElement>(null);
  const [progressPercent, setProgressPercent] = useState(0);
  const [frameworkOpen, setFrameworkOpen] = useState(false);

  const handleSeek = (percent: number) => {
    const audio = audioRef.current;
    if (audio && audio.duration) {
      audio.currentTime = (percent / 100) * audio.duration;
      audio.play().catch(() => {});
    }
    setProgressPercent(percent);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="muted">Question {index + 1}</Badge>
          <Badge>{item.question.mode.replaceAll("_", " ")}</Badge>
          <Badge variant="outline" className="capitalize">{item.question.difficulty}</Badge>
          {item.question.is_follow_up && <Badge variant="positive">Follow-up</Badge>}
          {evaluation?.requires_human_review && (
            <Badge variant="warning" className="gap-1">
              <AlertCircle className="h-3 w-3" aria-hidden="true" /> Flagged for human review
            </Badge>
          )}
        </div>
        <CardTitle as="h2" className="text-base font-medium">{item.question.prompt}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {audioUrl && isVideo && (
          <video controls src={audioUrl} className="mx-auto max-h-64 w-full max-w-xs rounded-[var(--radius-md)] bg-black">
            Your browser does not support video playback.
          </video>
        )}
        {audioUrl && !isVideo && (
          <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-border bg-surface-muted p-2">
            <Mic className="h-4 w-4 shrink-0 text-brand" aria-hidden="true" />
            <audio
              ref={audioRef}
              controls
              src={audioUrl}
              className="w-full"
              onTimeUpdate={(e) => {
                const el = e.currentTarget;
                if (el.duration) setProgressPercent((el.currentTime / el.duration) * 100);
              }}
            >
              Your browser does not support audio playback.
            </audio>
          </div>
        )}

        <div>
          <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-foreground">
            <MessageSquareText className="h-3.5 w-3.5 text-muted" aria-hidden="true" />
            Transcript{" "}
            <span className="font-normal text-muted">
              (
              {item.answer.transcript_source === "typed"
                ? "typed answer"
                : item.answer.transcript_source === "deterministic_demo"
                  ? "deterministic demo transcription"
                  : item.answer.transcript_source === "browser_stt"
                    ? "live speech-to-text (transcribed in your browser as you spoke)"
                    : item.answer.transcript_source === "live_stt"
                      ? "live speech-to-text"
                      : "unavailable"}
              )
            </span>
          </p>
          <div className="relative overflow-hidden rounded-[var(--radius-md)] border border-border bg-surface-muted p-3">
            <p className="relative whitespace-pre-wrap text-sm text-foreground">{item.answer.transcript}</p>
          </div>
        </div>

        {item.question.model_answer_summary && (
          <div className="rounded-[var(--radius-md)] border border-brand-soft bg-brand-soft/30 p-3">
            <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-foreground">
              <FileCheck2 className="h-3.5 w-3.5 text-brand" aria-hidden="true" /> What a strong answer covers
            </p>
            <p className="text-sm text-foreground">{item.question.model_answer_summary}</p>
          </div>
        )}

        <ReplayTimeline item={item} progressPercent={progressPercent} onSeek={handleSeek} />

        {evaluation && (
          <>
            <CommunicationMetrics item={item} />

            <div>
              <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-foreground">
                <Gauge className="h-3.5 w-3.5 text-muted" aria-hidden="true" /> Dimension scores
              </p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {Object.entries(evaluation.dimension_scores).map(([dim, score]) => (
                  <div key={dim}>
                    <div className="mb-1 flex items-center justify-between text-xs text-muted">
                      <span className="capitalize">{dim.replaceAll("_", " ")}</span>
                      <span className="font-medium text-foreground">{(score * 100).toFixed(0)}%</span>
                    </div>
                    <Progress value={score * 100} aria-label={`${dim.replaceAll("_", " ")}: ${(score * 100).toFixed(0)}%`} />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs">
              <Badge variant="outline">Overall {formatPercent(evaluation.overall_score)}</Badge>
              <Badge variant="outline">Confidence {formatPercent(evaluation.confidence)}</Badge>
              {evaluation.agreement !== null && (
                <Badge variant="outline">Agent agreement {formatPercent(evaluation.agreement)}</Badge>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
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
            </div>

            {evaluation.evidence_checks.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-foreground">Resume-evidence verification</p>
                {evaluation.evidence_checks.map((check, i) => (
                  <div key={i} className="rounded-[var(--radius-md)] border border-border p-2 text-xs">
                    <Badge
                      variant={
                        check.classification === "supported_by_resume_evidence"
                          ? "positive"
                          : check.classification === "contradicted_by_uploaded_evidence" ||
                              check.classification === "not_currently_supported"
                            ? "warning"
                            : "muted"
                      }
                    >
                      {check.classification.replaceAll("_", " ")}
                    </Badge>
                    <p className="mt-1 text-muted">{check.explanation}</p>
                  </div>
                ))}
              </div>
            )}

            <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted">
              <button
                type="button"
                onClick={() => setFrameworkOpen((o) => !o)}
                className="flex w-full items-center justify-between gap-2 p-3 text-left text-xs font-medium text-foreground"
                aria-expanded={frameworkOpen}
              >
                <span className="flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-brand" aria-hidden="true" /> How to strengthen this answer
                </span>
                <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", frameworkOpen && "rotate-180")} aria-hidden="true" />
              </button>
              {frameworkOpen && (
                <p className="animate-fade-in border-t border-border p-3 text-xs text-muted">{evaluation.better_answer_framework}</p>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2 border-t border-border pt-3">
              {evaluation.care_execution_id && (
                <Link
                  href={`/trust-center?execution=${evaluation.care_execution_id}`}
                  className="inline-flex items-center gap-1 text-xs text-brand hover:underline"
                >
                  <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                  View full decision trace in Trust Center
                </Link>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function ReplayBody() {
  const params = useParams<{ sessionId: string }>();
  const { data, isLoading, isError, error, refetch } = useInterviewReplay(params.sessionId);
  const itemsRef = useStaggerReveal<HTMLDivElement>(data?.items.length, { delay: 90 });

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) {
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load this interview replay."} onRetry={() => refetch()} titleAs="h1" />;
  }
  if (data.items.length === 0) {
    return <EmptyState title="No answered questions in this interview yet" />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="animate-fade-up space-y-3">
        <h1 className="text-h1 text-foreground">Interview Replay</h1>
        <p className="text-sm text-muted">
          {data.session.mode.replaceAll("_", " ")} interview ·{" "}
          {data.session.overall_score !== null ? `overall ${formatPercent(data.session.overall_score)}` : "in progress"}
          {data.session.overall_confidence !== null && ` · confidence ${formatPercent(data.session.overall_confidence)}`}
        </p>
        <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-brand-soft bg-brand-soft/40 p-3 text-xs text-foreground">
          <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" aria-hidden="true" />
          <p>
            Each answer&apos;s score below reflects that single response — it is not your permanent Career Twin
            mastery. Evidence from strong, evidence-backed answers is what moves your{" "}
            <Link href="/career-twin" className="font-medium text-brand hover:underline">
              Career Twin
            </Link>{" "}
            over time, alongside everything else you&apos;ve submitted.
          </p>
        </div>
      </div>

      <RoundSummaryPanel summary={data.summary} />

      <div ref={itemsRef} className="space-y-6">
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
