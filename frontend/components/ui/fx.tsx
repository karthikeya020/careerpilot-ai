"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { motion, useMotionValue, useReducedMotion, useSpring } from "framer-motion";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ styles */
/** One <style> for the shared Job-Match effects (spotlight glow + aurora). */
export function JobFxStyles() {
  return (
    <style>{`
      .js-spot {
        position: absolute; inset: 0; border-radius: inherit; pointer-events: none;
        opacity: 0; transition: opacity .25s ease;
        background: radial-gradient(220px circle at var(--mx, 50%) var(--my, 50%),
          color-mix(in srgb, var(--color-brand) 22%, transparent), transparent 60%);
      }
      .js-card:hover .js-spot, .js-card:focus-within .js-spot { opacity: 1; }
      .js-card { transition: transform .35s cubic-bezier(.22,1,.36,1), box-shadow .35s ease; }

      .js-aurora {
        position: absolute; inset: -40%; pointer-events: none; opacity: .5; filter: blur(48px);
        background:
          radial-gradient(40% 55% at 20% 30%, color-mix(in srgb, var(--color-brand) 55%, transparent), transparent 70%),
          radial-gradient(45% 50% at 80% 20%, color-mix(in srgb, var(--color-accent-2) 50%, transparent), transparent 70%),
          radial-gradient(50% 60% at 60% 80%, color-mix(in srgb, var(--color-brand-2) 45%, transparent), transparent 70%);
        background-size: 200% 200%;
        animation: js-aurora 16s ease-in-out infinite alternate;
      }
      @keyframes js-aurora {
        0%   { background-position: 0% 0%,   100% 0%, 50% 100%; }
        50%  { background-position: 60% 40%, 40% 60%, 60% 20%; }
        100% { background-position: 100% 100%, 0% 100%, 20% 60%; }
      }
      @keyframes js-spark {
        to { transform: translate(var(--dx), var(--dy)) scale(.2); opacity: 0; }
      }
      .js-spark-piece { animation: js-spark 480ms cubic-bezier(.2,.7,.3,1) forwards; }
      @media (prefers-reduced-motion: reduce) {
        .js-aurora { animation: none; }
        .js-spark-piece { animation-duration: 1ms; }
      }
    `}</style>
  );
}

/** Radial glow that tracks the cursor -- attach to any card root. */
export function spotlightMove(e: React.MouseEvent<HTMLElement>) {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty("--mx", `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty("--my", `${e.clientY - r.top}px`);
}

/* ------------------------------------------------------------------ Aurora */
export function Aurora({ className }: { className?: string }) {
  return (
    <div className={cn("absolute inset-0 overflow-hidden", className)} aria-hidden="true">
      <div className="js-aurora" />
    </div>
  );
}

/* -------------------------------------------------------------- GradientText */
export function GradientText({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "animate-gradient bg-gradient-to-r from-brand via-accent-2 to-brand-2 bg-clip-text text-transparent",
        className,
      )}
    >
      {children}
    </span>
  );
}

/* -------------------------------------------------------------------- CountUp */
export function CountUp({
  value,
  duration = 900,
  className,
}: {
  value: number;
  duration?: number;
  className?: string;
}) {
  const reduced = useReducedMotion();
  const [display, setDisplay] = useState(0);
  const fromRef = useRef(0);

  useEffect(() => {
    if (reduced) return;
    const start = performance.now();
    const from = fromRef.current;
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setDisplay(Math.round(from + (value - from) * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
      else fromRef.current = value;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration, reduced]);

  return <span className={className}>{reduced ? value : display}</span>;
}

/* ----------------------------------------------------------------- ClickSpark */
export function ClickSpark({
  children,
  color = "var(--color-brand)",
  count = 8,
}: {
  children: ReactNode;
  color?: string;
  count?: number;
}) {
  const [bursts, setBursts] = useState<{ id: number; x: number; y: number }[]>([]);
  const seed = useRef(0);

  const onClick = (e: React.MouseEvent<HTMLSpanElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const id = ++seed.current;
    setBursts((b) => [...b, { id, x: e.clientX - r.left, y: e.clientY - r.top }]);
    window.setTimeout(() => setBursts((b) => b.filter((x) => x.id !== id)), 520);
  };

  return (
    <span className="relative inline-flex" onClickCapture={onClick}>
      {children}
      {bursts.map((burst) => (
        <span key={burst.id} className="pointer-events-none absolute" style={{ left: burst.x, top: burst.y }} aria-hidden="true">
          {Array.from({ length: count }).map((_, i) => {
            const a = (i / count) * Math.PI * 2;
            return (
              <span
                key={i}
                className="js-spark-piece absolute h-1 w-1 rounded-full"
                style={
                  {
                    background: color,
                    "--dx": `${Math.cos(a) * 26}px`,
                    "--dy": `${Math.sin(a) * 26}px`,
                  } as React.CSSProperties
                }
              />
            );
          })}
        </span>
      ))}
    </span>
  );
}

/* ------------------------------------------------------------------ Magnetic */
export function Magnetic({
  children,
  strength = 0.35,
  className,
}: {
  children: ReactNode;
  strength?: number;
  className?: string;
}) {
  const reduced = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, { stiffness: 260, damping: 18, mass: 0.4 });
  const sy = useSpring(y, { stiffness: 260, damping: 18, mass: 0.4 });

  const onMove = (e: React.MouseEvent) => {
    if (reduced || !ref.current) return;
    const r = ref.current.getBoundingClientRect();
    x.set((e.clientX - (r.left + r.width / 2)) * strength);
    y.set((e.clientY - (r.top + r.height / 2)) * strength);
  };
  const reset = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={reset}
      style={{ x: sx, y: sy }}
      className={cn("inline-flex", className)}
    >
      {children}
    </motion.div>
  );
}
