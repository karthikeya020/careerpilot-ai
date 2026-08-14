"use client";

import { useEffect, useRef, useState } from "react";
import { animate } from "animejs";

/**
 * Animates a numeric display value up (or down) to `target` whenever it
 * changes, via anime.js. Returns the live in-between value to render --
 * e.g. `useCountUp(0.73)` ticks a readiness percentage up from wherever it
 * last was instead of jumping straight to the new number.
 */
export function useCountUp(target: number | null | undefined, options?: { duration?: number; decimals?: number }): number {
  const { duration = 900, decimals = 0 } = options ?? {};
  const stateRef = useRef({ value: target ?? 0 });
  const [display, setDisplay] = useState(target ?? 0);

  useEffect(() => {
    if (target === null || target === undefined) return;
    const animation = animate(stateRef.current, {
      value: target,
      duration,
      ease: "outExpo",
      onUpdate: () => setDisplay(stateRef.current.value),
    });
    return () => {
      animation.revert();
    };
  }, [target, duration]);

  return decimals > 0 ? Number(display.toFixed(decimals)) : Math.round(display);
}
