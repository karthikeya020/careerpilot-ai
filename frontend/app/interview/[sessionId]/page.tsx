"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  Bot,
  Camera,
  CheckCircle2,
  Clock,
  Gauge,
  Mic,
  MicOff,
  Square,
  ThumbsDown,
  ThumbsUp,
  Type,
  Volume2,
  VolumeX,
  Zap,
} from "lucide-react";
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
import { useCountUp } from "@/hooks/use-count-up";
import { useInterviewSession, useSubmitInterviewAnswer } from "@/hooks/use-interview";
import { useLiveTranscription } from "@/hooks/use-live-transcription";
import { useSetCameraConsent, useStudentProfile } from "@/hooks/use-onboarding";
import { useStaggerReveal } from "@/hooks/use-stagger-reveal";
import { useSpeechSynthesis } from "@/hooks/use-speech-synthesis";
import { ApiError } from "@/lib/api-client";
import { cn, formatPercent, titleCase } from "@/lib/utils";
import type { InterviewEvaluationOut, InterviewProgressOut, InterviewQuestionOut } from "@/types/api";

const FILLER_PATTERN = /\b(um+|uh+|erm+|like|you know|sort of|kind of|basically|actually|i mean)\b/gi;

function countWords(text: string): number {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}

function useElapsedSeconds(active: boolean): number {
  const [seconds, setSeconds] = useState(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (!active) return;
    startRef.current = Date.now();
    setSeconds(0);
    const id = setInterval(() => {
      setSeconds(startRef.current ? (Date.now() - startRef.current) / 1000 : 0);
    }, 200);
    return () => clearInterval(id);
  }, [active]);

  return seconds;
}

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
  const metrics = evaluation.communication_metrics;
  const dimensionsRef = useStaggerReveal<HTMLDivElement>(evaluation, { delay: 80 });
  const overall = useCountUp(evaluation.overall_score * 100);
  const confidence = useCountUp(evaluation.confidence * 100);
  return (
    <Card variant="glow-brand" className="animate-scale-in relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-radial-brand opacity-30" aria-hidden="true" />
      <CardContent className="relative space-y-4 pt-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-semibold text-foreground">Evaluation</p>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <Badge className="gap-1">Overall {overall}%</Badge>
            <Badge variant="outline">Confidence {confidence}%</Badge>
            {evaluation.agreement !== null && (
              <Badge variant="muted">Agent agreement {(evaluation.agreement * 100).toFixed(0)}%</Badge>
            )}
          </div>
        </div>

        {evaluation.requires_human_review && (
          <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2 text-xs text-warning">
            <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
            CARE flagged this evaluation for human review due to persistently low confidence.
          </div>
        )}

        <div ref={dimensionsRef} className="grid grid-cols-2 gap-3 sm:grid-cols-3">
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

        {metrics && (
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
            {[
              { label: "Words", value: String(metrics.word_count) },
              { label: "Filler ratio", value: formatPercent(metrics.filler_ratio) },
              { label: "Pace", value: metrics.speaking_rate_wpm ? `${Math.round(metrics.speaking_rate_wpm)} wpm` : "—" },
              { label: "Clarity", value: formatPercent(metrics.clarity_score) },
              { label: "Conciseness", value: formatPercent(metrics.conciseness_score) },
              { label: "Professionalism", value: formatPercent(metrics.professional_communication_score) },
            ].map((s) => (
              <div key={s.label} className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-2 py-1.5 text-center">
                <p className="text-sm font-semibold text-foreground">{s.value}</p>
                <p className="text-[10px] text-muted">{s.label}</p>
              </div>
            ))}
          </div>
        )}

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
          <div className="space-y-1">
            <p className="text-xs font-medium text-foreground">Resume-claim evidence check</p>
            {evaluation.evidence_checks.map((check, i) => (
              <div key={i} className="space-y-1 rounded-[var(--radius-md)] border border-border bg-surface-muted p-2">
                <EvidenceCheckBadge classification={check.classification} />
                <p className="text-xs text-muted">{check.explanation}</p>
              </div>
            ))}
          </div>
        )}

        <p className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 text-xs text-muted">
          <span className="font-medium text-foreground">Better-answer framework: </span>
          {evaluation.better_answer_framework}
        </p>
      </CardContent>
    </Card>
  );
}

