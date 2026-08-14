import { History } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { formatDateTime, formatPercent } from "@/lib/utils";
import type { TwinUpdateSummaryOut } from "@/types/api";

export function TwinTimeline({ updates }: { updates: TwinUpdateSummaryOut[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Career Twin updates</CardTitle>
      </CardHeader>
      <CardContent>
        {updates.length === 0 ? (
          <EmptyState icon={History} title="No updates yet" description="Your first snapshot appears after onboarding." />
        ) : (
          <ol className="relative space-y-5 before:absolute before:left-[7px] before:top-2 before:bottom-2 before:w-px before:bg-border">
            {updates.map((update) => (
              <li key={update.version} className="relative pl-6">
                <span className="absolute left-0 top-1.5 h-3.5 w-3.5 rounded-full border-2 border-background bg-gradient-brand shadow-[var(--shadow-glow-brand)]" />
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-foreground">Version {update.version}</span>
                  <span className="text-xs text-muted">{formatDateTime(update.created_at)}</span>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted">{update.change_summary}</p>
                <p
                  className={`mt-1.5 text-[11px] font-medium ${
                    update.score_delta === null
                      ? "text-muted"
                      : update.score_delta >= 0
                        ? "text-positive"
                        : "text-danger"
                  }`}
                >
                  Overall {formatPercent(update.overall_score)}
                  {update.score_delta !== null
                    ? ` (${update.score_delta >= 0 ? "+" : ""}${Math.round(update.score_delta * 100)}%)`
                    : ""}
                </p>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
