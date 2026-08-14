"use client";

import { useState } from "react";
import {
  AlertCircle,
  ChevronDown,
  Compass,
  Cpu,
  FlaskConical,
  Gauge,
  Plus,
  Sparkles,
  Target,
  Trash2,
  Trophy,
} from "lucide-react";
import { toast } from "sonner";
import { InverseModePanel } from "@/components/experiment/inverse-mode-panel";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useActivityTypes,
  useCompareScenarios,
  useExperimentScenarios,
  usePredictionAccuracy,
  useRunScenario,
} from "@/hooks/use-experiment";
import { useDashboard } from "@/hooks/use-dashboard";
import { useSkillsCatalog } from "@/hooks/use-onboarding";
import { ApiError } from "@/lib/api-client";
import { cn, formatPercent } from "@/lib/utils";
import type { AllocationRequest, ExperimentScenarioOut } from "@/types/api";

const DISCLAIMER = "Personalized scenario estimate—not a guaranteed outcome or hiring prediction.";

function AllocationRow({
  allocation,
  activityTypes,
  skillNames,
  onChange,
  onRemove,
  canRemove,
  index,
}: {
  allocation: AllocationRequest;
  activityTypes: string[];
  skillNames: string[];
  onChange: (next: AllocationRequest) => void;
  onRemove: () => void;
  canRemove: boolean;
  index: number;
}) {
  return (
    <div className={cn("animate-fade-up flex flex-wrap items-center gap-3 rounded-[var(--radius-md)] border border-border bg-surface-muted/40 p-3", `delay-${Math.min(index + 1, 8)}`)}>
      <input
        list="skill-options"
        value={allocation.skill_name}
        onChange={(e) => onChange({ ...allocation, skill_name: e.target.value })}
        placeholder="Skill (e.g. SQL)"
        aria-label="Skill"
        className="h-9 w-40 rounded-[var(--radius-md)] border border-border bg-surface px-2 text-sm text-foreground"
      />
      <datalist id="skill-options">
        {skillNames.map((name) => (
          <option key={name} value={name} />
        ))}
      </datalist>
      <select
        value={allocation.activity_type}
        onChange={(e) => onChange({ ...allocation, activity_type: e.target.value })}
        aria-label="Activity type"
        className="h-9 rounded-[var(--radius-md)] border border-border bg-surface px-2 text-sm text-foreground"
      >
        {activityTypes.map((type) => (
          <option key={type} value={type}>
            {type.replaceAll("_", " ")}
          </option>
        ))}
      </select>
      <div className="flex flex-1 min-w-40 items-center gap-2">
        <input
          type="range"
          min={1}
          max={200}
          value={allocation.hours}
          onChange={(e) => onChange({ ...allocation, hours: Number(e.target.value) })}
          aria-label="Hours (slider)"
          className="h-1.5 flex-1 accent-brand"
        />
        <Input
          type="number"
          min={1}
          max={200}
          value={allocation.hours}
          onChange={(e) => onChange({ ...allocation, hours: Number(e.target.value) })}
          aria-label="Hours"
          className="h-9 w-20 shrink-0"
        />
        <span className="shrink-0 text-xs text-muted">hrs</span>
      </div>
      <Button type="button" variant="ghost" size="icon" onClick={onRemove} disabled={!canRemove} aria-label="Remove allocation">
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}

function Drawer({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-[var(--radius-md)] border border-border bg-surface-muted">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-2 p-3 text-left text-xs font-medium text-foreground"
        aria-expanded={open}
      >
        <span>{title}</span>
        <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", open && "rotate-180")} aria-hidden="true" />
      </button>
      {open && <div className="animate-fade-in border-t border-border p-3 text-xs text-muted">{children}</div>}
    </div>
  );
}

function ScenarioResultCard({
  scenario,
  titleAs = "h3",
  rank,
}: {
  scenario: ExperimentScenarioOut;
  titleAs?: "h2" | "h3";
  rank?: number;
}) {
  const result = scenario.result;
  if (!result) return null;
  const confidenceLow = Math.max(0, result.overall_confidence - result.overall_uncertainty);
  const confidenceHigh = Math.min(1, result.overall_confidence + result.overall_uncertainty);

  return (
    <Card variant={rank === 1 ? "glow-brand" : "default"} className="relative animate-scale-in overflow-hidden">
      {rank === 1 && <div className="absolute inset-0 bg-gradient-radial-brand opacity-20" aria-hidden="true" />}
      <CardHeader className="relative flex-row items-center justify-between gap-2">
        <CardTitle as={titleAs}>{scenario.name}</CardTitle>
        <div className="flex items-center gap-2">
          {rank === 1 && (
            <Badge className="gap-1">
              <Trophy className="h-3 w-3" aria-hidden="true" /> Top recommendation
            </Badge>
          )}
          <Badge variant="outline" className="gap-1">
            <Cpu className="h-3 w-3" aria-hidden="true" /> {result.engine_version}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="relative space-y-5">
        <div className="grid grid-cols-2 gap-4 text-center sm:grid-cols-3">
          <div>
            <p className="text-xs text-muted">Current overall</p>
            <p className="text-metric text-foreground">
              {result.current_overall_score !== null ? formatPercent(result.current_overall_score) : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted">Simulated overall</p>
            <p className="text-metric text-gradient-brand">
              {result.simulated_overall_score !== null ? formatPercent(result.simulated_overall_score) : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted">Confidence range</p>
            <p className="text-metric text-foreground">
              {formatPercent(confidenceLow)}–{formatPercent(confidenceHigh)}
            </p>
          </div>
        </div>

        <div className="space-y-3">
          {result.component_changes.map((change, i) => (
            <div key={change.component_type} className={cn("animate-fade-up", `delay-${Math.min(i + 1, 8)}`)}>
              <div className="mb-1 flex items-center justify-between text-xs text-muted">
                <span className="capitalize">{change.component_type.replaceAll("_", " ")}</span>
                <span>
                  {change.current_score !== null ? formatPercent(change.current_score) : "no evidence yet"} →{" "}
                  <span className="font-medium text-foreground">{formatPercent(change.simulated_score)}</span>{" "}
                  <Badge variant={change.delta >= 0 ? "positive" : "warning"} className="ml-1">
                    {change.delta >= 0 ? "+" : ""}
                    {(change.delta * 100).toFixed(0)} pts
                  </Badge>
                </span>
              </div>
              <div className="relative h-2.5 w-full rounded-full bg-surface-muted">
                <div
                  className="absolute h-2.5 rounded-full bg-border-strong"
                  style={{ width: `${(change.current_score ?? 0.5) * 100}%`, transition: "width 900ms cubic-bezier(0.16,1,0.3,1)" }}
                />
                <div
                  className="absolute h-2.5 rounded-full bg-gradient-brand shadow-[0_0_10px_-2px_var(--brand)]"
                  style={{ width: `${change.simulated_score * 100}%`, transition: "width 1100ms cubic-bezier(0.16,1,0.3,1) 120ms" }}
                />
              </div>
              <p className="mt-0.5 text-[11px] text-muted">Confidence {formatPercent(change.confidence)} · uncertainty ±{formatPercent(change.uncertainty)}</p>
            </div>
          ))}
        </div>

        <p className="flex items-start gap-2 rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 text-xs text-muted">
          <Gauge className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" aria-hidden="true" />
          {result.explanation}
        </p>

        {result.waste_notes.length > 0 && (
          <div className="space-y-1.5">
            {result.waste_notes.map((note, i) => (
              <p key={i} className="flex items-start gap-2 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2.5 text-xs text-warning">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" /> {note}
              </p>
            ))}
          </div>
        )}

        {result.sensitivity.length > 0 && (
          <div className="rounded-[var(--radius-md)] border border-border p-3">
            <p className="mb-1.5 text-xs font-semibold text-foreground">This estimate is most fragile to:</p>
            <p className="text-xs text-muted">
              <span className="font-medium text-foreground">{result.sensitivity[0].label}</span> -- a ±20% change
              there swings the overall estimate by up to {(result.sensitivity[0].swing * 100).toFixed(1)} points.
            </p>
          </div>
        )}

        <div className="grid gap-2 sm:grid-cols-2">
          <Drawer title={`Assumptions (${result.assumptions.length})`}>
            <ul className="list-inside list-disc space-y-0.5">
              {result.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </Drawer>
          <Drawer title={`Evidence basis (${result.evidence_used.length})`}>
            {result.evidence_used.length === 0 ? (
              <p>No historical evidence items were used — this is a cold-start estimate.</p>
            ) : (
              <ul className="list-inside list-disc space-y-0.5 font-mono">
                {result.evidence_used.map((id, i) => (
                  <li key={i} className="truncate">{id}</li>
                ))}
              </ul>
            )}
          </Drawer>
        </div>

        <div className="rounded-[var(--radius-md)] border border-brand/30 bg-brand-soft p-2.5 text-center text-xs font-medium text-brand">
          {result.disclaimer}
        </div>
      </CardContent>
    </Card>
  );
}

function PredictionAccuracyBadge({ scenarioId }: { scenarioId: string }) {
  const { data: accuracy } = usePredictionAccuracy(scenarioId);
  if (!accuracy || accuracy.status !== "measured") return null;
  const isClose = accuracy.absolute_error !== null && accuracy.absolute_error <= 0.05;
  return (
    <Badge variant={isClose ? "positive" : "muted"} className="gap-1">
      <Target className="h-3 w-3" aria-hidden="true" />
      Predicted {((accuracy.predicted_delta ?? 0) * 100).toFixed(0)}pts · actual {((accuracy.actual_delta ?? 0) * 100).toFixed(0)}pts
    </Badge>
  );
}

function ExperimentLabBody() {
  const { data: activityTypes } = useActivityTypes();
  const { data: skills } = useSkillsCatalog();
  const { data: dashboard } = useDashboard();
  const { data: scenarios, isLoading: scenariosLoading } = useExperimentScenarios();
  const runScenario = useRunScenario();

  const [labMode, setLabMode] = useState<"forward" | "target">("forward");
  const [name, setName] = useState("My scenario");
  const [allocations, setAllocations] = useState<AllocationRequest[]>([
    { skill_name: "SQL", activity_type: "practice_problems", hours: 20 },
  ]);
  const [latestResult, setLatestResult] = useState<ExperimentScenarioOut | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);

  const { data: compared } = useCompareScenarios(compareIds);
  const rankedCompared = compared
    ? [...compared].sort((a, b) => (b.result?.overall_score_delta ?? -Infinity) - (a.result?.overall_score_delta ?? -Infinity))
    : null;

  const addAllocation = () => {
    setAllocations((prev) => [...prev, { skill_name: "", activity_type: "practice_problems", hours: 10 }]);
  };

  const handleRun = () => {
    if (allocations.some((a) => !a.skill_name.trim())) {
      toast.error("Give every allocation a skill name.");
      return;
    }
    runScenario.mutate(
      { name, allocations, target_role_id: dashboard?.target_role?.id ?? null },
      {
        onSuccess: (data) => {
          setLatestResult(data);
          toast.success("Scenario simulated.");
        },
        onError: (err) => {
          toast.error(err instanceof ApiError ? err.message : "Couldn't run this scenario.");
        },
      }
    );
  };

  const toggleCompare = (id: string) => {
    setCompareIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
            <FlaskConical className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Career Experiment Lab</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Compare possible learning investments before you make them. Every result is a deterministic, versioned
          estimate — never a guarantee.
        </p>
        <div className="relative mt-5 flex w-fit rounded-[var(--radius-md)] border border-border bg-surface p-1">
          <button
            type="button"
            onClick={() => setLabMode("forward")}
            className={cn(
              "flex items-center gap-1.5 rounded-[var(--radius-sm)] px-3 py-1.5 text-xs font-medium transition-colors",
              labMode === "forward" ? "bg-gradient-brand text-brand-foreground" : "text-muted hover:text-foreground",
            )}
            aria-pressed={labMode === "forward"}
          >
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" /> Forward: "what if I spend N hours?"
          </button>
          <button
            type="button"
            onClick={() => setLabMode("target")}
            className={cn(
              "flex items-center gap-1.5 rounded-[var(--radius-sm)] px-3 py-1.5 text-xs font-medium transition-colors",
              labMode === "target" ? "bg-gradient-brand text-brand-foreground" : "text-muted hover:text-foreground",
            )}
            aria-pressed={labMode === "target"}
          >
            <Compass className="h-3.5 w-3.5" aria-hidden="true" /> Target: "what's the cheapest path?"
          </button>
        </div>
      </div>

      {labMode === "target" && <InverseModePanel skillNames={(skills ?? []).map((s) => s.name)} />}

      {labMode === "forward" && (
        <>
      <Card className="animate-fade-up delay-1">
        <CardHeader>
          <CardTitle as="h2" className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-brand" aria-hidden="true" /> Build a scenario
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input value={name} onChange={(e) => setName(e.target.value)} aria-label="Scenario name" placeholder="Scenario name" />
          <div className="space-y-2">
            {allocations.map((allocation, i) => (
              <AllocationRow
                key={i}
                index={i}
                allocation={allocation}
                activityTypes={activityTypes ?? ["practice_problems", "mock_interview", "reading", "project", "mixed"]}
                skillNames={(skills ?? []).map((s) => s.name)}
                onChange={(next) => setAllocations((prev) => prev.map((a, idx) => (idx === i ? next : a)))}
                onRemove={() => setAllocations((prev) => prev.filter((_, idx) => idx !== i))}
                canRemove={allocations.length > 1}
              />
            ))}
          </div>
          <div className="flex items-center gap-2">
            <Button type="button" variant="outline" size="sm" onClick={addAllocation}>
              <Plus className="h-3.5 w-3.5" aria-hidden="true" /> Add allocation
            </Button>
            <Button onClick={handleRun} disabled={runScenario.isPending} size="lg">
              {runScenario.isPending ? "Simulating…" : "Run scenario"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {latestResult && <ScenarioResultCard scenario={latestResult} titleAs="h2" />}
      </>
      )}

      <Card className="animate-fade-up delay-2">
        <CardHeader>
          <CardTitle as="h2">Past scenarios</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {scenariosLoading ? (
            <Skeleton className="h-24" />
          ) : !scenarios || scenarios.length === 0 ? (
            <EmptyState icon={FlaskConical} title="No scenarios yet" description="Run a scenario above to see it here." />
          ) : (
            <>
              <ul className="space-y-2">
                {scenarios.map((s) => (
                  <li key={s.id} className="flex items-center justify-between rounded-[var(--radius-md)] border border-border p-2 text-sm">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={compareIds.includes(s.id)}
                        onChange={() => toggleCompare(s.id)}
                        aria-label={`Select ${s.name} for comparison`}
                      />
                      <span className="text-foreground">{s.name}</span>
                      {s.result?.overall_score_delta !== null && s.result?.overall_score_delta !== undefined && (
                        <Badge variant={s.result.overall_score_delta >= 0 ? "positive" : "warning"}>
                          {s.result.overall_score_delta >= 0 ? "+" : ""}
                          {(s.result.overall_score_delta * 100).toFixed(0)} pts
                        </Badge>
                      )}
                      <PredictionAccuracyBadge scenarioId={s.id} />
                    </label>
                  </li>
                ))}
              </ul>
              {compareIds.length > 1 && (
                <p className="text-xs text-muted">Comparing {compareIds.length} scenarios below, ranked by projected gain.</p>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {rankedCompared && rankedCompared.length > 1 && (
        <div className="space-y-4">
          <h2 className="text-h2 text-foreground">Scenario comparison</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {rankedCompared.map((s, i) => (
              <ScenarioResultCard key={s.id} scenario={s} rank={i + 1} />
            ))}
          </div>
        </div>
      )}

      <p className="text-center text-xs text-muted">{DISCLAIMER}</p>
    </div>
  );
}

export default function ExperimentLabPage() {
  return (
    <Protected>
      <ExperimentLabBody />
    </Protected>
  );
}
