"use client";

import Link from "next/link";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { AlertTriangle, FileDown, FlaskConical, GraduationCap, Microscope, ScrollText } from "lucide-react";
import { toast } from "sonner";
import { LiveCriticTogglePanel } from "@/components/research/live-critic-toggle-panel";
import {
  AdversarialSuiteCard,
  DriftCanaryCard,
  EfficiencyFrontierCard,
  FairnessProbeCard,
  FallbackFidelityCard,
  ThresholdTuningCard,
  useRobustnessPanels,
} from "@/components/research/robustness-panels";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useCalibration,
  useEvaluationRuns,
  useRunAblationSuite,
  useRunGraphVsVectorExperiment,
  useRunRoutingExperiment,
} from "@/hooks/use-research-lab";
import { ApiError } from "@/lib/api-client";
import { cn, formatDateTime } from "@/lib/utils";
import type { AblationSuiteOut, GraphVsVectorExperimentOut, RoutingExperimentOut } from "@/types/api";

type ViewMode = "general" | "technical";

const VARIANT_LABELS: Record<string, string> = {
  single_agent_fixed: "Single agent (fixed)",
  multi_agent_fixed: "Multi-agent (fixed)",
  care_adaptive: "CARE adaptive",
};

function SimpleBarChart({ data, unit = "%" }: { data: { label: string; value: number }[]; unit?: string }) {
  return (
    <div className="h-56 w-full" role="img" aria-label={`Bar chart: ${data.map((d) => `${d.label} ${d.value}${unit}`).join(", ")}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
          <XAxis dataKey="label" tick={{ fill: "var(--color-muted)", fontSize: 11 }} />
          <YAxis tick={{ fill: "var(--color-muted)", fontSize: 11 }} domain={[0, 100]} />
          <Bar dataKey="value" fill="var(--color-brand)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function RoutingResultCard({ result }: { result: RoutingExperimentOut }) {
  const data = Object.entries(result.agreement_rate_by_variant).map(([variant, rate]) => ({
    label: VARIANT_LABELS[variant] ?? variant,
    value: Math.round(rate * 100),
  }));
  return (
    <Card variant="glow-brand" className="animate-scale-in">
      <CardHeader>
        <CardTitle as="h2">Experiment A: routing-strategy agreement with rubric labels</CardTitle>
        <CardDescription>{result.case_count} curated cases -- higher agreement means the strategy routed the way a reviewer would expect.</CardDescription>
      </CardHeader>
      <CardContent>
        <SimpleBarChart data={data} />
        <p className="mt-2 flex items-center gap-1.5 text-xs text-muted">
          <Badge variant="warning">Preliminary</Badge>
          Sample size: {result.case_count} cases — a small curated dataset, not a large human-reviewed benchmark.
        </p>
      </CardContent>
    </Card>
  );
}

function GraphVsVectorResultCard({ result }: { result: GraphVsVectorExperimentOut }) {
  const data = [
    { label: "Graph traversal", value: Math.round((result.graph_traversal_accuracy ?? 0) * 100) },
    { label: "Vector-only", value: Math.round((result.vector_only_accuracy ?? 0) * 100) },
  ];
  return (
    <Card variant="glow-brand" className="animate-scale-in">
      <CardHeader>
        <CardTitle as="h2">Experiment B: GraphRAG traversal vs vector-only retrieval</CardTitle>
        <CardDescription>Does the retrieval method surface the correct prerequisite concept behind a missed question?</CardDescription>
      </CardHeader>
      <CardContent>
        <SimpleBarChart data={data} />
        <p className="mt-2 text-xs text-muted">{result.methodology_note}</p>
        <p className="mt-1 flex items-center gap-1.5 text-xs text-warning">
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" /> {result.sample_size_warning}
        </p>
      </CardContent>
    </Card>
  );
}

const SEAM_LABELS: Record<string, string> = {
  "1_care_disabled_vs_enabled": "1. CARE routing",
  "2_graph_retrieval_disabled_vs_enabled": "2. Graph retrieval",
  "3_vector_retrieval_disabled_vs_enabled": "3. Vector retrieval",
  "4_career_twin_memory_disabled_vs_enabled": "4. Career Twin memory",
  "5_reflection_disabled_vs_enabled": "5. Reflection (critic)",
  "6_consensus_disabled_vs_enabled": "6. Consensus",
};

function pct(value: unknown): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "—";
}

function AblationSeamCard({ seamKey, seam, mode }: { seamKey: string; seam: Record<string, unknown>; mode: ViewMode }) {
  const label = SEAM_LABELS[seamKey] ?? seamKey;
  const rows = mode === "technical" && Array.isArray(seam.rows) ? (seam.rows as Record<string, unknown>[]) : null;

  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted/30 p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-semibold text-foreground">{label}</p>
        {seam.preliminary === true && <Badge variant="warning">Preliminary</Badge>}
      </div>

      {seamKey === "1_care_disabled_vs_enabled" && !!seam.agreement_rate_by_variant && (
        <div className="mt-2 flex flex-wrap gap-3 text-xs">
          {Object.entries(seam.agreement_rate_by_variant as Record<string, number>).map(([variant, rate]) => (
            <span key={variant}>
              <span className="text-muted">{VARIANT_LABELS[variant] ?? variant}:</span>{" "}
              <span className="font-medium text-foreground">{pct(rate)}</span>
            </span>
          ))}
        </div>
      )}

      {seamKey === "2_graph_retrieval_disabled_vs_enabled" && (
        <p className="mt-2 text-xs">
          <span className="text-muted">Graph enabled:</span> <span className="font-medium text-foreground">{pct(seam.graph_enabled_accuracy)}</span>
          <span className="mx-2 text-muted">vs</span>
          <span className="text-muted">graph disabled (vector-only):</span> <span className="font-medium text-foreground">{pct(seam.graph_disabled_accuracy)}</span>
        </p>
      )}

      {seamKey === "3_vector_retrieval_disabled_vs_enabled" && (
        <p className="mt-2 text-xs">
          <span className="text-muted">Vector enabled:</span> <span className="font-medium text-foreground">{pct(seam.vector_enabled_accuracy)}</span>
          <span className="mx-2 text-muted">vs</span>
          <span className="text-muted">vector disabled (graph-only):</span> <span className="font-medium text-foreground">{pct(seam.vector_disabled_accuracy)}</span>
        </p>
      )}

      {rows && rows.length > 0 && (
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-muted">
                <th className="pr-3 font-medium">Case</th>
                <th className="pr-3 font-medium">Disabled</th>
                <th className="pr-3 font-medium">Enabled</th>
                <th className="font-medium">Delta</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => {
                const disabled = row.raw_mean_confidence ?? row.memory_disabled_consensus_confidence;
                const enabled = row.critic_adjusted_confidence ?? row.consensus_confidence ?? row.memory_enabled_consensus_confidence;
                const delta = row.delta;
                return (
                  <tr key={i} className="border-t border-border/60">
                    <td className="py-1 pr-3 text-foreground">{String(row.case_id ?? "—")}</td>
                    <td className="pr-3 text-muted">{pct(disabled)}</td>
                    <td className="pr-3 text-muted">{enabled !== undefined ? pct(enabled) : "n/a"}</td>
                    <td className="text-foreground">
                      {/* Not colored red/green: a negative delta here is often the seam working as
                          intended (e.g. consensus/reflection correctly penalizing overconfidence),
                          not a regression -- see each seam's "finding" text below for what it means. */}
                      {typeof delta === "number" ? `${delta >= 0 ? "+" : ""}${Math.round(delta * 100)}pp` : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {typeof seam.finding === "string" && <p className="mt-2 text-xs text-muted">{seam.finding}</p>}
    </div>
  );
}

function AblationSuiteCard({ result, mode }: { result: AblationSuiteOut; mode: ViewMode }) {
  return (
    <Card variant="glow-brand" className="animate-scale-in">
      <CardHeader>
        <CardTitle as="h2">Six-ablation comparison</CardTitle>
        <CardDescription>{result.methodology_note}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {Object.entries(result.ablations).map(([key, seam]) => (
          <AblationSeamCard key={key} seamKey={key} seam={seam} mode={mode} />
        ))}
      </CardContent>
    </Card>
  );
}

function ResearchLabBody() {
  const runRouting = useRunRoutingExperiment();
  const runGraphVsVector = useRunGraphVsVectorExperiment();
  const runAblations = useRunAblationSuite();
  const { data: runs, isLoading: runsLoading } = useEvaluationRuns();
  const { data: calibration, isLoading: calibrationLoading } = useCalibration();

  const [routingResult, setRoutingResult] = useState<RoutingExperimentOut | null>(null);
  const [graphVsVectorResult, setGraphVsVectorResult] = useState<GraphVsVectorExperimentOut | null>(null);
  const [ablationResult, setAblationResult] = useState<AblationSuiteOut | null>(null);
  const [mode, setMode] = useState<ViewMode>("general");

  const handleRunRouting = () => {
    runRouting.mutate(undefined, {
      onSuccess: (data) => setRoutingResult(data),
      onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't run the routing experiment."),
    });
  };

  const handleRunGraphVsVector = () => {
    runGraphVsVector.mutate(undefined, {
      onSuccess: (data) => setGraphVsVectorResult(data),
      onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't run the retrieval experiment."),
    });
  };

  const handleRunAblations = () => {
    runAblations.mutate(undefined, {
      onSuccess: (data) => setAblationResult(data),
      onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't run the ablation suite."),
    });
  };

  const robustness = useRobustnessPanels();

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
                <Microscope className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
              </span>
              <h1 className="text-h1 text-foreground">Research Benchmark Lab</h1>
            </div>
            <p className="mt-3 max-w-2xl text-sm text-muted">
              Why is CareerPilot more intelligent than one generic chatbot? Real, reproducible comparisons — run
              them yourself below. Sample sizes and limitations are shown, never hidden.
            </p>
            <Button size="sm" variant="outline" className="mt-4" asChild>
              <Link href="/research-lab/report">
                <FileDown className="h-3.5 w-3.5" aria-hidden="true" /> Export full research report
              </Link>
            </Button>
          </div>
          <div className="flex shrink-0 rounded-[var(--radius-md)] border border-border bg-surface p-1">
            <button
              type="button"
              onClick={() => setMode("general")}
              className={cn(
                "flex items-center gap-1.5 rounded-[var(--radius-sm)] px-3 py-1.5 text-xs font-medium transition-colors",
                mode === "general" ? "bg-gradient-brand text-brand-foreground" : "text-muted hover:text-foreground",
              )}
              aria-pressed={mode === "general"}
            >
              <GraduationCap className="h-3.5 w-3.5" aria-hidden="true" /> General audience
            </button>
            <button
              type="button"
              onClick={() => setMode("technical")}
              className={cn(
                "flex items-center gap-1.5 rounded-[var(--radius-sm)] px-3 py-1.5 text-xs font-medium transition-colors",
                mode === "technical" ? "bg-gradient-brand text-brand-foreground" : "text-muted hover:text-foreground",
              )}
              aria-pressed={mode === "technical"}
            >
              <ScrollText className="h-3.5 w-3.5" aria-hidden="true" /> Technical judge
            </button>
          </div>
        </div>
      </div>

      {mode === "general" && (
        <div className="animate-fade-up delay-1 rounded-[var(--radius-lg)] border border-brand-soft bg-brand-soft/40 p-4 text-sm text-foreground">
          CareerPilot doesn&apos;t rely on a single generic prompt. It routes each task through CARE (Confidence-Aware
          Routing Engine) to the right specialist agent, grounds answers in a real knowledge graph instead of guessing,
          and checks agents against each other before trusting a result. The experiments below measure each of those
          design choices against a simpler baseline, one at a time.
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        <Button onClick={handleRunRouting} disabled={runRouting.isPending}>
          <FlaskConical className="h-3.5 w-3.5" aria-hidden="true" />
          {runRouting.isPending ? "Running..." : "Run Experiment A: routing strategies"}
        </Button>
        <Button variant="outline" onClick={handleRunGraphVsVector} disabled={runGraphVsVector.isPending}>
          <FlaskConical className="h-3.5 w-3.5" aria-hidden="true" />
          {runGraphVsVector.isPending ? "Running..." : "Run Experiment B: graph vs vector"}
        </Button>
        <Button variant="outline" onClick={handleRunAblations} disabled={runAblations.isPending}>
          <FlaskConical className="h-3.5 w-3.5" aria-hidden="true" />
          {runAblations.isPending ? "Running..." : "Run all 6 ablations"}
        </Button>
      </div>

      {routingResult && <RoutingResultCard result={routingResult} />}
      {graphVsVectorResult && <GraphVsVectorResultCard result={graphVsVectorResult} />}
      {ablationResult && <AblationSuiteCard result={ablationResult} mode={mode} />}

      <Card className="animate-fade-up">
        <CardHeader>
          <CardTitle as="h2">Robustness &amp; validation suite</CardTitle>
          <CardDescription>
            Efficiency frontier, empirical threshold tuning, adversarial inputs, fallback fidelity, fairness
            probing, and scoring-drift detection -- all real, all reproducible.
          </CardDescription>
        </CardHeader>
        <CardContent>{robustness.buttons}</CardContent>
      </Card>

      {robustness.efficiency.data && <EfficiencyFrontierCard result={robustness.efficiency.data} />}
      {robustness.thresholds.data && <ThresholdTuningCard result={robustness.thresholds.data} />}
      {robustness.adversarial.data && <AdversarialSuiteCard result={robustness.adversarial.data} />}
      {robustness.fidelity.data && <FallbackFidelityCard result={robustness.fidelity.data} />}
      {robustness.fairness.data && <FairnessProbeCard result={robustness.fairness.data} />}
      {robustness.drift.data && <DriftCanaryCard result={robustness.drift.data} />}

      <LiveCriticTogglePanel />

      <Card>
        <CardHeader>
          <CardTitle as="h2">Confidence calibration</CardTitle>
          <CardDescription>How well does stated confidence match actual accuracy, across all runs so far?</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {calibrationLoading ? (
            <Skeleton className="h-32" />
          ) : !calibration || calibration.sample_size === 0 ? (
            <EmptyState title="No evaluation results yet" description="Run an experiment above to generate calibration data." />
          ) : (
            <>
              {calibration.preliminary && (
                <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2 text-xs text-warning">
                  <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                  Preliminary: only {calibration.sample_size} labeled result(s) so far (30+ recommended for a stable estimate).
                </div>
              )}
              {mode === "technical" && (
                <div className="grid grid-cols-2 gap-4 text-center sm:grid-cols-4">
                  <div>
                    <p className="text-lg font-semibold text-foreground">{calibration.sample_size}</p>
                    <p className="text-[11px] text-muted">Sample size</p>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-foreground">{calibration.brier_score?.toFixed(3) ?? "—"}</p>
                    <p className="text-[11px] text-muted">Brier score (lower is better)</p>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-foreground">{calibration.expected_calibration_error?.toFixed(3) ?? "—"}</p>
                    <p className="text-[11px] text-muted">Expected Calibration Error</p>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-foreground">
                      {calibration.high_confidence_error_rate !== null ? `${(calibration.high_confidence_error_rate * 100).toFixed(0)}%` : "—"}
                    </p>
                    <p className="text-[11px] text-muted">High-confidence error rate</p>
                  </div>
                </div>
              )}
              {mode === "general" && (
                <p className="text-xs text-muted">
                  In plain terms: when CareerPilot says it&apos;s 80% confident, it should be right about 80% of the
                  time. The bars below compare stated confidence against actual accuracy for every case run so far.
                </p>
              )}
              <div className="space-y-1">
                <p className="text-xs font-medium text-foreground">Reliability bins</p>
                {calibration.bins.map((bin, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="w-20 text-muted">
                      {(bin.bin_start * 100).toFixed(0)}-{(bin.bin_end * 100).toFixed(0)}%
                    </span>
                    <div className="relative h-2 flex-1 rounded-full bg-surface-muted">
                      {bin.accuracy !== null && (
                        <div className="absolute h-2 rounded-full bg-brand" style={{ width: `${bin.accuracy * 100}%` }} />
                      )}
                    </div>
                    <span className="w-24 text-right text-muted">
                      {bin.count > 0 ? `${bin.count} case(s), ${((bin.accuracy ?? 0) * 100).toFixed(0)}% correct` : "no data"}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex-row items-center justify-between gap-2">
          <CardTitle as="h2">Run history</CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              const payload = { routingResult, graphVsVectorResult, ablationResult, calibration, runs };
              const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "careerpilot-research-results.json";
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Export raw results
          </Button>
        </CardHeader>
        <CardContent>
          {runsLoading ? (
            <Skeleton className="h-24" />
          ) : !runs || runs.length === 0 ? (
            <EmptyState title="No experiment runs yet" />
          ) : (
            <ul className="space-y-2">
              {runs.map((run) => (
                <li key={run.id} className="flex items-center justify-between rounded-[var(--radius-md)] border border-border p-2 text-xs">
                  <div>
                    <p className="font-medium text-foreground">{run.name}</p>
                    <p className="text-muted">{run.notes}</p>
                  </div>
                  <div className="text-right text-muted">
                    <Badge variant="muted">{run.result_count} results</Badge>
                    <p className="mt-1">{formatDateTime(run.created_at)}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function ResearchLabPage() {
  return (
    <Protected>
      <ResearchLabBody />
    </Protected>
  );
}
