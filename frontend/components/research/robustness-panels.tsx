"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, CheckCircle2, Gauge, ShieldAlert, Sparkles, Timer, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  useRunAdversarialSuite,
  useRunDriftCanary,
  useRunEfficiencyFrontier,
  useRunFairnessProbe,
  useRunFallbackFidelity,
  useRunThresholdTuning,
} from "@/hooks/use-research-lab";
import { formatPercent } from "@/lib/utils";
import type {
  AdversarialSuiteOut,
  DriftCanaryOut,
  EfficiencyFrontierOut,
  FairnessProbeOut,
  FallbackFidelityOut,
  ThresholdTuningOut,
} from "@/types/api";

const CONDITION_LABELS: Record<string, string> = {
  single_agent_fixed: "Single agent",
  multi_agent_fixed: "Multi-agent council",
  care_adaptive: "CARE adaptive",
};

export function EfficiencyFrontierCard({ result }: { result: EfficiencyFrontierOut }) {
  const data = result.frontier.map((f) => ({
    label: CONDITION_LABELS[f.condition] ?? f.condition,
    accuracy: Math.round(f.accuracy * 100),
    latency: Math.round(f.mean_latency_ms),
    calls: f.mean_llm_calls,
  }));
  return (
    <Card variant="glow-brand" className="animate-scale-in">
      <CardHeader>
        <CardTitle as="h2">CARE efficiency frontier</CardTitle>
        <CardDescription>Real latency and LLM-call cost vs accuracy -- does CARE sit on the frontier?</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="h-56 w-full" role="img" aria-label="Bar chart of accuracy, latency, and LLM calls per routing condition">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="label" tick={{ fill: "var(--color-muted)", fontSize: 11 }} />
              <YAxis tick={{ fill: "var(--color-muted)", fontSize: 11 }} />
              <Tooltip contentStyle={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="accuracy" name="Accuracy %" fill="var(--color-brand)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          {result.frontier.map((f) => (
            <div key={f.condition} className="rounded-[var(--radius-md)] border border-border p-2.5 text-center">
              <p className="text-xs font-medium text-foreground">{CONDITION_LABELS[f.condition] ?? f.condition}</p>
              <p className="mt-1 text-lg font-bold text-foreground">{formatPercent(f.accuracy)}</p>
              <p className="text-[11px] text-muted">
                {f.mean_latency_ms.toFixed(1)}ms · {f.mean_llm_calls} call{f.mean_llm_calls === 1 ? "" : "s"}
              </p>
            </div>
          ))}
        </div>
        <p className="flex items-start gap-2 rounded-[var(--radius-md)] border border-border bg-surface-muted p-2.5 text-xs text-muted">
          <Timer className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" aria-hidden="true" /> {result.cost_note}
        </p>
      </CardContent>
    </Card>
  );
}

export function ThresholdTuningCard({ result }: { result: ThresholdTuningOut }) {
  return (
    <Card variant="glow-brand" className="animate-scale-in">
      <CardHeader>
        <CardTitle as="h2">Empirical threshold tuning</CardTitle>
        <CardDescription>Sweeping the documented 0.80 / 0.55 / 0.50 routing thresholds against the rubric.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-2 sm:grid-cols-2">
          <div className="rounded-[var(--radius-md)] border border-border p-3">
            <p className="text-xs font-medium text-muted">Current documented defaults</p>
            <p className="mt-1 text-sm text-foreground">
              {result.current_defaults.single_agent_threshold} / {result.current_defaults.multi_agent_threshold} / {result.current_defaults.human_review_threshold}
            </p>
            <p className="text-xs text-muted">Agreement: {formatPercent(result.current_defaults.agreement_rate)}</p>
          </div>
          <div className="rounded-[var(--radius-md)] border border-border p-3">
            <p className="text-xs font-medium text-muted">Empirical optimum ({result.combinations_swept} swept)</p>
            {result.empirical_best && (
              <>
                <p className="mt-1 text-sm text-foreground">
                  {result.empirical_best.single_agent_threshold} / {result.empirical_best.multi_agent_threshold} / {result.empirical_best.human_review_threshold}
                </p>
                <p className="text-xs text-muted">Agreement: {formatPercent(result.empirical_best.agreement_rate)}</p>
              </>
            )}
          </div>
        </div>
        <Badge variant={result.current_defaults_tied_for_best ? "positive" : "warning"} className="gap-1">
          {result.current_defaults_tied_for_best ? <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> : <AlertTriangle className="h-3 w-3" aria-hidden="true" />}
          {result.current_defaults_tied_for_best
            ? "Documented defaults tie for the empirical optimum"
            : "A different combination outperforms the documented defaults"}
        </Badge>
        <p className="text-xs text-muted">{result.methodology_note}</p>
      </CardContent>
    </Card>
  );
}

export function AdversarialSuiteCard({ result }: { result: AdversarialSuiteOut }) {
  return (
    <Card variant="glow-brand" className="animate-scale-in">
      <CardHeader className="flex-row items-center justify-between gap-2">
        <div>
          <CardTitle as="h2">Adversarial robustness suite</CardTitle>
          <CardDescription>Hostile inputs run through real agents -- pass means confidence stays low, nothing escalates wrongly.</CardDescription>
        </div>
        <Badge variant={result.all_passed ? "positive" : "warning"}>
          {result.passed_count}/{result.case_count} passed
        </Badge>
      </CardHeader>
      <CardContent className="space-y-2">
        {result.cases.map((c) => (
          <div key={c.case_id} className="rounded-[var(--radius-md)] border border-border p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-medium text-foreground">{c.case_id.replaceAll("-", " ")}</p>
              {c.passed ? (
                <Badge variant="positive" className="gap-1">
                  <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> Pass
                </Badge>
              ) : (
                <Badge variant="warning" className="gap-1">
                  <XCircle className="h-3 w-3" aria-hidden="true" /> Fail
                </Badge>
              )}
            </div>
            <p className="mt-1 text-xs text-muted">&ldquo;{c.input_summary}&rdquo;</p>
            <p className="mt-1 text-xs text-muted">{c.note}</p>
          </div>
        ))}
        <p className="text-xs text-muted">{result.methodology_note}</p>
      </CardContent>
    </Card>
  );
}

