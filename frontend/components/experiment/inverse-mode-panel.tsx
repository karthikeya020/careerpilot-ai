"use client";

import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, Calendar, CheckCircle2, Compass, TrendingDown } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { usePlanTarget } from "@/hooks/use-experiment";
import { ApiError } from "@/lib/api-client";
import { formatPercent } from "@/lib/utils";
import type { TargetPlanOut } from "@/types/api";

const COMPONENT_OPTIONS: { value: string; label: string }[] = [
  { value: "resume_readiness", label: "Resume" },
  { value: "technical_readiness", label: "Technical" },
  { value: "communication_readiness", label: "Communication" },
  { value: "assessment_readiness", label: "Assessment" },
  { value: "portfolio_readiness", label: "Portfolio" },
  { value: "role_alignment_readiness", label: "Role Alignment" },
];

function GainCurveChart({ curve }: { curve: TargetPlanOut["marginal_gain_curve"] }) {
  return (
    <div className="h-40 w-full" role="img" aria-label="Chart showing diminishing marginal readiness gain per additional hour">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={curve} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="gainCurveFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-accent-2)" stopOpacity={0.4} />
              <stop offset="100%" stopColor="var(--color-accent-2)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="var(--color-border)" strokeDasharray="3 3" />
          <XAxis dataKey="hours" tickFormatter={(v) => `${v}h`} tick={{ fill: "var(--color-muted)", fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "var(--color-muted)", fontSize: 10 }} axisLine={false} tickLine={false} width={36} />
          <Tooltip
            formatter={(value) => [typeof value === "number" ? value.toFixed(4) : String(value ?? ""), "Marginal gain"]}
            labelFormatter={(hours) => `Hour ${hours}`}
            contentStyle={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: 8, fontSize: 12 }}
          />
          <Area type="monotone" dataKey="marginal_gain" stroke="var(--color-accent-2)" strokeWidth={2} fill="url(#gainCurveFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function InverseModePanel({ skillNames }: { skillNames: string[] }) {
  const planTarget = usePlanTarget();
  const [targetComponent, setTargetComponent] = useState("technical_readiness");
  const [targetScore, setTargetScore] = useState(80);
  const [candidateSkills, setCandidateSkills] = useState("");
  const [weeklyHours, setWeeklyHours] = useState(10);
  const [deadline, setDeadline] = useState("");
  const [plan, setPlan] = useState<TargetPlanOut | null>(null);

  const handleSolve = () => {
    const skills = candidateSkills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (skills.length === 0) {
      toast.error("List at least one candidate skill, comma-separated.");
      return;
    }
    planTarget.mutate(
      {
        target_component: targetComponent,
        target_score: targetScore / 100,
        candidate_skills: skills,
        weekly_hours: weeklyHours,
        deadline: deadline || null,
      },
      {
        onSuccess: (data) => setPlan(data),
        onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't solve for this target."),
      }
    );
  };

  return (
    <div className="space-y-4">
      <Card className="animate-fade-up">
        <CardHeader>
          <CardTitle as="h2" className="flex items-center gap-2">
            <Compass className="h-4 w-4 text-brand" aria-hidden="true" /> Solve backwards from a target
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-xs font-medium text-muted">
              Target component
              <select
                value={targetComponent}
                onChange={(e) => setTargetComponent(e.target.value)}
                className="mt-1 h-9 w-full rounded-[var(--radius-md)] border border-border bg-surface px-2 text-sm text-foreground"
              >
                {COMPONENT_OPTIONS.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs font-medium text-muted">
              Target score: {targetScore}%
              <input
                type="range"
                min={10}
                max={99}
                value={targetScore}
                onChange={(e) => setTargetScore(Number(e.target.value))}
                className="mt-2.5 h-1.5 w-full accent-brand"
                aria-label="Target score percent"
              />
            </label>
          </div>
          <label className="block text-xs font-medium text-muted">
            Candidate skills (comma-separated)
            <input
              list="inverse-skill-options"
              value={candidateSkills}
              onChange={(e) => setCandidateSkills(e.target.value)}
              placeholder="e.g. Python, SQL, Data Structures"
              className="mt-1 h-9 w-full rounded-[var(--radius-md)] border border-border bg-surface px-2 text-sm text-foreground"
            />
            <datalist id="inverse-skill-options">
              {skillNames.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
          </label>
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="text-xs font-medium text-muted">
              Weekly hours budget
              <Input
                type="number"
                min={1}
                max={80}
                value={weeklyHours}
                onChange={(e) => setWeeklyHours(Number(e.target.value))}
                className="mt-1 h-9"
              />
            </label>
            <label className="text-xs font-medium text-muted">
              Deadline (optional)
              <Input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} className="mt-1 h-9" />
            </label>
          </div>
          <Button onClick={handleSolve} disabled={planTarget.isPending} size="lg">
            {planTarget.isPending ? "Solving…" : "Find the cheapest path"}
          </Button>
        </CardContent>
      </Card>

      {plan && (
        <Card variant="glow-brand" className="animate-scale-in">
          <CardHeader className="flex-row items-center justify-between gap-2">
            <CardTitle as="h2">
              {COMPONENT_OPTIONS.find((c) => c.value === plan.target_component)?.label ?? plan.target_component} to{" "}
              {formatPercent(plan.target_score)}
            </CardTitle>
            {plan.reached_target ? (
              <Badge variant="positive" className="gap-1">
                <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> Reachable
              </Badge>
            ) : (
              <Badge variant="warning" className="gap-1">
                <AlertTriangle className="h-3 w-3" aria-hidden="true" /> Not reached in search cap
              </Badge>
            )}
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <p className="text-xs text-muted">Baseline</p>
                <p className="text-metric text-foreground">{plan.baseline_score !== null ? formatPercent(plan.baseline_score) : "—"}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Total hours</p>
                <p className="text-metric text-gradient-brand">{plan.total_hours}h</p>
              </div>
              <div>
                <p className="text-xs text-muted">Weeks needed</p>
                <p className="text-metric text-foreground">{plan.weeks_to_complete ?? "—"}</p>
              </div>
            </div>

            <div>
              <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
                <Compass className="h-3.5 w-3.5" aria-hidden="true" /> Ordered plan (graph-aware scheduling)
              </p>
              <div className="space-y-2">
                {plan.plan.map((item) => (
                  <div key={item.skill_name} className="rounded-[var(--radius-md)] border border-border p-2.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium text-foreground">
                        {item.order_rank}. {item.skill_name}
                      </span>
                      <span className="text-muted">{item.hours}h · {item.activity_type.replaceAll("_", " ")}</span>
                    </div>
                    {item.scheduling_reason && (
                      <p className="mt-1 text-xs text-brand">{item.scheduling_reason}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {plan.calendar.weeks.length > 0 && (
              <div>
                <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
                  <Calendar className="h-3.5 w-3.5" aria-hidden="true" /> Weekly calendar
                </p>
                {plan.calendar.feasibility_note && (
                  <p className="mb-2 flex items-start gap-1.5 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-2 text-xs text-warning">
                    <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" /> {plan.calendar.feasibility_note}
                  </p>
                )}
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {plan.calendar.weeks.map((week) => (
                    <div key={week.week_number} className="w-40 shrink-0 rounded-[var(--radius-md)] border border-border p-2.5">
                      <p className="text-xs font-semibold text-foreground">Week {week.week_number}</p>
                      <p className="text-[11px] text-muted">{week.start_date}</p>
                      <div className="mt-1.5 space-y-1">
                        {week.items.map((item, i) => (
                          <p key={i} className="text-[11px] text-muted">
                            {item.skill_name}: <span className="text-foreground">{item.hours}h</span>
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
                <TrendingDown className="h-3.5 w-3.5" aria-hidden="true" /> Diminishing returns per hour
              </p>
              <GainCurveChart curve={plan.marginal_gain_curve} />
            </div>

            <div className="space-y-1">
              {plan.assumptions.map((a, i) => (
                <p key={i} className="text-xs text-muted">
                  {a}
                </p>
              ))}
            </div>
            <div className="rounded-[var(--radius-md)] border border-brand/30 bg-brand-soft p-2.5 text-center text-xs font-medium text-brand">
              {plan.disclaimer}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
