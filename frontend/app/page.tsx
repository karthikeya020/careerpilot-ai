"use client";

import Link from "next/link";
import {
  Braces,
  Briefcase,
  CheckCircle2,
  GaugeCircle,
  Mic,
  Network,
  Radar,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { LaptopInterviewScene } from "@/components/landing/laptop-interview-scene";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { AnimatedBar } from "@/components/ui/animated-bar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCountUp } from "@/hooks/use-count-up";
import { useScrollReveal } from "@/hooks/use-scroll-reveal";
import { useStaggerReveal } from "@/hooks/use-stagger-reveal";

const STATS = [
  { value: 100, suffix: "%", label: "Evidence-traced scores" },
  { value: 6, suffix: "", label: "Readiness components" },
  { value: 0, suffix: "", label: "Fabricated numbers" },
];

const HOW_IT_WORKS = [
  {
    icon: Mic,
    title: "Practice a real interview",
    description:
      "HR, Technical, and DSA rounds by voice or text in the Interview Arena — 2 easy, 2 medium, 2 hard, real questions with real follow-ups.",
  },
  {
    icon: Network,
    title: "Multi-agent evaluation",
    description:
      "CARE routes every answer through specialist agents scoring relevance, correctness, and depth — never a single black-box number.",
  },
  {
    icon: Radar,
    title: "Evidence joins your Career Twin",
    description:
      "Every score updates a persistent, versioned Career Twin with a full audit trail — nothing silently overwritten, nothing invented.",
  },
  {
    icon: Briefcase,
    title: "Recruiters see the proof",
    description:
      "When you opt in, recruiters see your evidence-backed readiness card — never a hiring prediction, never a public ranking.",
  },
];

const FEATURES = [
  {
    icon: Radar,
    title: "Career Twin",
    description: "A persistent, evidence-backed model of your skills, versioned every time new evidence arrives — never a guess.",
  },
  {
    icon: Mic,
    title: "Interview Arena",
    description: "Structured mock-interview rounds with camera, voice, and real follow-up questions, plus a full evidence-backed report.",
  },
  {
    icon: Network,
    title: "GraphRAG root cause",
    description: "Explains why a concept is weak by walking the knowledge graph — not just that it is.",
  },
  {
    icon: GaugeCircle,
    title: "Confidence-aware readiness",
    description: "Every readiness score ships with its confidence and evidence count. Insufficient evidence is labeled, not faked.",
  },
  {
    icon: ShieldCheck,
    title: "Trust Center",
    description: "Every AI decision traced: which agents ran, what evidence they cited, what confidence they returned.",
  },
  {
    icon: Braces,
    title: "Verified coding profile",
    description: "Real GitHub activity — language breakdown, contribution heatmap, top repos — evidence a reviewer can check themselves.",
  },
];

function StatNumber({ value, suffix }: { value: number; suffix: string }) {
  const animated = useCountUp(value, { duration: 1400 });
  return (
    <span className="text-metric-lg text-gradient-brand">
      {animated}
      {suffix}
    </span>
  );
}

function StatStrip() {
  const ref = useScrollReveal<HTMLDivElement>({ delay: 120 });
  return (
    <section className="border-y border-border bg-surface-muted/50">
      <div ref={ref} className="mx-auto grid max-w-4xl gap-8 px-6 py-10 sm:grid-cols-3">
        {STATS.map((stat) => (
          <div key={stat.label} className="text-center">
            <StatNumber value={stat.value} suffix={stat.suffix} />
            <p className="mt-1 text-xs font-medium uppercase tracking-wide text-muted">{stat.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function HowItWorks() {
  const ref = useScrollReveal<HTMLOListElement>({ delay: 110, y: 24 });
  return (
    <section className="mx-auto max-w-6xl px-6 py-24">
      <div className="mx-auto mb-14 max-w-2xl text-center">
        <Badge variant="muted" className="mb-3">
          How it works
        </Badge>
        <h2 className="text-h1 text-foreground">From a spoken answer to evidence a recruiter can trust.</h2>
      </div>
      <ol ref={ref} className="relative grid gap-6 md:grid-cols-4">
        <div
          className="absolute left-0 right-0 top-9 hidden h-px bg-gradient-to-r from-transparent via-border to-transparent md:block"
          aria-hidden="true"
        />
        {HOW_IT_WORKS.map((step, i) => (
          <li key={step.title} className="relative flex flex-col items-center text-center md:items-start md:text-left">
            <span className="relative z-10 mb-4 flex h-[72px] w-[72px] shrink-0 items-center justify-center rounded-full border-4 border-background bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
              <step.icon className="h-7 w-7 text-brand-foreground" aria-hidden="true" />
              <span className="absolute -right-1 -top-1 flex h-6 w-6 items-center justify-center rounded-full bg-surface text-[11px] font-bold text-foreground shadow-[var(--shadow-sm)]">
                {i + 1}
              </span>
            </span>
            <h3 className="mb-1.5 text-sm font-semibold text-foreground">{step.title}</h3>
            <p className="text-sm leading-relaxed text-muted">{step.description}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

function FeatureGrid() {
  const ref = useScrollReveal<HTMLDivElement>({ delay: 90 });
  return (
    <section className="mx-auto max-w-6xl px-6 pb-24">
      <div className="mx-auto mb-12 max-w-2xl text-center">
        <Badge variant="muted" className="mb-3">
          Everything, evidence-first
        </Badge>
        <h2 className="text-h1 text-foreground">One Career Twin. Six proof points.</h2>
      </div>
      <div ref={ref} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((feature) => (
          <Card key={feature.title} interactive>
            <CardContent className="pt-6">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
                <feature.icon className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
              </div>
              <h3 className="mb-1.5 text-sm font-semibold text-foreground">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-muted">{feature.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}

function RecruiterSection() {
  const ref = useScrollReveal<HTMLDivElement>({ delay: 130, y: 24 });
  return (
    <section className="mx-auto max-w-6xl px-6 pb-24">
      <div ref={ref} className="grid items-center gap-10 rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:grid-cols-2 md:p-12">
        <div>
          <Badge variant="muted" className="mb-3">
            <Users className="h-3 w-3" aria-hidden="true" /> Built for recruiters, too
          </Badge>
          <h2 className="text-h1 text-foreground">Evidence a recruiter can trust — never a verdict.</h2>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-muted">
            When a student opts in, recruiters see a real evidence summary — readiness components, confidence, and
            the record it traces back to. No hiring predictions. No public rankings. No fabricated scores. Ever.
          </p>
          <ul className="mt-6 space-y-2.5">
            {["No hiring probability, ever", "No cross-candidate ranking", "Every number traces to real evidence"].map((line) => (
              <li key={line} className="flex items-center gap-2.5 text-sm text-foreground">
                <CheckCircle2 className="h-4 w-4 shrink-0 text-positive" aria-hidden="true" />
                {line}
              </li>
            ))}
          </ul>
        </div>
        <Card variant="glow-brand" className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-radial-brand opacity-30" aria-hidden="true" />
          <CardContent className="relative space-y-4 pt-6">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-brand text-sm font-bold text-brand-foreground shadow-[var(--shadow-glow-brand)]">
                A
              </span>
              <div>
                <p className="text-sm font-semibold text-foreground">Evidence summary</p>
                <p className="text-xs text-muted">Shared with your consent only</p>
              </div>
              <Briefcase className="ml-auto h-4 w-4 text-muted" aria-hidden="true" />
            </div>
            {[
              { label: "Technical readiness", pct: 0.86 },
              { label: "Communication", pct: 0.74 },
              { label: "Portfolio evidence", pct: 0.62 },
            ].map((row) => (
              <div key={row.label}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span className="text-muted">{row.label}</span>
                  <span className="font-semibold text-foreground">{Math.round(row.pct * 100)}%</span>
                </div>
                <AnimatedBar percent={row.pct} />
              </div>
            ))}
            <p className="rounded-[var(--radius-md)] border border-border bg-surface-muted px-3 py-2 text-[11px] text-muted">
              Not a hiring prediction. Coverage and alignment only, traced to 46 real evidence records.
            </p>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

function FinalCta() {
  const ref = useScrollReveal<HTMLDivElement>({ delay: 90, y: 20 });
  return (
    <section className="mx-auto max-w-5xl px-6 pb-24">
      <div ref={ref} className="relative overflow-hidden rounded-[var(--radius-xl)] bg-gradient-brand px-8 py-16 text-center shadow-[var(--shadow-glow-brand)] md:px-16">
        <div className="absolute -left-20 -top-20 h-64 w-64 rounded-full bg-white/10 blur-3xl" aria-hidden="true" />
        <div className="absolute -bottom-20 -right-20 h-64 w-64 rounded-full bg-white/10 blur-3xl" aria-hidden="true" />
        <div className="relative">
          <Sparkles className="mx-auto mb-4 h-8 w-8 text-brand-foreground" aria-hidden="true" />
          <h2 className="text-h1 text-brand-foreground">Build a Career Twin that shows its work.</h2>
          <p className="mx-auto mt-3 max-w-lg text-sm text-brand-foreground/80">
            Free to start. No credit card. Every score traceable from day one.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="xl" variant="outline" className="border-white/40 bg-white text-brand hover:bg-white/90" asChild>
              <Link href="/register">Create your Career Twin</Link>
            </Button>
            <Button size="xl" variant="ghost" className="text-brand-foreground hover:bg-white/10" asChild>
              <Link href="/demo">Explore the demo</Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}

function LandingHero() {
  const textRef = useStaggerReveal<HTMLDivElement>(true, { delay: 110, y: 22 });
  return (
    <section className="relative mx-auto grid max-w-6xl items-center gap-14 overflow-hidden px-6 py-20 md:grid-cols-[1.05fr_0.95fr] md:py-28">
      <div ref={textRef} className="text-center md:text-left">
        <p className="inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-glass px-3.5 py-1.5 text-xs font-medium text-muted backdrop-blur">
          <span className="h-1.5 w-1.5 rounded-full bg-accent shadow-[0_0_8px_var(--accent)]" />
          Evidence-grounded · Confidence-aware · Agentic
        </p>
        <h1 className="text-display text-foreground">
          The Career Operating System
          <br />
          that <span className="text-gradient-brand">shows its work.</span>
        </h1>
        <p className="mx-auto max-w-xl text-lg text-muted md:mx-0">
          Practice real interviews, build a persistent Career Twin from real evidence, and let recruiters see the
          proof — never a fabricated score, never a hiring prediction.
        </p>
        <div className="flex flex-col items-center justify-center gap-3 sm:flex-row md:justify-start">
          <Button size="xl" asChild>
            <Link href="/register">Create your Career Twin</Link>
          </Button>
          <Button size="xl" variant="outline" asChild>
            <Link href="/demo">Explore the demo</Link>
          </Button>
        </div>
      </div>
      <LaptopInterviewScene />
    </section>
  );
}

export default function LandingPage() {
  return (
    <div className="bg-grain bg-mesh-animated flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-surface/60 px-6 py-4 backdrop-blur-xl md:px-12">
        <div className="flex items-center gap-2.5 font-semibold">
          <Logo size={32} />
          <span className="tracking-tight">CareerPilot AI</span>
        </div>
        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Button variant="ghost" asChild>
            <Link href="/login">Log in</Link>
          </Button>
          <Button asChild>
            <Link href="/register">Get started</Link>
          </Button>
        </div>
      </header>

      <main className="flex-1">
        <LandingHero />
        <StatStrip />
        <HowItWorks />
        <FeatureGrid />
        <RecruiterSection />
        <FinalCta />
      </main>

      <footer className="border-t border-border px-6 py-6 text-center text-xs text-muted">
        CareerPilot AI — Phase 1 foundation. No hiring predictions. No public rankings. No fabricated scores.
      </footer>
    </div>
  );
}
