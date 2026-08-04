import Link from "next/link";
import { Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { formatPercent } from "@/lib/utils";
import type { JobDescriptionStatusOut } from "@/types/api";

export function JobDescriptionStatusCard({ status }: { status: JobDescriptionStatusOut }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <Target className="h-4 w-4 text-brand" aria-hidden="true" />
        <CardTitle>Job match</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {status.added ? (
          <>
            <p className="truncate text-sm text-foreground">{status.title}</p>
            <Progress value={(status.coverage ?? 0) * 100} />
            <p className="text-xs text-muted">
              Coverage {formatPercent(status.coverage)} · {status.matched_count} matched · {status.partial_count}{" "}
              partial · {status.missing_count} missing
            </p>
          </>
        ) : (
          <p className="text-xs text-muted">No job description added yet.</p>
        )}
        <Button variant="outline" size="sm" asChild>
          <Link href="/job-description">{status.added ? "View match details" : "Add job description"}</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
