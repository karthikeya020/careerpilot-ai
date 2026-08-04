import { FileSearch } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { formatDateTime, formatPercent, titleCase } from "@/lib/utils";
import type { EvidenceItemOut } from "@/types/api";

export function EvidenceFeed({ evidence }: { evidence: EvidenceItemOut[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent evidence</CardTitle>
      </CardHeader>
      <CardContent>
        {evidence.length === 0 ? (
          <EmptyState
            icon={FileSearch}
            title="No evidence yet"
            description="Upload a resume to start building your evidence ledger."
          />
        ) : (
          <ul className="space-y-3">
            {evidence.map((item) => (
              <li key={item.id} className="border-b border-border pb-3 last:border-0 last:pb-0">
                <div className="mb-1 flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-foreground">{item.skill_name}</span>
                  <Badge variant="muted">{titleCase(item.evidence_type)}</Badge>
                </div>
                <p className="text-xs text-muted">{item.explanation}</p>
                <p className="mt-1 text-[11px] text-muted">
                  Score {formatPercent(item.normalized_score)} · Confidence {formatPercent(item.confidence)} ·{" "}
                  {formatDateTime(item.created_at)}
                </p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