export function FallbackFidelityCard({ result }: { result: FallbackFidelityOut }) {
  return (
    <Card variant="glow-brand" className="animate-scale-in">
      <CardHeader>
        <CardTitle as="h2">Fallback fidelity</CardTitle>
        <CardDescription>How closely the deterministic fallback tracks a live model on the same input.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {result.measurable ? (
          <>
            <p className="text-sm text-foreground">Strength-set overlap: {result.strength_set_overlap !== null && result.strength_set_overlap !== undefined ? formatPercent(result.strength_set_overlap) : "—"}</p>
          </>
        ) : (
          <p className="flex items-start gap-2 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2.5 text-xs text-warning">
            <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" /> {result.message}
          </p>
        )}
        <p className="text-xs text-muted">{result.methodology_note}</p>
      </CardContent>
    </Card>
  );
}

export function FairnessProbeCard({ result }: { result: FairnessProbeOut }) {
  return (
    <Card variant="glow-brand" className="animate-scale-in">
      <CardHeader>
        <CardTitle as="h2">Fairness probe</CardTitle>
        <CardDescription>Score deltas for semantically-equivalent answers that differ only in phrasing style.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {result.rows.map((row) => (
          <div key={row.pair_id} className="rounded-[var(--radius-md)] border border-border p-3 text-sm">
            <p className="font-medium text-foreground">{row.pair_id.replaceAll("-", " ")}</p>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted">
              <span>{row.variant_a_label}: {formatPercent(row.variant_a_correctness)}</span>
              <span>{row.variant_b_label}: {formatPercent(row.variant_b_correctness)}</span>
              <Badge variant={Math.abs(row.correctness_delta) > 0.15 ? "warning" : "muted"}>
                Δ {(row.correctness_delta * 100).toFixed(0)}pp
              </Badge>
            </div>
          </div>
        ))}
        <p className="rounded-[var(--radius-md)] border border-border bg-surface-muted p-2.5 text-xs text-muted">{result.disclaimer}</p>
      </CardContent>
    </Card>
  );
}

export function DriftCanaryCard({ result }: { result: DriftCanaryOut }) {
  return (
    <Card variant="glow-brand" className="animate-scale-in">
      <CardHeader className="flex-row items-center justify-between gap-2">
        <div>
          <CardTitle as="h2">Scoring-drift canary</CardTitle>
          <CardDescription>Frozen baseline from {result.baseline_frozen_at}, re-run against the live agent now.</CardDescription>
        </div>
        <Badge variant={result.any_drifted ? "warning" : "positive"} className="gap-1">
          {result.any_drifted ? <AlertTriangle className="h-3 w-3" aria-hidden="true" /> : <CheckCircle2 className="h-3 w-3" aria-hidden="true" />}
          {result.any_drifted ? "Drift detected" : "No drift"}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-2">
        {result.cases.map((c) => (
          <div key={c.case_id} className="flex items-center justify-between rounded-[var(--radius-md)] border border-border p-2.5 text-xs">
            <span className="text-foreground">{c.case_id.replaceAll("-", " ")}</span>
            <span className={c.drifted ? "text-warning" : "text-muted"}>
              confidence {c.confidence_drift >= 0 ? "+" : ""}{c.confidence_drift.toFixed(3)}
            </span>
          </div>
        ))}
        <p className="text-xs text-muted">{result.methodology_note}</p>
      </CardContent>
    </Card>
  );
}

export function useRobustnessPanels() {
  const efficiency = useRunEfficiencyFrontier();
  const thresholds = useRunThresholdTuning();
  const adversarial = useRunAdversarialSuite();
  const fidelity = useRunFallbackFidelity();
  const fairness = useRunFairnessProbe();
  const drift = useRunDriftCanary();

  return {
    efficiency,
    thresholds,
    adversarial,
    fidelity,
    fairness,
    drift,
    buttons: (
      <div className="flex flex-wrap gap-2">
        <Button variant="outline" onClick={() => efficiency.mutate()} disabled={efficiency.isPending}>
          <Gauge className="h-3.5 w-3.5" aria-hidden="true" /> {efficiency.isPending ? "Running..." : "Efficiency frontier"}
        </Button>
        <Button variant="outline" onClick={() => thresholds.mutate()} disabled={thresholds.isPending}>
          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" /> {thresholds.isPending ? "Running..." : "Threshold tuning"}
        </Button>
        <Button variant="outline" onClick={() => adversarial.mutate()} disabled={adversarial.isPending}>
          <ShieldAlert className="h-3.5 w-3.5" aria-hidden="true" /> {adversarial.isPending ? "Running..." : "Adversarial suite"}
        </Button>
        <Button variant="outline" onClick={() => fidelity.mutate()} disabled={fidelity.isPending}>
          {fidelity.isPending ? "Running..." : "Fallback fidelity"}
        </Button>
        <Button variant="outline" onClick={() => fairness.mutate()} disabled={fairness.isPending}>
          {fairness.isPending ? "Running..." : "Fairness probe"}
        </Button>
        <Button variant="outline" onClick={() => drift.mutate()} disabled={drift.isPending}>
          {drift.isPending ? "Running..." : "Drift canary"}
        </Button>
      </div>
    ),
  };
}
