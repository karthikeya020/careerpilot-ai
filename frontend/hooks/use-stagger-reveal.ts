"use client";

import { useEffect, useRef } from "react";
import { animate, stagger } from "animejs";

/**
 * Animates a container's direct children in with a fade + rise + stagger,
 * replaying whenever `replayKey` changes (e.g. a new page's data has
 * loaded). Attach the returned ref to the container -- no per-child markup
 * needed.
 */
export function useStaggerReveal<T extends HTMLElement>(replayKey: unknown = true, options?: { delay?: number; y?: number }) {
  const ref = useRef<T>(null);
  const { delay = 60, y = 18 } = options ?? {};

  useEffect(() => {
    const el = ref.current;
    if (!el || el.children.length === 0) return;
    const animation = animate(el.children, {
      opacity: [0, 1],
      translateY: [y, 0],
      duration: 600,
      delay: stagger(delay),
      ease: "outQuad",
    });
    return () => {
      animation.revert();
    };
  }, [replayKey, delay, y]);

  return ref;
}
