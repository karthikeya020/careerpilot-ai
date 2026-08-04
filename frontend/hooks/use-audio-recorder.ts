"use client";

import { useCallback, useRef, useState } from "react";

export type RecorderStatus =
  | "idle"
  | "requesting_permission"
  | "recording"
  | "stopped"
  | "permission_denied"
  | "unsupported";

/**
 * Browser audio recording with explicit permission-state handling. Never
 * throws on denial or an unsupported browser -- callers always have the
 * typed-answer textarea as a fallback (Prompt 3: never block the interview
 * on microphone/recording failure).
 */
export function useAudioRecorder() {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [durationSeconds, setDurationSeconds] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const startTimeRef = useRef(0);

  const start = useCallback(async () => {
    if (typeof window === "undefined" || !navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setStatus("unsupported");
      return;
    }
    setStatus("requesting_permission");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        setDurationSeconds((Date.now() - startTimeRef.current) / 1000);
        streamRef.current?.getTracks().forEach((track) => track.stop());
      };
      startTimeRef.current = Date.now();
      recorder.start();
      setStatus("recording");
    } catch {
      setStatus("permission_denied");
    }
  }, []);

  const stop = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setStatus("stopped");
  }, []);

  const reset = useCallback(() => {
    setAudioBlob(null);
    setDurationSeconds(0);
    setStatus("idle");
  }, []);

  return { status, audioBlob, durationSeconds, start, stop, reset };
}
