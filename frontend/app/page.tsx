import Link from "next/link";
import { CheckCircle2, GaugeCircle, Radar, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ThemeToggle } from "@/components/layout/theme-toggle";

const PILLARS = [
  {
    icon: Radar,
    title: "Career Twin",
    description:
      "A persistent, evidence-backed model of your skills, versioned every time new evidence arrives — never a guess.",
  },
  {
    icon: GaugeCircle,
    title: "Confidence-aware readiness",
    description:
      "Every readiness score ships with its confidence and evidence count. Insufficient evidence is labeled, not faked.",
  },
  {
    icon: ShieldCheck,
    title: "Trust by design",
    description:
      "No hiring predictions, no rankings, no fabricated scores. Every number traces back to a real evidence record.",
  },
];

const STEPS = [
  "Upload your resume and paste a target job description.",
  "Your Career Twin scores six readiness components from real evidence.",
  "Get one focused daily mission tied to your weakest, evidence-backed gap.",
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between px-6 py-5 md:px-12">
        <div className="flex items-center gap-2 font-semibold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-brand-foreground text-sm font-bold">
            C
          </span>
          <span>CareerPilot AI</span>
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
        <section className="mx-auto max-w-4xl px-6 py-16 text-center md:py-24">
          <p className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-border bg-surface-muted px-3 py-1 text-xs font-medium text-muted">
            Evidence-grounded. Confidence-aware. Agentic.
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground md:text-6xl">
            The Career Operating System that shows its work.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base text-muted md:text-lg">
            CareerPilot AI builds a persistent Career Twin from your resume and target roles — every score
            traceable to real evidence, every recommendation explained, never a fabricated number.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" asChild>
              <Link href="/register">Create your Career Twin</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/demo">Explore the demo</Link>
            </Button>
          </div>
        </section>

        <section className="mx-auto grid max-w-5xl gap-4 px-6 pb-16 md:grid-cols-3">
          {PILLARS.map((pillar) => (
            <Card key={pillar.title}>
              <CardContent className="pt-5">
                <pillar.icon className="mb-3 h-6 w-6 text-brand" aria-hidden="true" />
                <h2 className="mb-1 text-sm font-semibold text-foreground">{pillar.title}</h2>
                <p className="text-sm text-muted">{pillar.description}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="mx-auto max-w-3xl px-6 pb-24">
          <h2 className="mb-6 text-center text-lg font-semibold text-foreground">How it works</h2>
          <ol className="space-y-4">
            {STEPS.map((step, index) => (
              <li key={step} className="flex items-start gap-3 rounded-[var(--radius-md)] border border-border bg-surface p-4">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-positive" aria-hidden="true" />
                <span className="text-sm text-foreground">
                  <span className="mr-1 font-semibold text-muted">{index + 1}.</span>
                  {step}
                </span>
              </li>
            ))}
          </ol>
        </section>
      </main>

      <footer className="border-t border-border px-6 py-6 text-center text-xs text-muted">
        CareerPilot AI — Phase 1 foundation. No hiring predictions. No public rankings. No fabricated scores.
      </footer>
    </div>
  );
}
