"use client";

import Link from "next/link";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  Briefcase,
  ChevronDown,
  ChevronRight,
  Database,
  FileQuestion,
  GitBranch,
  Layers,
  Network,
  ShieldCheck,
  Sparkles,
  Target,
  ThumbsUp,
  TrendingDown,
  User,
  Wrench,
} from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ConceptDetailPanel } from "@/components/graphrag/concept-detail-panel";
import { KnowledgeGraph, KnowledgeGraphLegend } from "@/components/graphrag/knowledge-graph";
import { useGraphHealth, useRootCause, useStudentGraphOverview } from "@/hooks/use-graphrag";
import { useResources } from "@/hooks/use-resources";
import { ApiError } from "@/lib/api-client";
import { cn, formatPercent } from "@/lib/utils";
import type { ConceptInsightOut, GraphPathStepOut } from "@/types/api";

// ============================================================================
// Per-question root-cause chain -- unchanged deep-link view, reachable via
// ?question=<id> from Interview Arena / Assessment Arena "See root cause"
// links. The default GraphRAG experience below (StudentOverview) never
// redirects here or anywhere else.
// ============================================================================

const STEP_META: Record<
  GraphPathStepOut["step_type"],
  { icon: typeof User; label: string; color: string; ring: string }
> = {
  student: { icon: User, label: "You", color: "var(--color-muted)", ring: "border-border-strong" },
  question: { icon: FileQuestion, label: "Missed question", color: "var(--color-warning)", ring: "border-warning/40" },
  concept: { icon: Layers, label: "Weak concept", color: "var(--color-danger)", ring: "border-danger/50" },
  concept_dependency: { icon: GitBranch, label: "Missing prerequisite", color: "var(--color-warning)", ring: "border-warning/40" },
  job_role: { icon: Briefcase, label: "Target-role requirement", color: "var(--color-accent-2)", ring: "border-accent-2/40" },
  resource: { icon: Wrench, label: "Recommended intervention", color: "var(--color-positive)", ring: "border-positive/40" },
  inference: { icon: Sparkles, label: "Model inference", color: "var(--color-brand-2)", ring: "border-brand-2/40" },
};

function GraphPathNode({
  step,
  index,
  isRootCause,
  isLast,
}: {
  step: GraphPathStepOut;
  index: number;
  isRootCause: boolean;
  isLast: boolean;
}) {
  const meta = STEP_META[step.step_type];
  const Icon = meta.icon;
  const delayClass = `delay-${Math.min(index + 1, 8)}`;

  return (
    <div className="relative flex gap-4">
      <div className="flex flex-col items-center">
        <div
          className={cn(
            "animate-scale-in relative flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 bg-surface",
            meta.ring,
            delayClass,
          )}
          style={{ boxShadow: isRootCause ? "var(--shadow-glow-brand)" : "var(--shadow-sm)" }}
        >
          <Icon className="h-5 w-5" style={{ color: meta.color }} aria-hidden="true" />
          {isRootCause && (
            <span className="absolute -inset-1.5 animate-pulse-glow rounded-full ring-2 ring-brand/50" aria-hidden="true" />
          )}
        </div>
        {!isLast && (
          <svg width="2" height="48" className="my-0.5" aria-hidden="true">
            <line
              x1="1"
              y1="0"
              x2="1"
              y2="48"
              stroke="var(--color-border-strong)"
              strokeWidth="2"
              strokeDasharray={step.is_inference ? "3 4" : undefined}
              className="animate-draw-line"
              style={{ ["--line-length" as string]: 48, animationDelay: `${(index + 1) * 140}ms` }}
            />
          </svg>
        )}
      </div>
      <div className={cn("animate-fade-up min-w-0 flex-1 pb-6", delayClass)}>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wide text-muted">{meta.label}</span>
          {isRootCause && <Badge variant="danger">Root cause</Badge>}
          {step.is_inference && (
            <Badge variant="muted" className="gap-1">
              <Sparkles className="h-3 w-3" aria-hidden="true" /> Model inference
            </Badge>
          )}
          {!step.is_inference && step.node_id && (
            <Badge variant="outline" className="gap-1">
              <Database className="h-3 w-3" aria-hidden="true" /> Stored fact
            </Badge>
          )}
        </div>
        <p className="mt-1 text-base font-medium text-foreground">{step.label}</p>
      </div>
    </div>
  );
}

