"use client";

import Link from "next/link";
import { Activity } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useCareExecutions } from "@/hooks/use-trust-center";
import { titleCase } from "@/lib/utils";

const ROUTE_LABELS: Record<string, string> = {
  deterministic: "Deterministic",
  single_agent: "Single specialist",
  graphrag_agent: "GraphRAG",
  multi_agent: "Multi-agent",
  critic_reflection: "Critic/reflection",
  human_review: "Human review",
};

export function CareActivityCard() {
  const { data: executions, isLoading } = useCareExecutions(5);

  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <Activity className="h-4 w-4 text-brand" aria-hidden="true" />
        <CardTitle>CARE activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading ? (
          <Skeleton className="h-20" />
        ) : !executions || executions.length === 0 ? (
          <EmptyState title="No AI decisions yet" description="Take an assessment to see CARE route a decision." />
        ) : (
          <ul className="space-y-1.5 text-xs">
            {executions.map((execution) => (
              <li key={execution.id} className="flex items-center justify-between gap-2">
                <span className="truncate text-muted">{titleCase(execution.task_type)}</span>
                <Badge variant="muted">{ROUTE_LABELS[execution.route] ?? execution.route}</Badge>
              </li>
            ))}
          </ul>
        )}
        <Button variant="ghost" size="sm" asChild className="w-full">
          <Link href="/trust-center">View Trust Center</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
