import Link from "next/link";
import { FileText, Upload } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDateTime } from "@/lib/utils";
import type { ResumeStatusOut } from "@/types/api";

const STATUS_VARIANT: Record<string, "positive" | "warning" | "danger" | "muted"> = {
  parsed: "positive",
  pending: "warning",
  failed: "danger",
};

export function ResumeStatusCard({ status }: { status: ResumeStatusOut }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <FileText className="h-4 w-4 text-brand" aria-hidden="true" />
        <CardTitle>Resume</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {status.uploaded ? (
          <>
            <div className="flex items-center justify-between">
              <p className="truncate text-sm text-foreground">{status.filename}</p>
              <Badge variant={STATUS_VARIANT[status.parsing_status ?? ""] ?? "muted"}>
                {status.parsing_status}
              </Badge>
            </div>
            <p className="text-xs text-muted">
              {status.skills_detected} skill{status.skills_detected === 1 ? "" : "s"} detected · uploaded{" "}
              {formatDateTime(status.uploaded_at)}
            </p>
            {status.parsing_error ? <p className="text-xs text-danger">{status.parsing_error}</p> : null}
          </>
        ) : (
          <p className="text-xs text-muted">No resume uploaded yet.</p>
        )}
        <Button variant="outline" size="sm" asChild>
          <Link href="/resume">
            <Upload className="h-4 w-4" /> {status.uploaded ? "Replace resume" : "Upload resume"}
          </Link>
        </Button>
      </CardContent>
    </Card>
  );
}
