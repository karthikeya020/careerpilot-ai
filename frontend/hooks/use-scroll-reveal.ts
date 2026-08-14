"use client";

import { useEffect, useRef } from "react";
import { animate, stagger } from "animejs";

/**
 * Fades/rises a container's direct children in, staggered, the first time
 * the container scrolls into view. Driven by IntersectionObserver (not
 * anime.js's own ScrollObserver threshold syntax) for predictable,
 * easy-to-reason-about trigger behavior across section heights.
 */
export function useScrollReveal<T extends HTMLElement>(options?: { delay?: number; y?: number }) {
  const ref = useRef<T>(null);
  const { delay = 80, y = 28 } = options ?? {};

  useEffect(() => {
    const el = ref.current;
    if (!el || el.children.length === 0) return;
    const children = Array.from(el.children) as HTMLElement[];
    // Hidden until the reveal fires -- avoids a flash of fully-visible
    // content before the observer's first callback.
    children.forEach((child) => {
      child.style.opacity = "0";
    });

    let animation: ReturnType<typeof animate> | null = null;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        animation = animate(children, {
          opacity: [0, 1],
          translateY: [y, 0],
          duration: 700,
          delay: stagger(delay),
          ease: "outQuad",
        });
        observer.disconnect();
      },
      { threshold: 0.1, rootMargin: "0px 0px -10% 0px" },
    );
    observer.observe(el);

    return () => {
      observer.disconnect();
      animation?.revert();
      children.forEach((child) => {
        child.style.opacity = "";
      });
    };
  }, [delay, y]);

  return ref;
}
