"use client";

import { useState } from "react";
import { FlaskConical, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useActivityTypes, useCompareScenarios, useExperimentScenarios, useRunScenario } from "@/hooks/use-experiment";
import { useDashboard } from "@/hooks/use-dashboard";
import { useSkillsCatalog } from "@/hooks/use-onboarding";
import { ApiError } from "@/lib/api-client";
import type { AllocationRequest, ExperimentScenarioOut } from "@/types/api";

const DISCLAIMER = "Personalized scenario estimate—not a guaranteed outcome or hiring prediction.";

function AllocationRow({
  allocation,
  activityTypes,
  skillNames,
  onChange,
  onRemove,
  canRemove,
}: {
  allocation: AllocationRequest;
  activityTypes: string[];
  skillNames: string[];
  onChange: (next: AllocationRequest) => void;
  onRemove: () => void;
  canRemove: boolean;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-[var(--radius-md)] border border-border p-3">
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
      <Input
        type="number"
        min={1}
        max={200}
        value={allocation.hours}
        onChange={(e) => onChange({ ...allocation, hours: Number(e.target.value) })}
        aria-label="Hours"
        className="h-9 w-24"
      />
      <span className="text-xs text-muted">hours</span>
      <Button type="button" variant="ghost" size="icon" onClick={onRemove} disabled={!canRemove} aria-label="Remove allocation">
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}

function ScenarioResultCard({ scenario }: { scenario: ExperimentScenarioOut }) {
  const result = scenario.result;
  if (!result) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{scenario.name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-center sm:grid-cols-3">
          <div>
            <p className="text-xs text-muted">Current overall</p>
            <p className="text-2xl font-semibold text-foreground">
              {result.current_overall_score !== null ? `${(result.current_overall_score * 100).toFixed(0)}%` : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted">Simulated overall</p>
            <p className="text-2xl font-semibold text-brand">
              {result.simulated_overall_score !== null ? `${(result.simulated_overall_score * 100).toFixed(0)}%` : "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted">Confidence</p>
            <p className="text-2xl font-semibold text-foreground">{(result.overall_confidence * 100).toFixed(0)}%</p>
          </div>
        </div>

        <div className="space-y-3">
          {result.component_changes.map((change) => (
            <div key={change.component_type}>
              <div className="mb-1 flex items-center justify-between text-xs text-muted">
                <span className="capitalize">{change.component_type.replaceAll("_", " ")}</span>
                <span>
                  {change.current_score !== null ? `${(change.current_score * 100).toFixed(0)}%` : "no evidence yet"} →{" "}
                  <span className="font-medium text-foreground">{(change.simulated_score * 100).toFixed(0)}%</span>{" "}
                  ({change.delta >= 0 ? "+" : ""}
                  {(change.delta * 100).toFixed(0)} pts, confidence {(change.confidence * 100).toFixed(0)}%)
                </span>
              </div>
              <div className="relative h-2 w-full rounded-full bg-surface-muted">
                <div
                  className="absolute h-2 rounded-full bg-border"
                  style={{ width: `${(change.current_score ?? 0.5) * 100}%` }}
                />
                <div
                  className="absolute h-2 rounded-full border-2 border-brand"
                  style={{ width: `${change.simulated_score * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <div>
          <p className="mb-1 text-xs font-medium text-foreground">Assumptions</p>
          <ul className="list-inside list-disc space-y-0.5 text-xs text-muted">
            {result.assumptions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-muted">{result.explanation}</p>
        <p className="text-xs text-muted">Based on {result.evidence_used.length} evidence item(s) from your Career Twin.</p>

        <div className="rounded-[var(--radius-md)] border border-brand/30 bg-brand-soft p-2 text-center text-xs font-medium text-brand">
          {result.disclaimer}
        </div>
      </CardContent>
    </Card>
  );
}

function ExperimentLabBody() {
  const { data: activityTypes } = useActivityTypes();
  const { data: skills } = useSkillsCatalog();
  const { data: dashboard } = useDashboard();
  const { data: scenarios, isLoading: scenariosLoading } = useExperimentScenarios();
  const runScenario = useRunScenario();

  const [name, setName] = useState("My scenario");
  const [allocations, setAllocations] = useState<AllocationRequest[]>([
    { skill_name: "SQL", activity_type: "practice_problems", hours: 20 },
  ]);
  const [latestResult, setLatestResult] = useState<ExperimentScenarioOut | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);

  const { data: compared } = useCompareScenarios(compareIds);

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
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
          <FlaskConical className="h-5 w-5 text-brand" aria-hidden="true" />
          Career Experiment Lab
        </h1>
        <p className="mt-1 text-sm text-muted">
          Compare possible learning investments before you make them. Every result is a deterministic, versioned
          estimate — never a guarantee.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Build a scenario</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input value={name} onChange={(e) => setName(e.target.value)} aria-label="Scenario name" placeholder="Scenario name" />
          <div className="space-y-2">
            {allocations.map((allocation, i) => (
              <AllocationRow
                key={i}
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
              <Plus className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" /> Add allocation
            </Button>
            <Button onClick={handleRun} disabled={runScenario.isPending}>
              {runScenario.isPending ? "Simulating..." : "Run scenario"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {latestResult && <ScenarioResultCard scenario={latestResult} />}

      <Card>
        <CardHeader>
          <CardTitle>Past scenarios</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {scenariosLoading ? (
            <Skeleton className="h-24" />
          ) : !scenarios || scenarios.length === 0 ? (
            <EmptyState title="No scenarios yet" description="Run a scenario above to see it here." />
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
                    </label>
                  </li>
                ))}
              </ul>
              {compareIds.length > 1 && (
                <p className="text-xs text-muted">Comparing {compareIds.length} scenarios below.</p>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {compared && compared.length > 1 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-foreground">Scenario comparison</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {compared.map((s) => (
              <ScenarioResultCard key={s.id} scenario={s} />
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
