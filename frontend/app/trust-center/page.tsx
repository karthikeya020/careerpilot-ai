"use client";

import { useState } from "react";
import { Cpu, GitBranch, ShieldCheck } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useCareExecutionDetail, useCareExecutions } from "@/hooks/use-trust-center";
import { formatDateTime, titleCase } from "@/lib/utils";
import type { CareExecutionSummaryOut } from "@/types/api";

const ROUTE_LABELS: Record<string, string> = {
  deterministic: "Deterministic calculation",
  single_agent: "Single specialist",
  graphrag_agent: "GraphRAG retrieval",
  multi_agent: "Multi-agent council",
  critic_reflection: "Critic / reflection",
  human_review: "Human review recommended",
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
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-[var(--radius-md)] border p-3 text-left text-sm transition-colors ${
        selected ? "border-brand bg-brand/5" : "border-border hover:bg-surface-muted"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-foreground">{titleCase(execution.task_type)}</span>
        <Badge variant={routeBadgeVariant(execution.route)}>{ROUTE_LABELS[execution.route] ?? execution.route}</Badge>
      </div>
      <div className="mt-1 flex items-center justify-between text-xs text-muted">
        <span>Confidence {(execution.confidence * 100).toFixed(0)}%</span>
        <span>{formatDateTime(execution.created_at)}</span>
      </div>
    </button>
  );
}

function ExecutionDetail({ executionId }: { executionId: string | null }) {
  const { data: detail, isLoading, isError, error, refetch } = useCareExecutionDetail(executionId);

  if (!executionId) {
    return <EmptyState title="Select an execution" description="Choose an item from the list to see its full decision trace." />;
  }
  if (isLoading) return <Skeleton className="h-72" />;
  if (isError || !detail) {
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load execution detail."} onRetry={() => refetch()} />;
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant={routeBadgeVariant(detail.route)}>{ROUTE_LABELS[detail.route] ?? detail.route}</Badge>
          {detail.retrieval_used && <Badge variant="muted">Retrieval used</Badge>}
          {detail.reflection_used && <Badge variant="warning">Reflection used</Badge>}
          {detail.requires_human_review && <Badge variant="danger">Human review recommended</Badge>}
        </div>
        <p className="mt-2 text-sm text-foreground">{detail.reasoning_summary}</p>
      </div>

      <dl className="grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
        <div>
          <dt className="text-muted">Confidence</dt>
          <dd className="font-medium text-foreground">{(detail.confidence * 100).toFixed(0)}%</dd>
        </div>
        <div>
          <dt className="text-muted">Agreement</dt>
          <dd className="font-medium text-foreground">{detail.agreement !== null ? `${(detail.agreement * 100).toFixed(0)}%` : "—"}</dd>
        </div>
        <div>
          <dt className="text-muted">Latency</dt>
          <dd className="font-medium text-foreground">{detail.latency_ms.toFixed(0)} ms</dd>
        </div>
        <div>
          <dt className="text-muted">Cost</dt>
          <dd className="font-medium text-foreground">${detail.cost_usd.toFixed(4)}</dd>
        </div>
        <div>
          <dt className="text-muted">Policy version</dt>
          <dd className="font-medium text-foreground">{detail.policy_version}</dd>
        </div>
        <div>
          <dt className="text-muted">Evidence used</dt>
          <dd className="font-medium text-foreground">{detail.input_evidence_ids.length}</dd>
        </div>
      </dl>

      <div>
        <h3 className="mb-2 flex items-center gap-1.5 text-sm font-medium text-foreground">
          <Cpu className="h-4 w-4 text-brand" aria-hidden="true" />
          Agents invoked ({detail.agent_runs.length})
        </h3>
        {detail.agent_runs.length === 0 ? (
          <p className="text-xs text-muted">No specialist agents were invoked for this decision.</p>
        ) : (
          <ul className="space-y-2">
            {detail.agent_runs.map((run) => (
              <li key={run.id} className="rounded-[var(--radius-md)] bg-surface-muted p-3 text-xs">
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
        )}
      </div>
    </div>
  );
}

function TrustCenterBody() {
  const { data: executions, isLoading, isError, error, refetch } = useCareExecutions();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const effectiveSelectedId = selectedId ?? executions?.[0]?.id ?? null;

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
          <ShieldCheck className="h-5 w-5 text-positive" aria-hidden="true" />
          AI Trust Center
        </h1>
        <p className="mt-1 text-sm text-muted">
          Every AI-assisted decision CareerPilot makes is routed by the CARE engine and logged here: which route was
          chosen, which specialist agents ran, what evidence was used, and the confidence behind it.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-[minmax(0,320px)_1fr]">
        <Card>
          <CardHeader className="flex-row items-center gap-2">
            <GitBranch className="h-4 w-4 text-brand" aria-hidden="true" />
            <CardTitle>Recent decisions</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-56" />
            ) : isError ? (
              <ErrorState message={error instanceof Error ? error.message : "Couldn't load executions."} onRetry={() => refetch()} />
            ) : !executions || executions.length === 0 ? (
              <EmptyState
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

        <Card>
          <CardHeader>
            <CardTitle>Decision trace</CardTitle>
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
      <TrustCenterBody />
    </Protected>
  );
}
