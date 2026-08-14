"use client";

import { useCallback, useRef, useState } from "react";

export type RecorderStatus =
  | "idle"
  | "requesting_permission"
  | "recording"
  | "stopped"
  | "permission_denied"
  | "unsupported";

const VISUALIZER_BARS = 24;
const CAMERA_SAMPLE_INTERVAL_MS = 1000;
const CAMERA_SAMPLE_SIZE = 16;
// Average luma below this (near-black) reads as a blocked/off camera rather
// than a dim room -- deliberately conservative so a normally-lit face never
// gets misread as "off."
const CAMERA_ON_LUMA_THRESHOLD = 12;

export interface UseAudioRecorderOptions {
  /** When true, also captures video: a live self-preview stream and a
   * combined audio+video recording, plus an honest, observable "camera on"
   * ratio computed from simple frame-brightness sampling -- never a face,
   * gaze, or attention claim (Constitution rule 8: no emotional-state
   * inference). Defaults to false, which is byte-for-byte the previous
   * audio-only behavior. */
  video?: boolean;
}

/**
 * Browser audio (and optionally video) recording with explicit
 * permission-state handling. Never throws on denial or an unsupported
 * browser -- callers always have the typed-answer textarea as a fallback
 * (Prompt 3: never block the interview on microphone/recording failure).
 */
export function useAudioRecorder(options: UseAudioRecorderOptions = {}) {
  const { video = false } = options;
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [durationSeconds, setDurationSeconds] = useState(0);
  const [levels, setLevels] = useState<number[]>(() => Array(VISUALIZER_BARS).fill(0));
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [cameraOnRatio, setCameraOnRatio] = useState<number | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const startTimeRef = useRef(0);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const sampleVideoRef = useRef<HTMLVideoElement | null>(null);
  const cameraSampleTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const cameraSamplesRef = useRef<{ on: number; total: number }>({ on: 0, total: 0 });

  const stopVisualizer = useCallback(() => {
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    audioCtxRef.current?.close().catch(() => {});
    audioCtxRef.current = null;
    analyserRef.current = null;
    setLevels(Array(VISUALIZER_BARS).fill(0));
  }, []);

  const runVisualizer = useCallback((mediaStream: MediaStream) => {
    try {
      const AudioCtx = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      const source = ctx.createMediaStreamSource(mediaStream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);
      audioCtxRef.current = ctx;
      analyserRef.current = analyser;
      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteFrequencyData(data);
        const step = Math.floor(data.length / VISUALIZER_BARS) || 1;
        const next: number[] = [];
        for (let i = 0; i < VISUALIZER_BARS; i++) {
          next.push(Math.min(1, (data[i * step] ?? 0) / 200));
        }
        setLevels(next);
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    } catch {
      // Visualizer is cosmetic; recording continues without it.
    }
  }, []);

  const stopCameraSampling = useCallback(() => {
    if (cameraSampleTimerRef.current !== null) clearInterval(cameraSampleTimerRef.current);
    cameraSampleTimerRef.current = null;
    sampleVideoRef.current?.pause();
    sampleVideoRef.current = null;
  }, []);

  // Periodically samples the raw video frame at a tiny resolution and
  // checks whether it's meaningfully lit (vs. blank/covered) -- a cheap,
  // honest "was the camera on and showing something" signal. No face
  // detection, no gaze estimation, no claim about attention.
  const runCameraSampling = useCallback((mediaStream: MediaStream) => {
    if (typeof document === "undefined") return;
    const videoEl = document.createElement("video");
    videoEl.muted = true;
    videoEl.playsInline = true;
    videoEl.srcObject = mediaStream;
    videoEl.play().catch(() => {});
    sampleVideoRef.current = videoEl;

    const canvas = document.createElement("canvas");
    canvas.width = CAMERA_SAMPLE_SIZE;
    canvas.height = CAMERA_SAMPLE_SIZE;
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;

    cameraSamplesRef.current = { on: 0, total: 0 };
    cameraSampleTimerRef.current = setInterval(() => {
      if (videoEl.readyState < 2) return;
      try {
        ctx.drawImage(videoEl, 0, 0, CAMERA_SAMPLE_SIZE, CAMERA_SAMPLE_SIZE);
        const { data } = ctx.getImageData(0, 0, CAMERA_SAMPLE_SIZE, CAMERA_SAMPLE_SIZE);
        let sum = 0;
        for (let i = 0; i < data.length; i += 4) {
          sum += 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
        }
        const averageLuma = sum / (data.length / 4);
        cameraSamplesRef.current.total += 1;
        if (averageLuma > CAMERA_ON_LUMA_THRESHOLD) cameraSamplesRef.current.on += 1;
      } catch {
        // Sampling is best-effort only; recording continues regardless.
      }
    }, CAMERA_SAMPLE_INTERVAL_MS);
  }, []);

  const start = useCallback(async () => {
    if (typeof window === "undefined" || !navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setStatus("unsupported");
      return;
    }
    setStatus("requesting_permission");
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video });
      streamRef.current = mediaStream;
      setStream(video ? mediaStream : null);
      chunksRef.current = [];
      const recorder = new MediaRecorder(mediaStream);
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: video ? "video/webm" : "audio/webm" });
        setAudioBlob(blob);
        setDurationSeconds((Date.now() - startTimeRef.current) / 1000);
        if (video) {
          const { on, total } = cameraSamplesRef.current;
          setCameraOnRatio(total > 0 ? on / total : null);
          stopCameraSampling();
        }
        streamRef.current?.getTracks().forEach((track) => track.stop());
        setStream(null);
        stopVisualizer();
      };
      startTimeRef.current = Date.now();
      recorder.start();
      setStatus("recording");
      runVisualizer(mediaStream);
      if (video) runCameraSampling(mediaStream);
    } catch {
      setStatus("permission_denied");
    }
  }, [runVisualizer, stopVisualizer, video, runCameraSampling, stopCameraSampling]);

  const stop = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    setStatus("stopped");
  }, []);

  const reset = useCallback(() => {
    setAudioBlob(null);
    setDurationSeconds(0);
    setCameraOnRatio(null);
    setStatus("idle");
    stopVisualizer();
    stopCameraSampling();
  }, [stopVisualizer, stopCameraSampling]);

  return { status, audioBlob, durationSeconds, levels, stream, cameraOnRatio, start, stop, reset };
}
