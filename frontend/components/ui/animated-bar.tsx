"use client";

import { useEffect, useRef } from "react";
import { animate } from "animejs";
import { cn } from "@/lib/utils";

/**
 * A horizontal progress bar whose fill animates in via anime.js (spring-ish
 * ease, not a linear CSS transition) whenever `percent` changes. Drop-in
 * replacement for the CSS-transition bar pattern repeated across the app.
 */
export function AnimatedBar({
  percent,
  color = "var(--color-brand)",
  className,
  trackClassName,
  height = "h-2",
}: {
  percent: number;
  color?: string;
  className?: string;
  trackClassName?: string;
  height?: string;
}) {
  const fillRef = useRef<HTMLDivElement>(null);
  const clamped = Math.max(0, Math.min(1, percent));

  useEffect(() => {
    const el = fillRef.current;
    if (!el) return;
    const animation = animate(el, {
      width: `${clamped * 100}%`,
      duration: 800,
      ease: "outExpo",
    });
    return () => {
      animation.revert();
    };
  }, [clamped]);

  return (
    <div className={cn("w-full overflow-hidden rounded-full bg-surface-muted", height, trackClassName)}>
      <div ref={fillRef} className={cn("h-full rounded-full", className)} style={{ width: 0, background: color }} />
    </div>
  );
}
