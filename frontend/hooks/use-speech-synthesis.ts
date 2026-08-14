"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Client-side text-to-speech via the Web Speech API's `speechSynthesis` --
 * same zero-key, zero-dependency philosophy as `useLiveTranscription`'s
 * `SpeechRecognition` use. Lets the AI interviewer speak its questions aloud
 * without any backend audio-generation dependency.
 */

function getSynth(): SpeechSynthesis | null {
  if (typeof window === "undefined") return null;
  return window.speechSynthesis ?? null;
}

export function useSpeechSynthesis() {
  const [supported] = useState(() => getSynth() !== null);
  const [speaking, setSpeaking] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const stop = useCallback(() => {
    const synth = getSynth();
    if (!synth) return;
    synth.cancel();
    setSpeaking(false);
  }, []);

  const speak = useCallback((text: string) => {
    const synth = getSynth();
    if (!synth || !text.trim()) return;
    // Cancel any in-flight utterance first -- overlapping speech from a
    // fast question transition would otherwise talk over itself.
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);

    utteranceRef.current = utterance;
    synth.speak(utterance);
  }, []);

  useEffect(() => {
    return () => {
      getSynth()?.cancel();
    };
  }, []);

  return { supported, speaking, speak, stop };
}