function TechnicalView({ path, graphSource, conceptSlug }: { path: GraphPathStepOut[]; graphSource: string; conceptSlug: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-t border-border pt-4">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between text-left text-sm font-medium text-foreground"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2">
          <Database className="h-4 w-4 text-brand" aria-hidden="true" /> Technical view
        </span>
        <ChevronDown className={cn("h-4 w-4 text-muted transition-transform", open && "rotate-180")} aria-hidden="true" />
      </button>
      {open && (
        <div className="animate-fade-in mt-3 space-y-2 rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 font-mono text-xs text-muted">
          <p>
            graph_source: <span className="text-foreground">{graphSource}</span>
          </p>
          <p>
            concept_slug: <span className="text-foreground">{conceptSlug}</span>
          </p>
          <div className="divider-fade" />
          {path.map((step, i) => (
            <p key={i}>
              [{i}] {step.step_type} &middot; node_id={step.node_id ?? "null"} &middot; is_inference={String(step.is_inference)}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

function RootCauseView({ questionId }: { questionId: string }) {
  const { data: health } = useGraphHealth();
  const { data: result, isLoading, isError, error, refetch } = useRootCause(questionId);
  const { data: resources } = useResources();

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (isError || !result) {
    const isNotFound = error instanceof ApiError && error.status === 404;
    return (
      <div className="mx-auto max-w-3xl">
        <ErrorState
          titleAs="h1"
          title={isNotFound ? "No root-cause analysis yet" : undefined}
          message={
            isNotFound
              ? "This question hasn't been analyzed yet."
              : error instanceof Error
                ? error.message
                : "Couldn't load the GraphRAG root-cause chain."
          }
          onRetry={isNotFound ? undefined : () => refetch()}
        />
      </div>
    );
  }

  const isDegraded = result.graph_source === "relational_fallback";
  const rootCauseIndex = result.path.findIndex((s) => s.step_type === "concept");
  const linkedResources = resources?.filter((r) => result.recommended_resource_ids.includes(r.id)) ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="animate-fade-up space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Link href="/graphrag" className="flex items-center gap-1 text-xs font-medium text-muted hover:text-foreground">
            <Network className="h-3.5 w-3.5" aria-hidden="true" /> Back to your knowledge graph
          </Link>
        </div>
        <h1 className="text-h1 text-foreground">Root cause for this question</h1>
        <p className="max-w-2xl text-sm text-muted">
          The system traced why this answer was wrong back through your knowledge graph -- from the missed question,
          to the weak concept, to what it depends on, to why your target role needs it, to what closes the gap.
        </p>
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <Badge variant={isDegraded ? "warning" : "muted"} className="gap-1">
            <Database className="h-3 w-3" aria-hidden="true" />
            {isDegraded ? "Relational fallback (Neo4j unavailable)" : "Neo4j graph database"}
          </Badge>
          <Badge variant="outline">Confidence {formatPercent(result.confidence)}</Badge>
          {health && !health.available && !isDegraded && <Badge variant="warning">Graph service degraded</Badge>}
        </div>
      </div>

      {result.missing_context_warning && (
        <div className="animate-fade-up delay-1 flex items-start gap-2 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-3 text-sm text-foreground">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden="true" />
          <p>Part of this chain relies on limited graph context. Treat the connections below as directionally correct, not exhaustive.</p>
        </div>
      )}

      <Card variant="glow-brand" className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-radial-brand opacity-40" aria-hidden="true" />
        <CardContent className="relative pt-6">
          {result.path.map((step, i) => (
            <GraphPathNode key={i} step={step} index={i} isRootCause={i === rootCauseIndex} isLast={i === result.path.length - 1} />
          ))}
          <TechnicalView path={result.path} graphSource={result.graph_source} conceptSlug={result.concept_slug} />
        </CardContent>
      </Card>

      {result.target_role_relevance.length > 0 && (
        <Card className="animate-fade-up delay-2">
          <CardContent className="space-y-2 pt-5">
            <h2 className="flex items-center gap-2 text-h3 text-foreground">
              <Briefcase className="h-4 w-4 text-accent-2" aria-hidden="true" /> Why your target role cares
            </h2>
            <ul className="list-inside list-disc space-y-1 text-sm text-muted">
              {result.target_role_relevance.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {linkedResources.length > 0 && (
        <Card className="animate-fade-up delay-3">
          <CardContent className="space-y-3 pt-5">
            <h2 className="flex items-center gap-2 text-h3 text-foreground">
              <Wrench className="h-4 w-4 text-positive" aria-hidden="true" /> Recommended interventions
            </h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {linkedResources.map((res) => (
                <a key={res.id} href={res.url} target="_blank" rel="noreferrer" className="card-premium card-premium-hover block rounded-[var(--radius-md)] p-3">
                  <p className="text-sm font-medium text-foreground">{res.title}</p>
                  <p className="mt-0.5 text-xs text-muted">
                    {res.provider} &middot; {res.duration_minutes} min &middot; difficulty {res.difficulty}/5
                  </p>
                </a>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <p className="flex items-center gap-1.5 text-xs text-muted">
        <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
        Every step above is either a stored graph fact or explicitly labeled as a model inference -- nothing here is fabricated.
      </p>
    </div>
  );
}

// ============================================================================
// Default view: the student's whole knowledge graph, insights, reasoning,
// and embedded practice -- this page's own experience, no redirects.
// ============================================================================

function InsightRow({ insight, onOpen, isOpen }: { insight: ConceptInsightOut; onOpen: () => void; isOpen: boolean }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className={cn(
        "flex w-full items-center justify-between gap-2 rounded-[var(--radius-md)] border p-3 text-left transition-colors",
        isOpen ? "border-brand bg-brand-soft/50" : "border-border hover:bg-surface-muted",
      )}
    >
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-foreground">{insight.concept_name}</p>
        <p className="truncate text-xs text-muted">{insight.domain_name}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {insight.mastery !== null && <span className="text-xs font-semibold tabular-nums text-foreground">{formatPercent(insight.mastery)}</span>}
        <ChevronRight className="h-4 w-4 text-muted" aria-hidden="true" />
      </div>
    </button>
  );
}

function StudentOverview() {
  const { data, isLoading, isError, error, refetch } = useStudentGraphOverview();
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-6">
        <Skeleton className="h-40" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto max-w-3xl">
        <ErrorState
          titleAs="h1"
          message={error instanceof Error ? error.message : "Couldn't load your knowledge graph."}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  const isDegraded = data.graph_source === "relational_fallback";

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
            <Network className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Your Knowledge Graph</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Every concept you could be evaluated on, mapped by prerequisite dependency, colored by how well the
          evidence says you actually know it. Click any concept for the full reasoning -- and to practice it,
          right here.
        </p>
        <div className="relative mt-5 flex flex-wrap items-center gap-2">
          <Badge variant={isDegraded ? "warning" : "muted"} className="gap-1">
            <Database className="h-3 w-3" aria-hidden="true" />
            {isDegraded ? "Relational fallback (Neo4j unavailable)" : "Neo4j graph database"}
          </Badge>
          <Badge className="gap-1">
            <Target className="h-3 w-3" aria-hidden="true" />
            {data.concepts_with_evidence}/{data.total_concepts} concepts assessed
          </Badge>
          {data.overall_mastery !== null && <Badge variant="outline">Overall mastery {formatPercent(data.overall_mastery)}</Badge>}
          {data.target_role_title && (
            <Badge variant="outline" className="gap-1">
              <Briefcase className="h-3 w-3" aria-hidden="true" /> Target role: {data.target_role_title}
            </Badge>
          )}
        </div>
      </div>

      <Card className="animate-fade-up delay-1">
        <CardContent className="space-y-3 pt-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="flex items-center gap-2 text-h3 text-foreground">
              <Network className="h-4 w-4 text-brand" aria-hidden="true" /> The graph
            </h2>
            <KnowledgeGraphLegend />
          </div>
          <KnowledgeGraph nodes={data.nodes} edges={data.edges} selectedSlug={selectedSlug} onSelectNode={setSelectedSlug} />
        </CardContent>
      </Card>

      {selectedSlug && (
        <ConceptDetailPanel slug={selectedSlug} onClose={() => setSelectedSlug(null)} onDataChanged={() => refetch()} />
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="animate-fade-up delay-2">
          <CardContent className="space-y-3 pt-6">
            <h2 className="flex items-center gap-2 text-h3 text-foreground">
              <TrendingDown className="h-4 w-4 text-danger" aria-hidden="true" /> Where you're weak, and why
            </h2>
            {data.weaknesses.length === 0 ? (
              <p className="text-xs text-muted">
                No confirmed weak concepts yet -- keep practicing and answering assessment questions to build real
                evidence here.
              </p>
            ) : (
              <div className="space-y-2">
                {data.weaknesses.map((w) => (
                  <InsightRow key={w.concept_slug} insight={w} isOpen={selectedSlug === w.concept_slug} onOpen={() => setSelectedSlug(w.concept_slug)} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="animate-fade-up delay-3">
          <CardContent className="space-y-3 pt-6">
            <h2 className="flex items-center gap-2 text-h3 text-foreground">
              <ThumbsUp className="h-4 w-4 text-positive" aria-hidden="true" /> Where you're strong
            </h2>
            {data.strengths.length === 0 ? (
              <p className="text-xs text-muted">No confirmed strengths yet -- they'll appear here as evidence accumulates.</p>
            ) : (
              <div className="space-y-2">
                {data.strengths.map((s) => (
                  <InsightRow key={s.concept_slug} insight={s} isOpen={selectedSlug === s.concept_slug} onOpen={() => setSelectedSlug(s.concept_slug)} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <p className="flex items-center gap-1.5 text-xs text-muted">
        <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
        Every concept's status comes from real stored evidence, or is honestly labeled "not assessed yet" -- nothing
        on this graph is a guess.
      </p>
    </div>
  );
}

function GraphRagContent() {
  const params = useSearchParams();
  const questionId = params.get("question");
  return questionId ? <RootCauseView questionId={questionId} /> : <StudentOverview />;
}

export default function GraphRagPage() {
  return (
    <Protected>
      <Suspense fallback={<Skeleton className="h-96" />}>
        <GraphRagContent />
      </Suspense>
    </Protected>
  );
}
