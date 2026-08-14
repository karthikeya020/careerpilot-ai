"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowUpRight,
  Brain,
  Briefcase,
  Building2,
  CheckCircle2,
  FileQuestion,
  FlaskConical,
  GitBranch,
  Layers,
  Maximize,
  Mic,
  Microscope,
  Minimize,
  Rocket,
  ShieldCheck,
  Sparkles,
  Target,
  Wrench,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useCareerTwin } from "@/hooks/use-career-twin";
import { useCareExecutions } from "@/hooks/use-trust-center";
import { useDashboard } from "@/hooks/use-dashboard";
import { useExperimentScenarios } from "@/hooks/use-experiment";
import { useCalibration, useEvaluationRuns } from "@/hooks/use-research-lab";
import { useResponsibleAIOverview } from "@/hooks/use-responsible-ai";
import { useAuth } from "@/lib/auth-context";
import { formatPercent } from "@/lib/utils";

const STEPS = [
  "opening",
  "student",
  "twin",
  "weakness",
  "graphrag",
  "care",
  "mission",
  "assessment",
  "interview",
  "experiment",
  "research",
  "responsible",
  "scale",
  "closing",
] as const;
type Step = (typeof STEPS)[number];

const STEP_LABELS: Record<Step, string> = {
  opening: "Opening",
  student: "Meet the Student",
  twin: "Career Twin Awakening",
  weakness: "Priority Weakness",
  graphrag: "GraphRAG Root Cause",
  care: "CARE Decision",
  mission: "Mission",
  assessment: "Assessment Improvement",
  interview: "Interview Intelligence",
  experiment: "Experiment Lab",
  research: "Research Proof",
  responsible: "Responsible AI",
  scale: "Institutional Scale",
  closing: "Closing",
};

function TechnicalBadgeRow({ items }: { items: { label: string; value: string }[] }) {
  return (
    <div className="mt-6 flex flex-wrap justify-center gap-2">
      {items.map((item) => (
        <Badge key={item.label} variant="muted">
          {item.label}: {item.value}
        </Badge>
      ))}
    </div>
  );
}

function OpenLiveLink({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="mt-6 inline-flex items-center gap-1.5 rounded-full border border-brand/30 bg-brand-soft px-4 py-1.5 text-xs font-medium text-brand transition-transform hover:scale-105"
    >
      {label} <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
    </Link>
  );
}

function SlideShell({ children, icon: Icon }: { children: React.ReactNode; icon?: typeof Sparkles }) {
  return (
    <div className="mx-auto flex h-full max-w-4xl flex-col items-center justify-center px-6 text-center">
      {Icon && (
        <div className="animate-scale-in mb-7 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
          <Icon className="h-8 w-8 text-brand-foreground" aria-hidden="true" />
        </div>
      )}
      {children}
    </div>
  );
}

function OpeningSlide() {
  return (
    <SlideShell>
      <div className="relative mb-8 h-36 w-36">
        <div className="absolute inset-0 rounded-full bg-gradient-radial-brand blur-2xl animate-pulse-glow" />
        <div className="absolute inset-4 rounded-full bg-gradient-brand animate-float shadow-[var(--shadow-glow-brand)]" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Sparkles className="h-10 w-10 text-brand-foreground drop-shadow" aria-hidden="true" />
        </div>
      </div>
      <h1 className="animate-fade-up text-projector-lg text-foreground">CareerPilot AI</h1>
      <p className="animate-fade-up delay-1 mt-3 text-projector text-gradient-brand">The Career Operating System</p>
      <p className="animate-fade-up delay-2 mx-auto mt-7 max-w-xl text-lg text-muted">
        An AI system that remembers every student, finds the root cause of their weaknesses, simulates their best
        path forward, and continuously evolves with them.
      </p>
    </SlideShell>
  );
}

