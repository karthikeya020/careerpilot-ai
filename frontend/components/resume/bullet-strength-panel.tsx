"use client";

import { AlertTriangle, CheckCircle2, MinusCircle, PenLine } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { cn } from "@/lib/utils";
import type { BulletGradeOut, BulletStrength } from "@/types/api";

const STRENGTH_STYLE: Record<BulletStrength, { label: string; badge: "positive" | "warning" | "danger"; icon: typeof CheckCircle2 }> = {
  strong: { label: "Strong evidence", badge: "positive", icon: CheckCircle2 },
  moderate: { label: "Could be stronger", badge: "warning", icon: MinusCircle },
  weak: { label: "Reads as a vague claim", badge: "danger", icon: AlertTriangle },
};

export function BulletStrengthPanel({ grades }: { grades: BulletGradeOut[] }) {
  const strong = grades.filter((g) => g.strength === "strong").length;

  return (
    <Card className="animate-fade-up">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <PenLine className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">Bullet-level evidence strength</CardTitle>
          <CardDescription>
            {grades.length > 0
              ? `${strong} of ${grades.length} bullets read as strong, measurable evidence -- not just a claim.`
              : "Add bullets to your Experience or Projects sections to get graded."}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {grades.length === 0 ? (
          <EmptyState
            icon={PenLine}
            title="No bullets detected yet"
            description="Add bullet points to your Experience or Projects sections so each line can be graded for real evidence strength."
          />
        ) : (
          <div className="space-y-2.5">
            {grades.map((g, i) => {
              const style = STRENGTH_STYLE[g.strength];
              const Icon = style.icon;
              return (
                <div key={i} className="rounded-[var(--radius-md)] border border-border p-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm text-foreground">{g.text}</p>
                    <Badge variant={style.badge} className="shrink-0 gap-1">
                      <Icon className="h-3 w-3" aria-hidden="true" /> {style.label}
                    </Badge>
                  </div>
                  {g.fix_suggestion && (
                    <p className={cn("mt-2 text-xs", g.strength === "weak" ? "text-danger" : "text-warning")}>
                      Fix: {g.fix_suggestion}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
