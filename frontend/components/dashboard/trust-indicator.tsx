import { ShieldCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SystemTrustOut } from "@/types/api";

export function TrustIndicator({ trust }: { trust: SystemTrustOut }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <ShieldCheck className="h-4 w-4 text-positive" aria-hidden="true" />
        <CardTitle>System trust</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-3 gap-3 text-center">
        <div className="rounded-[var(--radius-sm)] bg-surface-muted py-2.5">
          <p className="text-lg font-bold tabular-nums text-foreground">
            {trust.components_scored}/{trust.components_total}
          </p>
          <p className="text-[11px] text-muted">Components scored</p>
        </div>
        <div className="rounded-[var(--radius-sm)] bg-surface-muted py-2.5">
          <p className="text-lg font-bold tabular-nums text-foreground">{trust.total_evidence_count}</p>
          <p className="text-[11px] text-muted">Evidence items</p>
        </div>
        <div className="rounded-[var(--radius-sm)] bg-surface-muted py-2.5">
          <p className="text-lg font-bold tabular-nums text-foreground">{trust.formula_version}</p>
          <p className="text-[11px] text-muted">Scoring formula</p>
        </div>
      </CardContent>
    </Card>
  );
}
