"use client";

import { FileText, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useResume, useUploadResume } from "@/hooks/use-resume";
import { ApiError } from "@/lib/api-client";
import { formatDateTime, formatPercent, titleCase } from "@/lib/utils";

const STATUS_VARIANT: Record<string, "positive" | "warning" | "danger" | "muted"> = {
  parsed: "positive",
  pending: "warning",
  failed: "danger",
};

function ResumeBody() {
  const { data: resume, isLoading, isError, error, refetch } = useResume();
  const uploadResume = useUploadResume();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    try {
      await uploadResume.mutateAsync(file);
      toast.success("Resume uploaded and parsed.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't upload resume.");
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Resume</h1>
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
          <Card>
            <CardHeader className="flex-row items-center justify-between gap-2">
              <div>
                <CardTitle>{resume.original_filename}</CardTitle>
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
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Detected skills ({resume.resume_skills.length})</CardTitle>
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
              <CardTitle>Sections ({resume.sections.length})</CardTitle>
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
