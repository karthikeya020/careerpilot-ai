"use client";

import { AlertOctagon, CheckCircle2, Wand2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useRewriteSuggestions } from "@/hooks/use-resume";
import { useTrackedJobs } from "@/hooks/use-job-catalog";

export function RewriteSuggestionsPanel() {
  const { data: tracked, isLoading: trackedLoading } = useTrackedJobs();
  const firstTracked = tracked?.[0] ?? null;
  const { data: suggestions, isLoading } = useRewriteSuggestions(firstTracked?.match.listing.id ?? null);

  return (
    <Card className="animate-fade-up delay-5">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <Wand2 className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">Suggested rewrites</CardTitle>
          <CardDescription>
            {firstTracked
              ? `Evidence-only bullet suggestions for your gap toward ${firstTracked.match.listing.company}. Never invents experience you don't have.`
              : "Track a dream job in Job Match to get evidence-only rewrite suggestions for its skill gaps."}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {trackedLoading || isLoading ? (
          <Skeleton className="h-24" />
        ) : !firstTracked ? (
          <EmptyState icon={Wand2} title="No tracked dream job yet" description="Add one from the Job Match page." />
        ) : !suggestions || suggestions.length === 0 ? (
          <p className="text-sm text-positive">
            Every required skill for {firstTracked.match.listing.company} already has strong resume evidence.
          </p>
        ) : (
          <div className="space-y-2.5">
            {suggestions.map((s, i) => (
              <div key={i} className="rounded-[var(--radius-md)] border border-border p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-foreground">{s.skill_name}</p>
                  <Badge variant={s.status === "missing" ? "danger" : "warning"}>{s.status}</Badge>
                </div>
                {s.has_sufficient_evidence ? (
                  <p className="mt-2 flex items-start gap-2 text-sm text-foreground">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-positive" aria-hidden="true" />
                    &ldquo;{s.rewritten_bullet}&rdquo;
                  </p>
                ) : (
                  <p className="mt-2 flex items-start gap-2 text-sm text-muted">
                    <AlertOctagon className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" aria-hidden="true" /> {s.note}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
