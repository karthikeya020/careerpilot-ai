"use client";

import { useEffect, useMemo } from "react";
import { createPortal } from "react-dom";

/**
 * Synthesised "gift received" chime -- an ascending bell arpeggio + a sparkle
 * sweep + a soft thump. No audio asset. Safe to call from any click handler;
 * no-ops if Web Audio is unavailable or blocked.
 */
export function playGiftSound() {
  try {
    const Ctx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const now = ctx.currentTime;
    const master = ctx.createGain();
    master.gain.value = 0.0001;
    master.gain.setValueAtTime(0.5, now);
    master.connect(ctx.destination);

    // soft body thump
    const thump = ctx.createOscillator();
    const thumpGain = ctx.createGain();
    thump.type = "sine";
    thump.frequency.setValueAtTime(180, now);
    thump.frequency.exponentialRampToValueAtTime(70, now + 0.18);
    thumpGain.gain.setValueAtTime(0.35, now);
    thumpGain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
    thump.connect(thumpGain).connect(master);
    thump.start(now);
    thump.stop(now + 0.26);

    // ascending bell arpeggio C5-E5-G5-C6
    [523.25, 659.25, 783.99, 1046.5].forEach((freq, i) => {
      const t = now + 0.05 + i * 0.09;
      const osc = ctx.createOscillator();
      const sub = ctx.createOscillator();
      const g = ctx.createGain();
      osc.type = "sine";
      sub.type = "triangle";
      osc.frequency.value = freq;
      sub.frequency.value = freq * 2;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.28, t + 0.012);
      g.gain.exponentialRampToValueAtTime(0.001, t + 0.5);
      osc.connect(g);
      sub.connect(g);
      g.connect(master);
      osc.start(t);
      sub.start(t);
      osc.stop(t + 0.52);
      sub.stop(t + 0.52);
    });

    // sparkle sweep
    const spark = ctx.createOscillator();
    const sparkGain = ctx.createGain();
    const sparkFilter = ctx.createBiquadFilter();
    spark.type = "sawtooth";
    sparkFilter.type = "bandpass";
    sparkFilter.frequency.setValueAtTime(1200, now + 0.35);
    sparkFilter.frequency.exponentialRampToValueAtTime(6000, now + 0.75);
    sparkFilter.Q.value = 6;
    spark.frequency.setValueAtTime(900, now + 0.35);
    spark.frequency.exponentialRampToValueAtTime(2400, now + 0.75);
    sparkGain.gain.setValueAtTime(0.0001, now + 0.35);
    sparkGain.gain.exponentialRampToValueAtTime(0.12, now + 0.45);
    sparkGain.gain.exponentialRampToValueAtTime(0.001, now + 0.8);
    spark.connect(sparkFilter).connect(sparkGain).connect(master);
    spark.start(now + 0.35);
    spark.stop(now + 0.82);

    master.gain.setValueAtTime(0.5, now + 0.8);
    master.gain.exponentialRampToValueAtTime(0.0001, now + 1.1);
    window.setTimeout(() => {
      try {
        ctx.close();
      } catch {
        /* already closed */
      }
    }, 1400);
  } catch {
    /* audio blocked or unavailable -- silent */
  }
}

function reducedMotion(): boolean {
  return typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

const CONFETTI_COLORS = [
  "var(--color-brand)",
  "var(--color-accent-2)",
  "var(--color-brand-2)",
  "var(--color-positive)",
  "var(--color-warning)",
];

/** One-shot celebration overlay. Mount with a key so each trigger replays. */
export function GiftBurst({ onDone, caption = "It's yours to earn" }: { onDone: () => void; caption?: string }) {
  const calm = useMemo(() => reducedMotion(), []);

  useEffect(() => {
    const t = window.setTimeout(onDone, calm ? 900 : 1700);
    return () => window.clearTimeout(t);
  }, [onDone, calm]);

  const pieces = useMemo(() => {
    // deterministic jitter -- pure function of the index, no Math.random()
    const rnd = (n: number, salt: number) => {
      const x = Math.sin(n * 127.1 + salt * 311.7) * 43758.5453;
      return x - Math.floor(x);
    };
    return Array.from({ length: calm ? 0 : 26 }).map((_, i) => {
      const angle = (i / 26) * Math.PI * 2 + rnd(i, 1) * 0.5;
      const dist = 90 + rnd(i, 2) * 130;
      return {
        dx: `${Math.cos(angle) * dist}px`,
        dy: `${Math.sin(angle) * dist - 30}px`,
        rot: `${rnd(i, 3) * 720 - 360}deg`,
        delay: `${rnd(i, 4) * 90}ms`,
        color: CONFETTI_COLORS[i % CONFETTI_COLORS.length],
        w: 5 + Math.round(rnd(i, 5) * 6),
        h: 8 + Math.round(rnd(i, 6) * 8),
      };
    });
  }, [calm]);

  if (typeof document === "undefined") return null;

  return createPortal(
    <div className="pointer-events-none fixed inset-0 z-[60] flex items-center justify-center" aria-hidden="true">
      <style>{`
        @keyframes gfx-pop { 0%{transform:scale(.2) translateY(20px);opacity:0} 45%{transform:scale(1.15) translateY(-8px);opacity:1} 70%{transform:scale(.95)} 100%{transform:scale(1) translateY(0);opacity:1} }
        @keyframes gfx-out { 0%{opacity:1;transform:scale(1)} 100%{opacity:0;transform:scale(1.3) translateY(-24px)} }
        @keyframes gfx-ring { 0%{transform:scale(.3);opacity:.7} 100%{transform:scale(2.6);opacity:0} }
        @keyframes gfx-confetti { 0%{transform:translate(0,0) rotate(0);opacity:1} 100%{transform:translate(var(--dx),var(--dy)) rotate(var(--rot));opacity:0} }
        @keyframes gfx-caption { 0%{opacity:0;transform:translateY(8px)} 30%{opacity:1;transform:translateY(0)} 80%{opacity:1} 100%{opacity:0} }
        .gfx-box{animation:gfx-pop .45s cubic-bezier(.22,1,.36,1) both, gfx-out .5s ease 1.1s both}
        .gfx-ring{animation:gfx-ring .9s ease-out both}
        .gfx-piece{animation:gfx-confetti 1.2s cubic-bezier(.15,.6,.3,1) both}
        .gfx-caption{animation:gfx-caption 1.7s ease both}
        @media (prefers-reduced-motion: reduce){
          .gfx-box{animation:gfx-pop .3s ease both}
          .gfx-ring,.gfx-piece{display:none}
        }
      `}</style>
      <span className="gfx-ring absolute h-24 w-24 rounded-full border-2 border-brand" />
      {pieces.map((p, i) => (
        <span
          key={i}
          className="gfx-piece absolute rounded-[2px]"
          style={
            {
              "--dx": p.dx,
              "--dy": p.dy,
              "--rot": p.rot,
              animationDelay: p.delay,
              background: p.color,
              width: p.w,
              height: p.h,
            } as React.CSSProperties
          }
        />
      ))}
      <div className="gfx-box relative text-5xl drop-shadow-lg">🎁</div>
      <p className="gfx-caption absolute mt-28 rounded-full bg-foreground/85 px-3 py-1 text-xs font-semibold text-background">
        {caption}
      </p>
    </div>,
    document.body,
  );
}
