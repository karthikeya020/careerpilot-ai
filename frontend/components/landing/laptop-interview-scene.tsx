"use client";

import { useEffect, useRef, useState } from "react";
import { animate, eases, stagger } from "animejs";
import { Bot, Briefcase, CheckCircle2, Mic, ShieldCheck } from "lucide-react";

const QUESTION = "Tell me about a time you led a project under a tight deadline.";
const CHECKS = ["Relevance", "Structure", "Evidence"];
const TYPE_INTERVAL_MS = 28;

/**
 * The hero centerpiece: a laptop running a live Interview Arena session
 * (real product UI, not stock art) with a typewriter question, sequential
 * evaluation checks, and floating "recruiter view" / "confidence" cards --
 * the whole student -> interview -> evidence -> recruiter loop in one
 * glance. Idle float + cursor-parallax tilt via anime.js.
 */
export function LaptopInterviewScene() {
  const sceneRef = useRef<HTMLDivElement>(null);
  const laptopRef = useRef<HTMLDivElement>(null);
  const cardsRef = useRef<HTMLDivElement>(null);
  const [typed, setTyped] = useState("");
  const [checksShown, setChecksShown] = useState(0);

  // Looping typewriter: types the question, reveals eval checks, holds, resets.
  useEffect(() => {
    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout>;

    function revealChecks(count: number) {
      if (cancelled) return;
      setChecksShown(count);
      if (count < CHECKS.length) {
        timeout = setTimeout(() => revealChecks(count + 1), 450);
      } else {
        timeout = setTimeout(restart, 2600);
      }
    }

    function type(index: number) {
      if (cancelled) return;
      setTyped(QUESTION.slice(0, index));
      if (index < QUESTION.length) {
        timeout = setTimeout(() => type(index + 1), TYPE_INTERVAL_MS);
      } else {
        timeout = setTimeout(() => revealChecks(1), 500);
      }
    }

    function restart() {
      setTyped("");
      setChecksShown(0);
      timeout = setTimeout(() => type(1), 500);
    }

    timeout = setTimeout(() => type(1), 700);
    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, []);

  // Entrance: laptop rises in, floating cards pop in staggered.
  useEffect(() => {
    if (laptopRef.current) {
      animate(laptopRef.current, {
        opacity: [0, 1],
        translateY: [40, 0],
        scale: [0.94, 1],
        duration: 900,
        ease: "outExpo",
      });
    }
    if (cardsRef.current && cardsRef.current.children.length > 0) {
      animate(cardsRef.current.children, {
        opacity: [0, 1],
        translateY: [24, 0],
        scale: [0.9, 1],
        delay: stagger(180, { start: 500 }),
        duration: 700,
        ease: "outExpo",
      });
    }
  }, []);

  // Idle float loop on the floating cards, starting once they've landed.
  useEffect(() => {
    const container = cardsRef.current;
    if (!container) return;
    const children = Array.from(container.children) as HTMLElement[];
    const animations = children.map((child, i) =>
      animate(child, {
        translateY: [0, -10],
        duration: 2600 + i * 400,
        loop: true,
        alternate: true,
        ease: "inOutSine",
        delay: 1300 + i * 300,
      }),
    );
    return () => animations.forEach((a) => a.revert());
  }, []);

  // Cursor-parallax tilt on the laptop -- a subtle 3D follow effect.
  useEffect(() => {
    const scene = sceneRef.current;
    const laptop = laptopRef.current;
    if (!scene || !laptop) return;

    const handleMove = (event: MouseEvent) => {
      const rect = scene.getBoundingClientRect();
      const px = (event.clientX - rect.left) / rect.width - 0.5;
      const py = (event.clientY - rect.top) / rect.height - 0.5;
      animate(laptop, { rotateY: px * 10, rotateX: py * -10, duration: 500, ease: "outQuad" });
    };
    const handleLeave = () => {
      animate(laptop, { rotateY: 0, rotateX: 0, duration: 700, ease: eases.outElastic(1, 0.6) });
    };

    scene.addEventListener("mousemove", handleMove);
    scene.addEventListener("mouseleave", handleLeave);
    return () => {
      scene.removeEventListener("mousemove", handleMove);
      scene.removeEventListener("mouseleave", handleLeave);
    };
  }, []);

  return (
    <div ref={sceneRef} className="relative mx-auto w-full max-w-lg [perspective:1200px]" aria-hidden="true">
      <div className="absolute inset-[8%] rounded-full bg-gradient-radial-brand opacity-60 blur-3xl" />

      <div ref={laptopRef} className="relative opacity-0 [transform-style:preserve-3d]">
        <div className="relative overflow-hidden rounded-t-2xl border-4 border-b-0 border-[#1c1830] bg-[#0b0a1a] shadow-[var(--shadow-lg)]">
          <div className="flex items-center gap-1.5 border-b border-white/10 bg-[#14101f] px-3 py-2">
            <span className="h-2.5 w-2.5 rounded-full bg-danger/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-warning/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-positive/70" />
            <span className="ml-2 text-[10px] text-white/40">Interview Arena — Live Session</span>
          </div>
          <div className="space-y-3 p-5">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
                <span className="absolute inset-0 animate-pulse-glow rounded-full bg-gradient-brand opacity-60 blur-md" />
                <Bot className="relative h-4 w-4 text-white" aria-hidden="true" />
              </span>
              <div>
                <p className="text-xs font-semibold text-white">AI Interviewer</p>
                <p className="text-[10px] text-white/40">CARE-routed specialist panel</p>
              </div>
              <span className="ml-auto flex items-center gap-1 rounded-full bg-danger/20 px-2 py-0.5 text-[9px] font-medium text-danger">
                <Mic className="h-2.5 w-2.5" aria-hidden="true" /> REC
              </span>
            </div>
            <p className="min-h-[2.6rem] text-sm leading-relaxed text-white/90">
              {typed}
              <span className="ml-0.5 inline-block h-3.5 w-[2px] animate-pulse bg-white/70 align-middle" />
            </p>
            <div className="flex flex-wrap gap-1.5 pt-1">
              {CHECKS.map((label, i) => (
                <span
                  key={label}
                  className={`flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium transition-all duration-500 ${
                    i < checksShown
                      ? "border-positive/30 bg-positive/15 text-positive opacity-100"
                      : "border-white/10 bg-white/5 text-white/20 opacity-60"
                  }`}
                >
                  <CheckCircle2 className="h-2.5 w-2.5" aria-hidden="true" /> {label}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="h-3 rounded-b-2xl bg-gradient-to-b from-[#2a2440] to-[#171329] shadow-[var(--shadow-lg)]" />
        <div className="mx-auto h-1.5 w-1/3 rounded-b-xl bg-[#171329]" />
      </div>

      <div ref={cardsRef}>
        <div className="absolute -top-8 -left-4 w-40 rounded-[var(--radius-md)] border border-border bg-surface/90 p-3 opacity-0 shadow-[var(--shadow-lg)] backdrop-blur md:-left-12 md:-top-10">
          <div className="mb-1 flex items-center gap-1.5">
            <Briefcase className="h-3.5 w-3.5 text-brand" aria-hidden="true" />
            <p className="text-[10px] font-semibold text-foreground">Recruiter view</p>
          </div>
          <p className="text-[10px] text-muted">Evidence-backed match</p>
          <p className="text-lg font-bold text-gradient-brand">87%</p>
        </div>
        <div className="absolute -right-4 -bottom-8 w-36 rounded-[var(--radius-md)] border border-border bg-surface/90 p-3 opacity-0 shadow-[var(--shadow-lg)] backdrop-blur md:-right-12 md:-bottom-10">
          <div className="mb-1 flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-positive" aria-hidden="true" />
            <p className="text-[10px] font-semibold text-foreground">Confidence</p>
          </div>
          <p className="text-lg font-bold text-foreground">91%</p>
          <p className="text-[10px] text-muted">12 evidence items</p>
        </div>
      </div>
    </div>
  );
}
