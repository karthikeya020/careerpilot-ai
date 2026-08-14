"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Client-side live speech-to-text via the Web Speech API. This exists
 * because the backend's speech-to-text provider has no live adapter
 * configured in this deployment (no `SPEECH_TO_TEXT_API_KEY`) -- uploaded
 * audio always resolves to `transcript_source=unavailable` there. Running
 * recognition in-browser (Chrome/Edge) means voice answers are transcribed
 * for real, with zero backend dependency, and the student sees their words
 * appear as they speak.
 */

interface SpeechRecognitionResultLike {
  readonly isFinal: boolean;
  readonly length: number;
  [index: number]: { transcript: string; confidence: number };
}

interface SpeechRecognitionResultListLike {
  readonly length: number;
  [index: number]: SpeechRecognitionResultLike;
}

interface SpeechRecognitionEventLike extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultListLike;
}

interface SpeechRecognitionErrorEventLike extends Event {
  error: string;
}

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
}

type SpeechRecognitionCtor = new () => SpeechRecognitionInstance;

function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export function useLiveTranscription() {
  const [supported] = useState(() => getSpeechRecognitionCtor() !== null);
  const [listening, setListening] = useState(false);
  const [interimText, setInterimText] = useState("");
  const [finalText, setFinalText] = useState("");
  const [erroredSilently, setErroredSilently] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const finalTextRef = useRef("");
  const shouldRestartRef = useRef(false);

  const stop = useCallback(() => {
    shouldRestartRef.current = false;
    recognitionRef.current?.stop();
  }, []);

  const reset = useCallback(() => {
    finalTextRef.current = "";
    setFinalText("");
    setInterimText("");
    setErroredSilently(false);
  }, []);

  const start = useCallback(() => {
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) return;
    finalTextRef.current = "";
    setFinalText("");
    setInterimText("");
    setErroredSilently(false);

    const recognition = new Ctor();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcript = result[0]?.transcript ?? "";
        if (result.isFinal) {
          finalTextRef.current = `${finalTextRef.current} ${transcript}`.trim();
        } else {
          interim += transcript;
        }
      }
      setFinalText(finalTextRef.current);
      setInterimText(interim);
    };
    recognition.onerror = (event) => {
      // "no-speech" fires often during natural pauses -- not a real failure.
      if (event.error !== "no-speech") setErroredSilently(true);
    };
    recognition.onend = () => {
      // Chrome auto-stops recognition after ~60s of continuous listening;
      // restart transparently so a long answer doesn't silently go deaf.
      if (shouldRestartRef.current) {
        try {
          recognition.start();
          return;
        } catch {
          // fall through to reporting stopped
        }
      }
      setListening(false);
    };

    recognitionRef.current = recognition;
    shouldRestartRef.current = true;
    setListening(true);
    try {
      recognition.start();
    } catch {
      setListening(false);
      setErroredSilently(true);
    }
  }, []);

  useEffect(() => {
    return () => {
      shouldRestartRef.current = false;
      recognitionRef.current?.stop();
    };
  }, []);

  return { supported, listening, interimText, finalText, erroredSilently, start, stop, reset };
}
