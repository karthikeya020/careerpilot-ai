"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Bot,
  Calculator,
  Clock,
  Cpu,
  DollarSign,
  Eye,
  GitBranch,
  Network,
  ShieldCheck,
  UserCheck,
  Users,
} from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useCareExecutionDetail, useCareExecutions } from "@/hooks/use-trust-center";
import { cn, formatDateTime, titleCase } from "@/lib/utils";
import type { CareExecutionDetailOut, CareExecutionSummaryOut } from "@/types/api";

const ROUTE_LABELS: Record<string, string> = {
  deterministic: "Deterministic calculation",
  single_agent: "Single specialist",
  graphrag_agent: "GraphRAG retrieval",
  multi_agent: "Multi-agent council",
  critic_reflection: "Critic / reflection",
  human_review: "Human review recommended",
};

const ROUTE_ICONS: Record<string, typeof Bot> = {
  deterministic: Calculator,
  single_agent: Bot,
  graphrag_agent: Network,
  multi_agent: Users,
  critic_reflection: Eye,
  human_review: UserCheck,
};

const INFERENCE_LABELS: Record<string, string> = {
  deterministic_calculation: "Deterministic calculation",
  model_inference: "Model inference",
  extracted_fact: "Extracted fact",
  user_claim: "User claim",
};

const GRAPH_SOURCE_LABELS: Record<string, string> = {
  neo4j: "Neo4j graph",
  relational_fallback: "Relational fallback (Neo4j unavailable)",
};

function routeBadgeVariant(route: string): "default" | "warning" | "danger" | "muted" {
  if (route === "human_review") return "danger";
  if (route === "critic_reflection" || route === "multi_agent") return "warning";
  if (route === "deterministic") return "muted";
  return "default";
}

function ExecutionListItem({
  execution,
  selected,
  onSelect,
}: {
  execution: CareExecutionSummaryOut;
  selected: boolean;
  onSelect: () => void;
}) {
  const Icon = ROUTE_ICONS[execution.route] ?? Bot;
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "w-full rounded-[var(--radius-md)] border p-3 text-left text-sm transition-all",
        selected ? "border-brand bg-brand-soft shadow-[var(--shadow-glow-brand)]" : "border-border hover:bg-surface-muted hover:translate-x-0.5",
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 font-medium text-foreground">
          <Icon className="h-3.5 w-3.5 shrink-0 text-brand" aria-hidden="true" />
          {titleCase(execution.task_type)}
        </span>
        <Badge variant={routeBadgeVariant(execution.route)}>{ROUTE_LABELS[execution.route] ?? execution.route}</Badge>
      </div>
      <div className="mt-1 flex items-center justify-between text-xs text-muted">
        <span>Confidence {(execution.confidence * 100).toFixed(0)}%</span>
        <span>{formatDateTime(execution.created_at)}</span>
      </div>
    </button>
  );
}

