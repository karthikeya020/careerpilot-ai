"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * The app's single enter gesture: a short fade + rise as the element scrolls
 * into view, one-shot. Motion communicates "this just became relevant",
 * not decoration. Honours prefers-reduced-motion (handled in globals.css).
 */
export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      el.classList.add("is-in");
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          el.style.transitionDelay = `${delay}ms`;
          el.classList.add("is-in");
          io.disconnect();
        }
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [delay]);

  return (
    <div ref={ref} className={cn("ds-reveal", className)}>
      {children}
    </div>
  );
}
