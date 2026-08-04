"use client";

import Link from "next/link";
import { CheckCircle2, Compass } from "lucide-react";
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
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-2">
        <div>
          <CardTitle>Today&apos;s mission</CardTitle>
        </div>
        <Badge variant="muted">{titleCase(mission.source_component.replace("_readiness", ""))}</Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm font-semibold text-foreground">{mission.title}</p>
        <p className="text-sm text-muted">{mission.description}</p>
        {mission.target_skill ? <Badge>{mission.target_skill.name}</Badge> : null}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant={isCompleted ? "secondary" : "primary"}
            onClick={handleComplete}
            disabled={isCompleted || completeMission.isPending}
            className="mt-1"
          >
            <CheckCircle2 className="h-4 w-4" />
            {isCompleted ? "Completed" : completeMission.isPending ? "Saving…" : "Mark complete"}
          </Button>
          <Button size="sm" variant="ghost" className="mt-1" asChild>
            <Link href="/trust-center">Why?</Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
