import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { getAccessToken } from "@/lib/token-store";
import type { InterviewMode, InterviewProgressOut, InterviewReplayOut } from "@/types/api";

export function useInterviewModes() {
  return useQuery({
    queryKey: ["interview-modes"],
    queryFn: () => api.get<string[]>("/interviews/modes"),
  });
}

interface StartInterviewInput {
  mode: InterviewMode;
  target_role_id?: string | null;
  job_description_id?: string | null;
  company_name?: string | null;
}

export function useStartInterview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: StartInterviewInput) => api.post<InterviewProgressOut>("/interviews/sessions", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useInterviewSession(sessionId: string | null) {
  return useQuery({
    queryKey: ["interview-session", sessionId],
    queryFn: () => api.get<InterviewProgressOut>(`/interviews/sessions/${sessionId}`),
    enabled: !!sessionId,
  });
}

interface SubmitAnswerInput {
  sessionId: string;
  questionId: string;
  typedAnswerText?: string;
  audioBlob?: Blob | null;
  audioDurationSeconds?: number;
  usedBrowserTranscription?: boolean;
  cameraOnRatio?: number | null;
}

export function useSubmitInterviewAnswer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      questionId,
      typedAnswerText,
      audioBlob,
      audioDurationSeconds,
      usedBrowserTranscription,
      cameraOnRatio,
    }: SubmitAnswerInput) => {
      const form = new FormData();
      form.append("question_id", questionId);
      if (typedAnswerText) form.append("typed_answer_text", typedAnswerText);
      if (audioDurationSeconds !== undefined) form.append("audio_duration_seconds", String(audioDurationSeconds));
      if (usedBrowserTranscription) form.append("used_browser_transcription", "true");
      if (cameraOnRatio !== undefined && cameraOnRatio !== null) form.append("camera_on_ratio", String(cameraOnRatio));
      if (audioBlob) form.append("audio", audioBlob, "answer.webm");
      return api.post<InterviewProgressOut>(`/interviews/sessions/${sessionId}/answers`, form, { isFormData: true });
    },
    onSuccess: (data) => {
      if (data.is_complete) {
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
        queryClient.invalidateQueries({ queryKey: ["career-twin"] });
        queryClient.invalidateQueries({ queryKey: ["trust-center"] });
      }
    },
  });
}

export function useInterviewReplay(sessionId: string | null) {
  return useQuery({
    queryKey: ["interview-replay", sessionId],
    queryFn: () => api.get<InterviewReplayOut>(`/interviews/sessions/${sessionId}/replay`),
    enabled: !!sessionId,
  });
}

// The audio-playback endpoint requires bearer auth, which a plain <audio src>
// can't send -- fetch it as an authenticated blob and hand back an object
// URL instead, revoking it on unmount to avoid leaking memory.
export function useAnswerAudioUrl(answerId: string | null): string | null {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!answerId) {
      return;
    }
    let objectUrl: string | null = null;
    let cancelled = false;
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
    const token = getAccessToken();

    fetch(`${base}/interviews/answers/${answerId}/audio`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      credentials: "include",
    })
      .then((res) => (res.ok ? res.blob() : null))
      .then((blob) => {
        if (cancelled || !blob) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => setUrl(null));

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [answerId]);

  return url;
}
