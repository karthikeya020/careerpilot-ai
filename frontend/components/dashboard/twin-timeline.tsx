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
          <ol className="space-y-3">
            {updates.map((update) => (
              <li key={update.version} className="border-b border-border pb-3 last:border-0 last:pb-0">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-foreground">Version {update.version}</span>
                  <span className="text-muted">{formatDateTime(update.created_at)}</span>
                </div>
                <p className="mt-1 text-xs text-muted">{update.change_summary}</p>
                <p className="mt-1 text-[11px] text-muted">
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
