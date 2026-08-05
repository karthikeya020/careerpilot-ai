"use client";

import { CheckCircle2, Clock, FileText, History, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useActivateResume, useResume, useResumeHistory, useUploadResume } from "@/hooks/use-resume";
import { ApiError } from "@/lib/api-client";
import { formatDateTime, formatPercent, titleCase } from "@/lib/utils";
import type { ResumeSummaryOut } from "@/types/api";

const STATUS_VARIANT: Record<string, "positive" | "warning" | "danger" | "muted"> = {
  parsed: "positive",
  pending: "warning",
  failed: "danger",
};

function ResumeHistoryCard() {
  const { data: history, isLoading } = useResumeHistory();
  const activateResume = useActivateResume();

  const handleActivate = async (resume: ResumeSummaryOut) => {
    try {
      await activateResume.mutateAsync(resume.id);
      toast.success(
        `"${resume.original_filename}" is now your active resume. Career Twin, job matches, and missions have been recomputed.`,
      );
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't activate this resume version.");
    }
  };

  if (isLoading) return <Skeleton className="h-32" />;
  if (!history || history.length < 2) return null;

  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <History className="h-4 w-4 text-brand" aria-hidden="true" />
        <div>
          <CardTitle as="h2">Resume history</CardTitle>
          <CardDescription>
            Only your active resume drives your Career Twin, job matches, and missions. Older versions stay here,
            not deleted — reactivate one anytime.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {history.map((resume) => (
          <div
            key={resume.id}
            className="flex flex-wrap items-center justify-between gap-2 rounded-[var(--radius-md)] border border-border p-3"
          >
            <div className="min-w-0">
              <p className="flex items-center gap-2 truncate text-sm font-medium text-foreground">
                {resume.original_filename}
                {resume.is_active && (
                  <Badge variant="positive" className="gap-1 shrink-0">
                    <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> Active
                  </Badge>
                )}
              </p>
              <p className="text-xs text-muted">
                {resume.skill_count} skill(s) detected · uploaded {formatDateTime(resume.uploaded_at)}
                {!resume.is_active && resume.superseded_at && (
                  <> · superseded {formatDateTime(resume.superseded_at)}</>
                )}
              </p>
            </div>
            {!resume.is_active && resume.parsing_status === "parsed" && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleActivate(resume)}
                disabled={activateResume.isPending}
              >
                Make active
              </Button>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function ResumeBody() {
  const { data: resume, isLoading, isError, error, refetch } = useResume();
  const uploadResume = useUploadResume();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    try {
      await uploadResume.mutateAsync(file);
      toast.success("Resume uploaded and parsed — it's now your active resume. Career Twin and job matches have been recomputed.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't upload resume.");
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-h1 text-foreground">Resume</h1>
        <p className="mt-1 text-sm text-muted">Upload a PDF, DOCX, or text resume to extract skill evidence.</p>
      </div>

      <Card>
        <CardContent
          className="pt-5"
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            void handleFile(e.dataTransfer.files?.[0]);
          }}
        >
          <label
            htmlFor="resume-upload"
            className={`flex cursor-pointer flex-col items-center gap-2 rounded-[var(--radius-md)] border-2 border-dashed p-8 text-center transition-colors ${
              dragActive ? "border-brand bg-brand-soft" : "border-border"
            }`}
          >
            <Upload className="h-6 w-6 text-brand" aria-hidden="true" />
            <span className="text-sm font-medium text-foreground">
              {uploadResume.isPending ? "Uploading…" : "Click to upload or drag a file here"}
            </span>
            <span className="text-xs text-muted">PDF, DOCX, or TXT — up to 5MB</span>
            <input
              ref={inputRef}
              id="resume-upload"
              type="file"
              accept=".pdf,.docx,.txt"
              className="sr-only"
              disabled={uploadResume.isPending}
              onChange={(e) => void handleFile(e.target.files?.[0])}
            />
          </label>
        </CardContent>
      </Card>

      {isLoading ? (
        <Skeleton className="h-48" />
      ) : isError ? (
        error instanceof ApiError && error.status === 404 ? (
          <EmptyState icon={FileText} title="No resume uploaded yet" description="Upload one above to get started." />
        ) : (
          <ErrorState message={error instanceof Error ? error.message : "Couldn't load resume."} onRetry={() => refetch()} />
        )
      ) : resume ? (
        <>
          <Card variant="glow-brand">
            <CardHeader className="flex-row items-center justify-between gap-2">
              <div>
                <CardTitle as="h2" className="flex items-center gap-2">
                  {resume.original_filename}
                  {resume.is_active ? (
                    <Badge variant="positive" className="gap-1">
                      <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> Active resume
                    </Badge>
                  ) : (
                    <Badge variant="warning" className="gap-1">
                      <Clock className="h-3 w-3" aria-hidden="true" /> Superseded
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  Uploaded {formatDateTime(resume.uploaded_at)} · {(resume.file_size / 1024).toFixed(0)} KB
                </CardDescription>
              </div>
              <Badge variant={STATUS_VARIANT[resume.parsing_status] ?? "muted"}>{resume.parsing_status}</Badge>
            </CardHeader>
            {resume.parsing_error ? (
              <CardContent>
                <p className="text-sm text-danger">{resume.parsing_error}</p>
              </CardContent>
            ) : null}
            {resume.is_active && (
              <CardContent className="pt-0">
                <p className="text-xs text-muted">
                  This is the resume currently driving your Career Twin, job matches, and missions. Skills from any
                  earlier resume version are excluded until you reactivate it below.
                </p>
              </CardContent>
            )}
          </Card>

          <ResumeHistoryCard />

          <Card>
            <CardHeader>
              <CardTitle as="h2">Detected skills ({resume.resume_skills.length})</CardTitle>
            </CardHeader>
            <CardContent>
              {resume.resume_skills.length === 0 ? (
                <p className="text-sm text-muted">No skills detected yet.</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {resume.resume_skills.map((rs) => (
                    <span
                      key={rs.skill.id}
                      title={rs.evidence_snippet}
                      className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-muted px-2.5 py-1 text-xs text-foreground"
                    >
                      {rs.skill.name}
                      <span className="text-muted">{formatPercent(rs.confidence)}</span>
                    </span>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle as="h2">Sections ({resume.sections.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {resume.sections.map((section) => (
                <div key={section.id}>
                  <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                    {titleCase(section.section_type)}
                  </p>
                  <p className="mt-1 whitespace-pre-line text-sm text-foreground">{section.raw_text}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

export default function ResumePage() {
  return (
    <Protected>
      <ResumeBody />
    </Protected>
  );
}
