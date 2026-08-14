"use client";

import { useEffect } from "react";
import { Printer, ScrollText } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useResearchReport } from "@/hooks/use-research-lab";
import { formatDateTime } from "@/lib/utils";

function jsonPreview(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function ReportBody() {
  const { data: report, isLoading, isError, error, refetch } = useResearchReport();

  useEffect(() => {
    refetch();
    // Fires once on mount -- this page's whole purpose is to generate a fresh report.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isLoading || (!report && !isError)) {
    return (
      <div className="mx-auto max-w-4xl space-y-4">
        <p className="text-center text-sm text-muted">
          Generating the full research report -- this runs every evaluation for real and can take up to a minute.
        </p>
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (isError || !report) {
    return (
      <div className="mx-auto max-w-4xl">
        <ErrorState message={error instanceof Error ? error.message : "Couldn't generate the research report."} onRetry={() => refetch()} titleAs="h1" />
      </div>
    );
  }

  const sections: { key: keyof typeof report; title: string }[] = [
    { key: "calibration", title: "Confidence calibration" },
    { key: "ablations", title: "Six-ablation comparison" },
    { key: "efficiency_frontier", title: "CARE efficiency frontier" },
    { key: "threshold_tuning", title: "Empirical threshold tuning" },
    { key: "adversarial_suite", title: "Adversarial robustness suite" },
    { key: "fallback_fidelity", title: "Fallback fidelity" },
    { key: "fairness_probe", title: "Fairness probe" },
    { key: "drift_canary", title: "Scoring-drift canary" },
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="print-hidden flex items-center justify-between">
        <p className="text-sm text-muted">A single, exportable research artifact -- every section is a real, freshly-run result.</p>
        <Button onClick={() => window.print()}>
          <Printer className="h-4 w-4" aria-hidden="true" /> Print / Save as PDF
        </Button>
      </div>

      <Card className="border-2 border-brand/30">
        <CardHeader className="flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand">
              <ScrollText className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
            </span>
            <div>
              <h1 className="text-lg font-semibold tracking-tight text-foreground">CareerPilot AI Research Report</h1>
              <p className="text-xs text-muted">Generated {formatDateTime(report.generated_at)}</p>
            </div>
          </div>
          <Badge>{report.report_version}</Badge>
        </CardHeader>
      </Card>

      {sections.map(({ key, title }) => (
        <Card key={key}>
          <CardHeader>
            <h2 className="text-base font-semibold text-foreground">{title}</h2>
          </CardHeader>
          <CardContent>
            <pre className="max-h-[32rem] overflow-auto rounded-[var(--radius-md)] bg-surface-muted p-3 text-[11px] leading-relaxed text-foreground">
              {jsonPreview(report[key])}
            </pre>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function ResearchReportPage() {
  return (
    <Protected>
      <ReportBody />
    </Protected>
  );
}