function StudentSlide({ technicalView }: { technicalView: boolean }) {
  const { data } = useDashboard();
  return (
    <SlideShell icon={Sparkles}>
      <h2 className="animate-fade-up text-projector text-foreground">Meet the Student</h2>
      {data ? (
        <>
          <p className="mt-4 text-2xl text-foreground">{data.student_name}</p>
          <p className="mt-1 text-muted">Target role: {data.target_role?.title ?? "not yet set"}</p>
          <div className="mt-6 flex gap-3">
            <Badge variant={data.resume_status.uploaded ? "positive" : "muted"}>
              {data.resume_status.uploaded ? "Resume uploaded" : "No resume yet"}
            </Badge>
            <Badge variant={data.job_description_status.added ? "positive" : "muted"}>
              {data.job_description_status.added ? "Job description added" : "No job description yet"}
            </Badge>
          </div>
        </>
      ) : (
        <p className="mt-4 text-muted">Loading student profile…</p>
      )}
      {technicalView && data && <TechnicalBadgeRow items={[{ label: "Onboarding", value: String(data.onboarding_completed) }]} />}
    </SlideShell>
  );
}

function TwinSlide({ technicalView }: { technicalView: boolean }) {
  const { data: snapshot } = useCareerTwin();
  return (
    <SlideShell icon={Brain}>
      <h2 className="animate-fade-up text-projector text-foreground">Career Twin Awakening</h2>
      {snapshot ? (
        <>
          <p className="animate-fade-up delay-1 mt-4 text-metric-lg text-gradient-brand">{formatPercent(snapshot.overall_score)}</p>
          <p className="mt-1 text-muted">Overall readiness, version {snapshot.version}</p>
          <div className="mt-6 grid w-full grid-cols-3 gap-3">
            {snapshot.components.slice(0, 6).map((c) => (
              <div key={c.component_type} className="card-premium rounded-[var(--radius-md)] p-3">
                <p className="text-[10px] capitalize text-muted">{c.component_type.replaceAll("_readiness", "").replaceAll("_", " ")}</p>
                <p className="text-base font-bold text-foreground">{c.status === "scored" ? formatPercent(c.score) : "—"}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 max-w-lg text-sm text-muted">{snapshot.change_summary}</p>
          {technicalView && (
            <TechnicalBadgeRow items={[{ label: "Formula", value: snapshot.formula_version }, { label: "Confidence", value: formatPercent(snapshot.overall_confidence) }]} />
          )}
        </>
      ) : (
        <p className="mt-4 text-muted">No Career Twin snapshot yet for this account -- complete onboarding to generate one.</p>
      )}
    </SlideShell>
  );
}

function WeaknessSlide() {
  const { data } = useDashboard();
  const weakness = data?.priority_weakness;
  return (
    <SlideShell icon={Target}>
      <h2 className="animate-fade-up text-projector text-foreground">Priority Weakness</h2>
      {weakness ? (
        <>
          <p className="mt-4 text-2xl font-semibold capitalize text-warning">
            {weakness.component_type.replaceAll("_readiness", "").replaceAll("_", " ")}
          </p>
          <p className="mt-2 max-w-xl text-sm text-muted">{weakness.explanation}</p>
          <p className="mt-4 text-xs text-muted">
            Score {formatPercent(weakness.score)} · Confidence {formatPercent(weakness.confidence)} · {weakness.evidence_count} evidence item(s)
          </p>
        </>
      ) : (
        <p className="mt-4 text-muted">No priority weakness identified yet -- every component is either strong or has insufficient evidence.</p>
      )}
    </SlideShell>
  );
}

function GraphChainMotif() {
  const nodes = [
    { icon: FileQuestion, label: "Missed question", color: "var(--color-warning)" },
    { icon: Layers, label: "Weak concept", color: "var(--color-danger)" },
    { icon: Briefcase, label: "Role requirement", color: "var(--color-accent-2)" },
    { icon: Wrench, label: "Intervention", color: "var(--color-positive)" },
  ];
  return (
    <div className="mt-6 flex items-center justify-center gap-1">
      {nodes.map((node, i) => {
        const Icon = node.icon;
        return (
          <div key={node.label} className="flex items-center gap-1">
            <div className={`animate-scale-in delay-${i + 1} flex flex-col items-center gap-1.5`}>
              <span
                className="flex h-11 w-11 items-center justify-center rounded-full border-2 bg-surface"
                style={{ borderColor: node.color, boxShadow: i === 1 ? "var(--shadow-glow-brand)" : undefined }}
              >
                <Icon className="h-5 w-5" style={{ color: node.color }} aria-hidden="true" />
              </span>
              <span className="max-w-[5.5rem] text-[10px] leading-tight text-muted">{node.label}</span>
            </div>
            {i < nodes.length - 1 && (
              <div className={`animate-draw-line h-px w-8 bg-border-strong delay-${i + 1}`} style={{ ["--line-length" as string]: 32 }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function GraphRagSlide({ technicalView }: { technicalView: boolean }) {
  const { data: executions } = useCareExecutions(50);
  const rootCauseExecution = executions?.find((e) => e.task_type === "root_cause_analysis");
  return (
    <SlideShell icon={GitBranch}>
      <h2 className="animate-fade-up text-projector text-foreground">GraphRAG Root Cause</h2>
      {rootCauseExecution ? (
        <>
          <p className="mt-4 max-w-xl text-sm text-foreground">
            CareerPilot traced this student&apos;s gap through the concept-dependency graph -- not a guess, a stored relationship.
          </p>
          <GraphChainMotif />
          <div className="mt-6 flex items-center gap-2">
            <Badge variant={rootCauseExecution.retrieval_used ? "positive" : "muted"}>
              {rootCauseExecution.retrieval_used ? "Graph retrieval used" : "No retrieval needed"}
            </Badge>
            <Badge variant="default">Confidence {formatPercent(rootCauseExecution.confidence)}</Badge>
          </div>
          {technicalView && (
            <TechnicalBadgeRow items={[{ label: "Route", value: rootCauseExecution.route }, { label: "Agents", value: rootCauseExecution.agents_invoked.join(", ") || "none" }]} />
          )}
          <OpenLiveLink href="/graphrag" label="Open the live GraphRAG reveal" />
        </>
      ) : (
        <>
          <p className="mt-4 text-muted">No root-cause analysis has run for this account yet -- it triggers automatically the first time a mission targets a missed concept.</p>
          <GraphChainMotif />
          <OpenLiveLink href="/graphrag" label="Open the live GraphRAG reveal" />
        </>
      )}
    </SlideShell>
  );
}

function CareSlide({ technicalView }: { technicalView: boolean }) {
  const { data: executions } = useCareExecutions(5);
  const latest = executions?.[0];
  return (
    <SlideShell icon={ShieldCheck}>
      <h2 className="animate-fade-up text-projector text-foreground">CARE Decision</h2>
      {latest ? (
        <>
          <p className="mt-4 text-2xl font-semibold capitalize text-brand">{latest.route.replaceAll("_", " ")}</p>
          <p className="mt-2 max-w-xl text-sm text-muted">
            CARE dynamically chose this reasoning path based on evidence sufficiency and confidence -- not a fixed pipeline.
          </p>
          {technicalView && (
            <TechnicalBadgeRow
              items={[
                { label: "Task", value: latest.task_type },
                { label: "Confidence", value: formatPercent(latest.confidence) },
                { label: "Human review", value: String(latest.requires_human_review) },
              ]}
            />
          )}
          <OpenLiveLink href="/trust-center" label="Open the AI Trust Center" />
        </>
      ) : (
        <p className="mt-4 text-muted">No CARE decisions recorded for this account yet.</p>
      )}
    </SlideShell>
  );
}

function MissionSlide() {
  const { data } = useDashboard();
  return (
    <SlideShell icon={Rocket}>
      <h2 className="animate-fade-up text-projector text-foreground">Today&apos;s Mission</h2>
      {data?.mission ? (
        <>
          <p className="mt-4 text-2xl font-semibold text-foreground">{data.mission.title}</p>
          <p className="mt-2 max-w-xl text-sm text-muted">{data.mission.description}</p>
          <Badge className="mt-4" variant={data.mission.status === "completed" ? "positive" : "default"}>
            {data.mission.status.replaceAll("_", " ")}
          </Badge>
        </>
      ) : (
        <p className="mt-4 text-muted">No active mission for this account right now.</p>
      )}
    </SlideShell>
  );
}

function AssessmentSlide() {
  const { data: history } = useCareerTwin();
  return (
    <SlideShell icon={CheckCircle2}>
      <h2 className="animate-fade-up text-projector text-foreground">Career Twin Update</h2>
      {history ? (
        <>
          <p className="mt-4 max-w-xl text-sm text-foreground">{history.change_summary}</p>
          {history.score_delta !== null && (
            <p className={`animate-fade-up delay-1 mt-4 text-metric-lg ${history.score_delta >= 0 ? "text-positive" : "text-danger"}`}>
              {history.score_delta >= 0 ? "+" : ""}
              {(history.score_delta * 100).toFixed(1)}%
            </p>
          )}
        </>
      ) : (
        <p className="mt-4 text-muted">No Career Twin update recorded yet.</p>
      )}
    </SlideShell>
  );
}

function InterviewSlide({ technicalView }: { technicalView: boolean }) {
  const { data: executions } = useCareExecutions(50);
  const latest = executions?.find((e) => e.task_type === "interview_evaluation");
  return (
    <SlideShell icon={Mic}>
      <h2 className="animate-fade-up text-projector text-foreground">Interview Intelligence</h2>
      {latest ? (
        <>
          <p className="mt-4 max-w-xl text-sm text-foreground">
            CARE routed this answer to <span className="font-semibold capitalize">{latest.route.replaceAll("_", " ")}</span> --
            specialist agents evaluated relevance, correctness, structure, and communication, then checked resume-claim evidence.
          </p>
          <div className="mt-4 flex items-center gap-2">
            <Badge variant="default">Confidence {formatPercent(latest.confidence)}</Badge>
            <Badge variant="muted">{latest.agents_invoked.length} agent(s) invoked</Badge>
          </div>
          {technicalView && <TechnicalBadgeRow items={[{ label: "Agents", value: latest.agents_invoked.join(", ") }]} />}
          <OpenLiveLink href="/interview" label="Open Interview Arena" />
        </>
      ) : (
        <>
          <p className="mt-4 text-muted">No interview answers evaluated yet for this account -- try the Interview Arena.</p>
          <OpenLiveLink href="/interview" label="Open Interview Arena" />
        </>
      )}
    </SlideShell>
  );
}

function ExperimentSlide() {
  const { data: scenarios } = useExperimentScenarios();
  const latest = scenarios?.[0];
  return (
    <SlideShell icon={FlaskConical}>
      <h2 className="animate-fade-up text-projector text-foreground">Career Experiment Lab</h2>
      {latest?.result ? (
        <>
          <p className="mt-4 text-sm text-muted">Scenario: {latest.name}</p>
          <p className="animate-fade-up delay-1 mt-2 text-metric-lg text-gradient-brand">
            {latest.result.simulated_overall_score !== null ? formatPercent(latest.result.simulated_overall_score) : "—"}
          </p>
          <p className="mt-1 text-xs text-muted">simulated overall readiness</p>
          <p className="mt-4 rounded-[var(--radius-md)] border border-brand/30 bg-brand-soft px-3 py-2 text-xs font-medium text-brand">
            {latest.result.disclaimer}
          </p>
          <OpenLiveLink href="/experiment-lab" label="Open the Experiment Lab" />
        </>
      ) : (
        <>
          <p className="mt-4 text-muted">No scenarios simulated yet for this account -- try the Experiment Lab to compare learning investments.</p>
          <OpenLiveLink href="/experiment-lab" label="Open the Experiment Lab" />
        </>
      )}
    </SlideShell>
  );
}

function ResearchSlide() {
  const { data: calibration } = useCalibration();
  const { data: runs } = useEvaluationRuns();
  return (
    <SlideShell icon={Microscope}>
      <h2 className="animate-fade-up text-projector text-foreground">Research Proof</h2>
      <p className="mt-2 max-w-xl text-sm text-muted">Why is CareerPilot better than one generic chatbot? Real, reproducible comparisons.</p>
      {runs && runs.length > 0 ? (
        <div className="mt-6 grid grid-cols-2 gap-4 text-center">
          <div>
            <p className="text-3xl font-bold text-foreground">{runs.length}</p>
            <p className="text-xs text-muted">Experiment run(s) recorded</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-foreground">{calibration?.sample_size ?? 0}</p>
            <p className="text-xs text-muted">Calibration sample size</p>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-muted">No experiments run yet -- visit the Research Lab to run Experiment A/B live.</p>
      )}
      <OpenLiveLink href="/research-lab" label="Open the Research Benchmark Lab" />
    </SlideShell>
  );
}

function ResponsibleSlide() {
  const { data } = useResponsibleAIOverview();
  return (
    <SlideShell icon={ShieldCheck}>
      <h2 className="animate-fade-up text-projector text-foreground">Responsible AI</h2>
      {data ? (
        <ul className="mt-4 space-y-1.5 text-sm text-foreground">
          {data.non_claims.slice(0, 5).map((claim, i) => (
            <li key={i} className="flex items-center justify-center gap-2">
              <X className="h-3.5 w-3.5 text-danger" aria-hidden="true" />
              {claim}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-4 text-muted">Loading Responsible AI status…</p>
      )}
      <OpenLiveLink href="/responsible-ai" label="Open the Responsible AI Center" />
    </SlideShell>
  );
}

function ScaleSlide() {
  return (
    <SlideShell icon={Building2}>
      <h2 className="animate-fade-up text-projector text-foreground">Institutional Scale</h2>
      <p className="mx-auto mt-4 max-w-xl text-sm text-muted">
        The same evidence-backed Career Twin scales beyond one student: faculty see cohort skill gaps and who needs
        support, placement cells see readiness distribution and program effectiveness, recruiters see only evidence
        students explicitly share -- always privacy-safe aggregates, never a public ranking.
      </p>
      <div className="mt-6 flex flex-wrap justify-center gap-2">
        <Badge variant="muted">Faculty dashboard</Badge>
        <Badge variant="muted">Placement-cell dashboard</Badge>
        <Badge variant="muted">Recruiter dashboard (opt-in only)</Badge>
        <Badge variant="muted">Administrator dashboard</Badge>
      </div>
    </SlideShell>
  );
}

function ClosingSlide() {
  return (
    <SlideShell>
      <p className="animate-fade-up text-sm font-semibold uppercase tracking-[0.3em] text-muted">
        Past → Present → Simulated Future
      </p>
      <p className="animate-fade-up delay-1 mx-auto mt-6 max-w-xl text-lg text-foreground">
        CareerPilot does not just prepare students for one interview. It continuously learns how to guide every
        student toward their strongest possible career.
      </p>
      <h1 className="animate-fade-up delay-2 mt-9 text-projector-lg text-foreground">CareerPilot AI</h1>
      <p className="animate-fade-up delay-3 mt-3 text-projector text-gradient-brand">Your Career. Continuously Evolving.</p>
    </SlideShell>
  );
}

const STEP_ICONS: Record<Step, typeof Sparkles> = {
  opening: Sparkles,
  student: Sparkles,
  twin: Brain,
  weakness: Target,
  graphrag: GitBranch,
  care: ShieldCheck,
  mission: Rocket,
  assessment: CheckCircle2,
  interview: Mic,
  experiment: FlaskConical,
  research: Microscope,
  responsible: ShieldCheck,
  scale: Building2,
  closing: Mic,
};

function StepRenderer({ step, technicalView }: { step: Step; technicalView: boolean }) {
  switch (step) {
    case "opening":
      return <OpeningSlide />;
    case "student":
      return <StudentSlide technicalView={technicalView} />;
    case "twin":
      return <TwinSlide technicalView={technicalView} />;
    case "weakness":
      return <WeaknessSlide />;
    case "graphrag":
      return <GraphRagSlide technicalView={technicalView} />;
    case "care":
      return <CareSlide technicalView={technicalView} />;
    case "mission":
      return <MissionSlide />;
    case "assessment":
      return <AssessmentSlide />;
    case "interview":
      return <InterviewSlide technicalView={technicalView} />;
    case "experiment":
      return <ExperimentSlide />;
    case "research":
      return <ResearchSlide />;
    case "responsible":
      return <ResponsibleSlide />;
    case "scale":
      return <ScaleSlide />;
    case "closing":
      return <ClosingSlide />;
  }
}

function CompetitionShell() {
  const router = useRouter();
  const [stepIndex, setStepIndex] = useState(0);
  const [technicalView, setTechnicalView] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const step = STEPS[stepIndex];
  const Icon = STEP_ICONS[step];

  const next = useCallback(() => setStepIndex((i) => Math.min(i + 1, STEPS.length - 1)), []);
  const prev = useCallback(() => setStepIndex((i) => Math.max(i - 1, 0)), []);
  const reset = useCallback(() => setStepIndex(0), []);

  const toggleFullscreen = useCallback(() => {
    if (typeof document === "undefined") return;
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.().catch(() => undefined);
    } else {
      document.exitFullscreen?.().catch(() => undefined);
    }
  }, []);

  useEffect(() => {
    const handleChange = () => setIsFullscreen(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange", handleChange);
    return () => document.removeEventListener("fullscreenchange", handleChange);
  }, []);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight" || e.key === " ") {
        e.preventDefault();
        next();
      } else if (e.key === "ArrowLeft") {
        prev();
      } else if (e.key.toLowerCase() === "r") {
        reset();
      } else if (e.key.toLowerCase() === "f") {
        toggleFullscreen();
      } else if (e.key.toLowerCase() === "t") {
        setTechnicalView((v) => !v);
      } else if (e.key === "Escape") {
        router.push("/dashboard");
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [next, prev, reset, toggleFullscreen, router]);

  const progressPercent = useMemo(() => ((stepIndex + 1) / STEPS.length) * 100, [stepIndex]);

  return (
    <div className="bg-mesh fixed inset-0 z-50 flex flex-col text-foreground">
      <header className="flex items-center gap-3 border-b border-border bg-surface/60 px-6 py-3 backdrop-blur-xl">
        <Badge className="px-3 py-1 text-xs">{STEP_LABELS[step]}</Badge>
        <div className="flex-1">
          <Progress value={progressPercent} aria-label={`Presentation progress: step ${stepIndex + 1} of ${STEPS.length}`} />
        </div>
        <span className="text-xs font-medium tabular-nums text-muted">
          {stepIndex + 1} / {STEPS.length}
        </span>
        <Button variant="ghost" size="sm" onClick={() => setTechnicalView((v) => !v)} aria-pressed={technicalView}>
          {technicalView ? "General view" : "Technical view"}
        </Button>
        <Button variant="ghost" size="icon" onClick={toggleFullscreen} aria-label="Toggle fullscreen">
          {isFullscreen ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
        </Button>
        <Button variant="ghost" size="icon" onClick={() => router.push("/dashboard")} aria-label="Exit competition mode">
          <X className="h-4 w-4" />
        </Button>
      </header>

      <main className="flex-1 overflow-y-auto py-10">
        <div key={step} className="animate-fade-up h-full">
          <StepRenderer step={step} technicalView={technicalView} />
        </div>
      </main>

      <footer className="flex flex-col items-center gap-2 border-t border-border bg-surface/60 px-6 py-4 backdrop-blur-xl">
        <div className="flex items-center justify-center gap-3">
          <Button variant="outline" size="lg" onClick={prev} disabled={stepIndex === 0}>
            ← Previous
          </Button>
          <Button variant="ghost" size="lg" onClick={reset}>
            Reset
          </Button>
          <Button size="lg" onClick={next} disabled={stepIndex === STEPS.length - 1}>
            Next <Icon className="ml-1.5 h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
        <p className="pb-1 pt-1 text-center font-mono text-[10px] tracking-wide text-muted">
          → / Space next &nbsp;·&nbsp; ← previous &nbsp;·&nbsp; R reset &nbsp;·&nbsp; F fullscreen &nbsp;·&nbsp; T technical view &nbsp;·&nbsp; Esc exit
        </p>
      </footer>
    </div>
  );
}

export default function CompetitionPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background" role="status" aria-live="polite">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-brand" />
      </div>
    );
  }

  return <CompetitionShell />;
}
