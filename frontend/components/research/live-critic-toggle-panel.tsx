"use client";

import { useState } from "react";
import { ArrowRight, Radio, Zap } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useRunLiveCriticToggle } from "@/hooks/use-research-lab";
import { ApiError } from "@/lib/api-client";
import { formatPercent } from "@/lib/utils";

const SAMPLE_ANSWERS = [
  { label: "Thin answer", text: "Indexes are good." },
  {
    label: "Strong, cited answer",
    text: "An index speeds up lookups, however it adds write overhead and storage cost, for example a heavily-indexed table slows down inserts.",
  },
  {
    label: "Confident but uncited",
    text: "Trust me, indexes are always the right call here and dramatically improve every query with zero downsides.",
  },
];

export function LiveCriticTogglePanel() {
  const [transcript, setTranscript] = useState(SAMPLE_ANSWERS[0].text);
  const liveCritic = useRunLiveCriticToggle();

  const handleRun = () => {
    if (!transcript.trim()) {
      toast.error("Type an answer first.");
      return;
    }
    liveCritic.mutate(
      { transcript },
      { onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't run the live toggle.") }
    );
  };

  const result = liveCritic.data;

  return (
    <Card variant="glow-accent" className="animate-fade-up">
      <CardHeader>
        <CardTitle as="h2" className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-brand" aria-hidden="true" /> Live on stage: toggle the Critic
        </CardTitle>
        <CardDescription>
          Type any interview answer (or use a judge&apos;s suggestion) and watch the Critic pass&apos;s effect on
          confidence appear in real time.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-1.5">
          {SAMPLE_ANSWERS.map((sample) => (
            <button
              key={sample.label}
              type="button"
              onClick={() => setTranscript(sample.text)}
              className="rounded-full border border-border-strong px-2.5 py-1 text-xs text-muted transition-colors hover:bg-surface-muted hover:text-foreground"
            >
              {sample.label}
            </button>
          ))}
        </div>
        <textarea
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          rows={3}
          className="w-full rounded-[var(--radius-md)] border border-border bg-surface p-3 text-sm text-foreground"
          aria-label="Interview answer transcript"
        />
        <Button onClick={handleRun} disabled={liveCritic.isPending} size="lg">
          <Zap className="h-4 w-4" aria-hidden="true" /> {liveCritic.isPending ? "Scoring..." : "Run live"}
        </Button>

        {result && (
          <div className="animate-scale-in flex flex-col items-center gap-4 rounded-[var(--radius-lg)] border border-border bg-surface-muted/40 p-5 sm:flex-row sm:justify-around">
            <div className="text-center">
              <p className="text-xs uppercase tracking-wide text-muted">Critic off (raw mean)</p>
              <p className="text-metric text-foreground">{formatPercent(result.critic_off_confidence)}</p>
            </div>
            <ArrowRight className="h-6 w-6 shrink-0 rotate-90 text-muted sm:rotate-0" aria-hidden="true" />
            <div className="text-center">
              <p className="text-xs uppercase tracking-wide text-muted">Critic on (real pass)</p>
              <p className="text-metric text-gradient-brand">{formatPercent(result.critic_on_confidence)}</p>
              <Badge variant={result.delta < 0 ? "warning" : "positive"} className="mt-1">
                {result.delta >= 0 ? "+" : ""}
                {(result.delta * 100).toFixed(0)}pp
              </Badge>
            </div>
          </div>
        )}
        {result && result.issues_found.length > 0 && (
          <div className="space-y-1 text-xs text-muted">
            <p className="font-medium text-foreground">Issues the Critic found:</p>
            {result.issues_found.map((issue, i) => (
              <p key={i}>- {issue}</p>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