function AudioVisualizer({ levels, active }: { levels: number[]; active: boolean }) {
  return (
    <div className="flex h-12 items-end gap-[3px]" aria-hidden="true">
      {levels.map((level, i) => (
        <span
          key={i}
          className="w-1.5 rounded-full bg-gradient-brand transition-[height] duration-100 ease-out"
          style={{ height: `${Math.max(active ? 6 : 3, level * 100)}%`, opacity: active ? 1 : 0.35 }}
        />
      ))}
    </div>
  );
}

function formatClock(seconds: number): string {
  const mm = Math.floor(seconds / 60);
  const ss = Math.floor(seconds % 60);
  return `${mm}:${ss.toString().padStart(2, "0")}`;
}

function LiveCaption({ finalText, interimText, listening }: { finalText: string; interimText: string; listening: boolean }) {
  if (!listening && !finalText && !interimText) return null;
  return (
    <div className="animate-fade-in rounded-[var(--radius-md)] border border-brand-soft bg-brand-soft/30 p-3">
      <div className="mb-1.5 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-wide text-brand">
        {listening && (
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand opacity-60" aria-hidden="true" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-brand" aria-hidden="true" />
          </span>
        )}
        Live captions
      </div>
      <p className="min-h-[1.5em] text-sm leading-relaxed text-foreground">
        {finalText}
        {interimText && <span className="text-muted"> {interimText}</span>}
        {listening && <span className="animate-pulse-glow text-brand">▍</span>}
        {!finalText && !interimText && listening && <span className="text-muted">Listening for your answer…</span>}
      </p>
    </div>
  );
}

function CoachingStats({
  text,
  elapsedSeconds,
  showPace = true,
}: {
  text: string;
  elapsedSeconds: number;
  showPace?: boolean;
}) {
  const wordCount = countWords(text);
  const fillerCount = (text.match(FILLER_PATTERN) || []).length;
  const pace = showPace && elapsedSeconds >= 3 ? Math.round(wordCount / (elapsedSeconds / 60)) : null;

  if (wordCount === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5 text-[11px]" aria-live="polite">
      <Badge variant="outline" className="gap-1">
        <Type className="h-3 w-3" aria-hidden="true" /> {wordCount} word{wordCount === 1 ? "" : "s"}
      </Badge>
      <Badge variant={fillerCount > 3 ? "warning" : "outline"} className="gap-1">
        <Zap className="h-3 w-3" aria-hidden="true" /> {fillerCount} filler word{fillerCount === 1 ? "" : "s"}
      </Badge>
      {pace !== null && (
        <Badge variant={pace < 90 || pace > 170 ? "warning" : "outline"} className="gap-1">
          <Gauge className="h-3 w-3" aria-hidden="true" /> {pace} wpm
        </Badge>
      )}
    </div>
  );
}

function InterviewerPresence({ questionKey, speaking }: { questionKey: string; speaking: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative flex h-11 w-11 shrink-0 items-center justify-center">
        <span
          key={questionKey}
          className={cn(
            "absolute inset-0 rounded-full bg-gradient-brand opacity-50 blur-md",
            speaking && "animate-pulse-glow",
          )}
          aria-hidden="true"
        />
        <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
          <Bot className="h-[18px] w-[18px] text-brand-foreground" aria-hidden="true" />
        </span>
      </div>
      <div>
        <p className="text-xs font-semibold text-foreground">AI Interviewer</p>
        <p className="text-[11px] text-muted">CARE-routed specialist panel</p>
      </div>
    </div>
  );
}

