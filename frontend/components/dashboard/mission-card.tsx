"use client";

import Link from "next/link";
import { CheckCircle2, Compass, Rocket } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { useCompleteMission } from "@/hooks/use-missions";
import { ApiError } from "@/lib/api-client";
import { titleCase } from "@/lib/utils";
import type { LearningMissionOut } from "@/types/api";

export function MissionCard({ mission }: { mission: LearningMissionOut | null }) {
  const completeMission = useCompleteMission();

  if (!mission) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Today&apos;s mission</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Compass}
            title="No mission yet"
            description="Complete onboarding to get your first evidence-backed mission."
          />
        </CardContent>
      </Card>
    );
  }

  const isCompleted = mission.status === "completed";

  const handleComplete = async () => {
    try {
      await completeMission.mutateAsync(mission.id);
      toast.success("Mission marked complete.");
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "Couldn't update the mission.");
    }
  };

  return (
    <Card variant="glow-brand" className="relative overflow-hidden">
      <div className="absolute -right-8 -top-8 h-28 w-28 rounded-full bg-gradient-radial-brand blur-2xl" aria-hidden="true" />
      <CardHeader className="relative flex-row items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
            <Rocket className="h-4 w-4 text-brand-foreground" aria-hidden="true" />
          </span>
          <CardTitle>Today&apos;s mission</CardTitle>
        </div>
        <Badge variant="muted">{titleCase(mission.source_component.replace("_readiness", ""))}</Badge>
      </CardHeader>
      <CardContent className="relative space-y-3">
        <p className="text-base font-semibold text-foreground">{mission.title}</p>
        <p className="text-sm leading-relaxed text-muted">{mission.description}</p>
        {mission.target_skill ? <Badge>{mission.target_skill.name}</Badge> : null}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <Button
            size="sm"
            variant={isCompleted ? "secondary" : "primary"}
            onClick={handleComplete}
            disabled={isCompleted || completeMission.isPending}
          >
            <CheckCircle2 className="h-4 w-4" />
            {isCompleted ? "Completed" : completeMission.isPending ? "Saving…" : "Mark complete"}
          </Button>
          <Button size="sm" variant="ghost" asChild>
            <Link href="/trust-center">Why?</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