function ExecutionTimeline({ detail }: { detail: CareExecutionDetailOut }) {
  const RouteIcon = ROUTE_ICONS[detail.route] ?? Bot;
  const steps: { icon: typeof Bot; label: string; sub?: string }[] = [
    { icon: GitBranch, label: "Task received", sub: titleCase(detail.task_type) },
    { icon: RouteIcon, label: "CARE route selected", sub: ROUTE_LABELS[detail.route] ?? detail.route },
    ...detail.agent_runs.map((run) => ({
      icon: Cpu,
      label: `${titleCase(run.agent_name)} ran`,
      sub: `${INFERENCE_LABELS[run.inference_type] ?? run.inference_type} · ${(run.confidence * 100).toFixed(0)}% confidence`,
    })),
    {
      icon: detail.requires_human_review ? UserCheck : ShieldCheck,
      label: detail.requires_human_review ? "Flagged for human review" : "Result finalized",
      sub: `${(detail.confidence * 100).toFixed(0)}% overall confidence`,
    },
  ];

  return (
    <div>
      {steps.map((step, i) => {
        const Icon = step.icon;
        const isLast = i === steps.length - 1;
        return (
          <div key={i} className="relative flex gap-3">
            <div className="flex flex-col items-center">
              <div
                className={cn("animate-scale-in flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 border-brand-soft bg-surface", `delay-${Math.min(i + 1, 8)}`)}
                style={{ boxShadow: "var(--shadow-sm)" }}
              >
                <Icon className="h-4 w-4 text-brand" aria-hidden="true" />
              </div>
              {!isLast && (
                <svg width="2" height="32" className="my-0.5" aria-hidden="true">
                  <line x1="1" y1="0" x2="1" y2="32" stroke="var(--color-border-strong)" strokeWidth="2" className="animate-draw-line" style={{ ["--line-length" as string]: 32, animationDelay: `${(i + 1) * 120}ms` }} />
                </svg>
              )}
            </div>
            <div className={cn("animate-fade-up min-w-0 flex-1 pb-4", `delay-${Math.min(i + 1, 8)}`)}>
              <p className="text-sm font-medium text-foreground">{step.label}</p>
              {step.sub && <p className="text-xs text-muted">{step.sub}</p>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ExecutionDetail({ executionId }: { executionId: string | null }) {
  const { data: detail, isLoading, isError, error, refetch } = useCareExecutionDetail(executionId);
  const [showTechnical, setShowTechnical] = useState(true);

  if (!executionId) {
    return <EmptyState icon={ShieldCheck} title="Select an execution" description="Choose an item from the list to see its full decision trace." />;
  }
  if (isLoading) return <Skeleton className="h-72" />;
  if (isError || !detail) {
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load execution detail."} onRetry={() => refetch()} />;
  }

  return (
    <div className="space-y-5">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={routeBadgeVariant(detail.route)}>{ROUTE_LABELS[detail.route] ?? detail.route}</Badge>
          {detail.retrieval_used && <Badge variant="muted">Retrieval used</Badge>}
          {detail.reflection_used && <Badge variant="warning">Reflection used</Badge>}
          {detail.requires_human_review && <Badge variant="danger">Human review recommended</Badge>}
        </div>
        <p className="mt-2 text-sm text-foreground">{detail.reasoning_summary}</p>
      </div>

      <div className="rounded-[var(--radius-lg)] border border-border bg-surface-muted/40 p-4">
        <p className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
          <Clock className="h-3.5 w-3.5" aria-hidden="true" /> Execution timeline
        </p>
        <ExecutionTimeline detail={detail} />
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[
          { label: "Confidence", value: `${(detail.confidence * 100).toFixed(0)}%` },
          { label: "Agreement", value: detail.agreement !== null ? `${(detail.agreement * 100).toFixed(0)}%` : "—" },
          { label: "Latency", value: `${detail.latency_ms.toFixed(0)} ms`, icon: Clock },
          { label: "Cost", value: `$${detail.cost_usd.toFixed(4)}`, icon: DollarSign },
          { label: "Policy version", value: detail.policy_version },
          { label: "Evidence used", value: String(detail.input_evidence_ids.length) },
        ].map((stat) => (
          <div key={stat.label} className="rounded-[var(--radius-md)] border border-border bg-surface px-3 py-2">
            <p className="text-sm font-semibold text-foreground">{stat.value}</p>
            <p className="text-[11px] text-muted">{stat.label}</p>
          </div>
        ))}
      </div>

      <div>
        <button
          type="button"
          onClick={() => setShowTechnical((o) => !o)}
          className="mb-2 flex items-center gap-1.5 text-sm font-medium text-foreground"
          aria-expanded={showTechnical}
        >
          <Cpu className="h-4 w-4 text-brand" aria-hidden="true" />
          Agents invoked ({detail.agent_runs.length})
        </button>
        {showTechnical &&
          (detail.agent_runs.length === 0 ? (
            <p className="text-xs text-muted">No specialist agents were invoked for this decision.</p>
          ) : (
            <ul className="space-y-2">
              {detail.agent_runs.map((run, i) => (
                <li key={run.id} className={cn("animate-fade-up rounded-[var(--radius-md)] bg-surface-muted p-3 text-xs", `delay-${Math.min(i + 1, 8)}`)}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-foreground">{titleCase(run.agent_name)}</span>
                    <Badge variant={run.status === "failed" ? "danger" : "muted"}>{run.status}</Badge>
                  </div>
                  <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-muted">
                    <span>{INFERENCE_LABELS[run.inference_type] ?? run.inference_type}</span>
                    <span>Confidence {(run.confidence * 100).toFixed(0)}%</span>
                    <span>{run.latency_ms.toFixed(0)} ms</span>
                    <span>Prompt {run.prompt_version}</span>
                  </div>
                  {run.evidence_citations.length > 0 && (
                    <p className="mt-1 text-muted">Evidence: {run.evidence_citations.length} citation(s)</p>
                  )}
                  {typeof run.output_payload?.graph_source === "string" && run.output_payload.graph_source && (
                    <p className="mt-1">
                      <Badge variant={run.output_payload.graph_source === "neo4j" ? "muted" : "warning"}>
                        {GRAPH_SOURCE_LABELS[run.output_payload.graph_source] ?? run.output_payload.graph_source}
                      </Badge>
                    </p>
                  )}
                </li>
              ))}
            </ul>
          ))}
      </div>
    </div>
  );
}

function TrustCenterBody() {
  const searchParams = useSearchParams();
  const { data: executions, isLoading, isError, error, refetch } = useCareExecutions();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const effectiveSelectedId = selectedId ?? searchParams.get("execution") ?? executions?.[0]?.id ?? null;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
            <ShieldCheck className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">AI Trust Center</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Every AI-assisted decision CareerPilot makes is routed by the CARE engine and logged here: which route was
          chosen, which specialist agents ran, what evidence was used, and the confidence behind it.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-[minmax(0,320px)_1fr]">
        <Card>
          <CardHeader className="flex-row items-center gap-2">
            <GitBranch className="h-4 w-4 text-brand" aria-hidden="true" />
            <CardTitle as="h2">Recent decisions</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-56" />
            ) : isError ? (
              <ErrorState message={error instanceof Error ? error.message : "Couldn't load executions."} onRetry={() => refetch()} />
            ) : !executions || executions.length === 0 ? (
              <EmptyState
                icon={ShieldCheck}
                title="No AI decisions yet"
                description="Complete an assessment or upload a resume to generate the first CARE-routed decision."
              />
            ) : (
              <div className="space-y-2">
                {executions.map((execution) => (
                  <ExecutionListItem
                    key={execution.id}
                    execution={execution}
                    selected={execution.id === effectiveSelectedId}
                    onSelect={() => setSelectedId(execution.id)}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card variant="glow-brand">
          <CardHeader>
            <CardTitle as="h2">Decision trace</CardTitle>
            <CardDescription>Route, agents, evidence, and confidence for the selected decision.</CardDescription>
          </CardHeader>
          <CardContent>
            <ExecutionDetail executionId={effectiveSelectedId} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function TrustCenterPage() {
  return (
    <Protected>
      <Suspense fallback={<Skeleton className="h-96" />}>
        <TrustCenterBody />
      </Suspense>
    </Protected>
  );
}