function QuestionPanel({
  question,
  onSubmit,
  isSubmitting,
  muted,
  onToggleMuted,
  cameraEnabled,
}: {
  question: InterviewQuestionOut;
  onSubmit: (
    typedText: string,
    audioBlob: Blob | null,
    durationSeconds: number,
    usedBrowserTranscription: boolean,
    cameraOnRatio: number | null,
  ) => void;
  isSubmitting: boolean;
  muted: boolean;
  onToggleMuted: () => void;
  cameraEnabled: boolean;
}) {
  const [typedText, setTypedText] = useState("");
  const [manuallyEdited, setManuallyEdited] = useState(false);
  const recorder = useAudioRecorder({ video: cameraEnabled });
  const videoRef = useRef<HTMLVideoElement>(null);
  const speech = useLiveTranscription();
  const voice = useSpeechSynthesis();
  const autoFilledValueRef = useRef("");
  const elapsedSeconds = useElapsedSeconds(recorder.status === "recording");

  // QuestionPanel remounts per question (see `key={question.id}` at the call
  // site), so this fires exactly once per new question -- speaks it aloud
  // unless muted, and cancels if the student navigates away mid-question.
  useEffect(() => {
    if (!muted) voice.speak(question.prompt);
    return () => voice.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question.id]);

  const canSubmit = typedText.trim().length > 0 || recorder.audioBlob !== null;
  const isRecordingOrJustStopped = recorder.status === "recording" || recorder.status === "stopped";

  // Live-fill the answer box as speech is recognized -- this is the actual
  // fix for voice answers never reaching the evaluator: the backend has no
  // live transcription provider configured, so without this the recorded
  // audio always resolved to an empty, unusable transcript.
  useEffect(() => {
    if (!speech.supported || manuallyEdited || !isRecordingOrJustStopped) return;
    const combined = [speech.finalText, speech.interimText].filter(Boolean).join(" ").trim();
    if (!combined) return;
    autoFilledValueRef.current = combined;
    setTypedText(combined);
  }, [speech.finalText, speech.interimText, speech.supported, manuallyEdited, isRecordingOrJustStopped]);

  const handleStart = () => {
    setManuallyEdited(false);
    recorder.start();
    if (speech.supported) speech.start();
  };

  const handleStop = () => {
    recorder.stop();
    if (speech.supported) speech.stop();
  };

  const handleReRecord = () => {
    recorder.reset();
    speech.reset();
    autoFilledValueRef.current = "";
    setManuallyEdited(false);
    setTypedText("");
  };

  const handleTypedChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setTypedText(value);
    if (value !== autoFilledValueRef.current) setManuallyEdited(true);
  };

  // Pace only means something when the words on screen were actually spoken
  // during the timed recording window -- once the student hand-edits or
  // types instead, "words / recording seconds" stops measuring anything real.
  const isVoiceSourced = speech.supported && !manuallyEdited && speech.finalText.trim().length > 0;

  const handleSubmit = () => {
    const usedBrowserTranscription = isVoiceSourced && recorder.audioBlob !== null;
    onSubmit(typedText.trim(), recorder.audioBlob, recorder.durationSeconds, usedBrowserTranscription, recorder.cameraOnRatio);
  };

  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = recorder.stream;
  }, [recorder.stream]);

  if (isSubmitting) {
    return (
      <div className="flex flex-col items-center gap-4 py-10 text-center">
        <div className="relative flex h-16 w-16 items-center justify-center">
          <span className="absolute inset-0 animate-pulse-glow rounded-full bg-gradient-brand opacity-40 blur-lg" aria-hidden="true" />
          <Bot className="h-8 w-8 animate-float text-brand" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">CARE is routing your answer…</p>
          <p className="mt-1 text-xs text-muted">Specialist agents are evaluating dimension scores and evidence checks.</p>
        </div>
        <div className="h-1.5 w-48 overflow-hidden rounded-full bg-surface-muted">
          <div className="h-full w-1/3 animate-gradient bg-gradient-brand" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <InterviewerPresence questionKey={question.id} speaking={voice.speaking} />
        <div className="flex items-center gap-2">
          {question.is_follow_up && (
            <Badge variant="positive" title={question.follow_up_rationale ?? undefined}>
              Follow-up
            </Badge>
          )}
          <Badge variant="muted">{question.mode.replaceAll("_", " ")}</Badge>
          <Badge variant="outline" className="capitalize">{question.difficulty}</Badge>
          {voice.supported && (
            <Button
              type="button"
              variant="outline"
              size="icon"
              onClick={() => {
                voice.stop();
                onToggleMuted();
              }}
              aria-label={muted ? "Unmute interviewer voice" : "Mute interviewer voice"}
            >
              {muted ? <VolumeX className="h-3.5 w-3.5" aria-hidden="true" /> : <Volume2 className="h-3.5 w-3.5" aria-hidden="true" />}
            </Button>
          )}
        </div>
      </div>
      <p className="text-h3 whitespace-pre-wrap text-foreground">{question.prompt}</p>

      {cameraEnabled && (
        <div className="mx-auto aspect-video w-full max-w-[220px] overflow-hidden rounded-[var(--radius-md)] bg-black">
          <video ref={videoRef} autoPlay muted playsInline className="h-full w-full object-cover" />
        </div>
      )}

      {recorder.status === "unsupported" ? (
        <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 text-xs text-muted">
          <MicOff className="h-4 w-4 shrink-0" aria-hidden="true" />
          Voice recording isn&apos;t supported in this browser — use the typed answer below.
        </div>
      ) : (
        <div className="rounded-[var(--radius-lg)] border border-border bg-surface-muted/60 p-4">
          <div className="flex flex-wrap items-center gap-3">
            {recorder.status === "idle" ? (
              <Button type="button" variant="outline" size="sm" onClick={handleStart}>
                <Mic className="h-3.5 w-3.5" aria-hidden="true" /> Record answer
              </Button>
            ) : recorder.status === "requesting_permission" ? (
              <Badge variant="muted" className="gap-1.5">
                <span className="h-2 w-2 animate-pulse-glow rounded-full bg-brand" /> Requesting microphone permission…
              </Badge>
            ) : recorder.status === "recording" ? (
              <>
                <Button type="button" variant="destructive" size="sm" onClick={handleStop}>
                  <Square className="h-3.5 w-3.5" aria-hidden="true" /> Stop
                </Button>
                <span className="relative flex h-3 w-3">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-danger opacity-60" aria-hidden="true" />
                  <span className="relative inline-flex h-3 w-3 rounded-full bg-danger" aria-hidden="true" />
                </span>
                <span className="font-mono text-sm tabular-nums text-danger">{formatClock(elapsedSeconds)}</span>
              </>
            ) : recorder.status === "permission_denied" ? (
              <Button type="button" variant="outline" size="sm" onClick={handleStart}>
                <Mic className="h-3.5 w-3.5" aria-hidden="true" /> Try recording again
              </Button>
            ) : (
              <>
                <Badge variant="positive" className="gap-1">
                  <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> Recorded {recorder.durationSeconds.toFixed(0)}s
                </Badge>
                <Button type="button" variant="outline" size="sm" onClick={handleReRecord}>
                  Re-record
                </Button>
              </>
            )}
          </div>

          {(recorder.status === "recording" || recorder.status === "stopped") && (
            <div className="mt-3 space-y-3">
              <AudioVisualizer levels={recorder.levels} active={recorder.status === "recording"} />
              <LiveCaption finalText={speech.finalText} interimText={speech.interimText} listening={speech.listening} />
              <CoachingStats
                text={typedText}
                elapsedSeconds={elapsedSeconds || recorder.durationSeconds}
                showPace={isVoiceSourced}
              />
            </div>
          )}

          {recorder.status === "recording" && !speech.supported && (
            <p className="mt-3 flex items-start gap-2 text-xs text-warning">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              Live captions aren&apos;t available in this browser (works best in Chrome or Edge). Your voice is still
              recorded — type your answer below before submitting so it isn&apos;t lost.
            </p>
          )}

          {recorder.status === "permission_denied" && (
            <p className="mt-3 flex items-start gap-2 text-xs text-warning">
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              Microphone access was denied. Type your answer below instead — it won&apos;t block your interview.
            </p>
          )}
        </div>
      )}

      <div className="relative">
        <div className="mb-1.5 flex items-center justify-between gap-2">
          <p className="text-xs font-medium text-muted">
            {speech.supported && !manuallyEdited && speech.finalText.trim().length > 0
              ? "Answer (transcribed live from your voice — edit freely)"
              : "Typed answer"}
          </p>
          {!isRecordingOrJustStopped && <CoachingStats text={typedText} elapsedSeconds={0} showPace={false} />}
        </div>
        <Textarea
          value={typedText}
          onChange={handleTypedChange}
          placeholder="Type your answer (used as a fallback if the recording can't be transcribed, or as your primary answer)..."
          rows={5}
          aria-label="Your answer"
        />
      </div>

      <Button onClick={handleSubmit} disabled={!canSubmit || isSubmitting} size="lg">
        Submit answer
      </Button>
      {!canSubmit && <p className="text-xs text-muted">Record an answer or type one to continue.</p>}
    </div>
  );
}

function ReadyRoom({
  mode,
  cameraEnabled,
  onToggleCamera,
  onBegin,
}: {
  mode: string;
  cameraEnabled: boolean;
  onToggleCamera: (enabled: boolean) => void;
  onBegin: () => void;
}) {
  const preview = useAudioRecorder({ video: true });
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current) videoRef.current.srcObject = preview.stream;
  }, [preview.stream]);

  useEffect(() => {
    return () => {
      if (preview.status === "recording") preview.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleToggleCamera = () => {
    const next = !cameraEnabled;
    onToggleCamera(next);
    if (next) preview.start();
    else if (preview.status === "recording") preview.stop();
  };

  const handleBegin = () => {
    if (preview.status === "recording") preview.stop();
    onBegin();
  };

  return (
    <div className="mx-auto max-w-xl animate-fade-up">
      <Card variant="glow-brand">
        <CardContent className="space-y-6 pt-8">
          <div className="text-center">
            <span className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
              <Bot className="h-6 w-6 text-brand-foreground" aria-hidden="true" />
            </span>
            <p className="text-h2 text-foreground">Ready room</p>
            <p className="mt-1 text-sm text-muted">{mode === "dsa" ? "DSA" : titleCase(mode)} round</p>
          </div>

          <div className="flex items-center justify-center gap-4 rounded-[var(--radius-md)] border border-border bg-surface-muted px-4 py-3 text-xs text-muted">
            <span className="flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-brand" aria-hidden="true" /> 6 questions — 2 easy, 2 medium, 2 hard
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-brand" aria-hidden="true" /> ~15-20 min
            </span>
          </div>

          <div className="flex items-center justify-between gap-3 rounded-[var(--radius-md)] border border-border p-4">
            <div>
              <p className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                <Camera className="h-4 w-4" aria-hidden="true" /> Camera
              </p>
              <p className="mt-0.5 text-xs text-muted">
                Optional. Records video for your own self-review, plus an honest &quot;camera on&quot; delivery
                metric — never analyzed for emotion, attention, or confidence.
              </p>
            </div>
            <Button type="button" variant={cameraEnabled ? "destructive" : "outline"} size="sm" onClick={handleToggleCamera}>
              {cameraEnabled ? "Disable" : "Enable"}
            </Button>
          </div>

          {cameraEnabled && (
            <div className="mx-auto aspect-video w-full max-w-xs overflow-hidden rounded-[var(--radius-md)] bg-black">
              <video ref={videoRef} autoPlay muted playsInline className="h-full w-full object-cover" />
            </div>
          )}

          <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 text-xs text-muted">
            <Mic className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            You&apos;ll be asked to allow microphone access when you record your first answer. Typing is always
            available as a fallback.
          </div>

          <Button size="lg" className="w-full" onClick={handleBegin}>
            Begin round
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function InterviewSessionBody() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const { data, isLoading, isError, error, refetch } = useInterviewSession(sessionId);
  const submitAnswer = useSubmitInterviewAnswer();
  const { data: profile } = useStudentProfile();
  const setCameraConsent = useSetCameraConsent();
  const [localProgress, setLocalProgress] = useState<InterviewProgressOut | null>(null);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [muted, setMuted] = useState(false);
  const [hasEntered, setHasEntered] = useState(false);
  // null = no explicit choice made yet this visit, so it tracks the saved
  // profile setting live; once the student toggles it in the ready room,
  // the override takes over for the rest of the session.
  const [cameraOverride, setCameraOverride] = useState<boolean | null>(null);
  const cameraEnabled = cameraOverride ?? profile?.camera_consent ?? false;

  const progress = localProgress ?? data;

  const handleSubmit = (
    typedText: string,
    audioBlob: Blob | null,
    durationSeconds: number,
    usedBrowserTranscription: boolean,
    cameraOnRatio: number | null,
  ) => {
    if (!progress?.next_question) return;
    submitAnswer.mutate(
      {
        sessionId,
        questionId: progress.next_question.id,
        typedAnswerText: typedText || undefined,
        audioBlob,
        audioDurationSeconds: audioBlob ? durationSeconds : undefined,
        usedBrowserTranscription,
        cameraOnRatio,
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
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load this interview."} onRetry={() => refetch()} titleAs="h1" />;
  }
  if (!progress) return null;

  if (!hasEntered && !progress.is_complete) {
    return (
      <ReadyRoom
        mode={progress.session.mode}
        cameraEnabled={cameraEnabled}
        onToggleCamera={(enabled) => {
          setCameraOverride(enabled);
          setCameraConsent.mutate(enabled);
        }}
        onBegin={() => setHasEntered(true)}
      />
    );
  }

  const currentQuestionNumber = answeredCount + (progress.is_complete ? 0 : 1);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="animate-fade-up space-y-2">
        <h1 className="text-h1 text-foreground">Mock interview</h1>
        <div className="flex flex-wrap items-center gap-2">
          <Badge>{progress.session.mode.replaceAll("_", " ")}</Badge>
          {!progress.is_complete && <span className="text-sm text-muted">Question {currentQuestionNumber} of 6</span>}
        </div>
        {!progress.is_complete && (
          <div className="flex gap-1" aria-hidden="true">
            {Array.from({ length: Math.max(currentQuestionNumber, 6) }).map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1.5 flex-1 rounded-full transition-colors",
                  i < currentQuestionNumber - 1 ? "bg-brand" : i === currentQuestionNumber - 1 ? "bg-brand/50" : "bg-surface-muted",
                )}
              />
            ))}
          </div>
        )}
      </div>

      {progress.evaluation && <EvaluationPanel evaluation={progress.evaluation} />}

      <Card className="animate-fade-up delay-1">
        <CardContent className="pt-6">
          {progress.is_complete || !progress.next_question ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
                <CheckCircle2 className="h-7 w-7 text-brand-foreground" aria-hidden="true" />
              </div>
              <p className="text-h3 text-foreground">Interview complete</p>
              <p className="max-w-sm text-xs text-muted">
                Your answers were evaluated by CARE-routed specialist agents and recorded as Career Twin evidence
                where justified. Formula and confidence: {formatPercent(progress.session.overall_confidence)}.
              </p>
              <div className="flex flex-wrap justify-center gap-2 pt-1">
                <Button asChild size="sm">
                  <Link href={`/interview/${sessionId}/replay`}>Open Interview Replay</Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link href="/interview">Start another interview</Link>
                </Button>
              </div>
            </div>
          ) : (
            <QuestionPanel
              key={progress.next_question.id}
              question={progress.next_question}
              onSubmit={handleSubmit}
              isSubmitting={submitAnswer.isPending}
              muted={muted}
              onToggleMuted={() => setMuted((m) => !m)}
              cameraEnabled={cameraEnabled}
            />
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
