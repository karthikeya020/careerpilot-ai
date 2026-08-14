"use client";

import { CheckCircle2, Clock, FileText, History, Rocket, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { MissionCard } from "@/components/dashboard/mission-card";
import { BulletStrengthPanel } from "@/components/resume/bullet-strength-panel";
import { GraphDiagnosisPanel } from "@/components/resume/graph-diagnosis-panel";
import { ParseabilityPanel } from "@/components/resume/parseability-panel";
import { RecruiterCardPanel } from "@/components/resume/recruiter-card-panel";
import { RewriteSuggestionsPanel } from "@/components/resume/rewrite-suggestions-panel";
import { SelfConsistencyPanel } from "@/components/resume/self-consistency-panel";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/hooks/use-dashboard";
import {
  useActivateResume,
  useRecruiterCard,
  useResume,
  useResumeAnalysis,
  useResumeHistory,
  useUploadResume,
} from "@/hooks/use-resume";
import { ApiError } from "@/lib/api-client";
import { formatDateTime, formatPercent, titleCase } from "@/lib/utils";
import type { ResumeSummaryOut } from "@/types/api";

const STATUS_VARIANT: Record<string, "positive" | "warning" | "danger" | "muted"> = {
  parsed: "positive",
  pending: "warning",
  failed: "danger",
};

function FirstMissionCallout() {
  const { data: dashboard } = useDashboard();
  if (!dashboard?.mission) return null;

  return (
    <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-brand/30 bg-brand-soft/40 p-5">
      <div className="mb-3 flex items-center gap-2">
        <Rocket className="h-4 w-4 text-brand" aria-hidden="true" />
        <p className="text-sm font-semibold text-brand">Your first diagnosed gap and mission are ready</p>
      </div>
      <MissionCard mission={dashboard.mission} />
    </div>
  );
}

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
    <Card className="animate-fade-up delay-6">
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
              <button
                type="button"
                onClick={() => handleActivate(resume)}
                disabled={activateResume.isPending}
                className="rounded-[var(--radius-sm)] border border-border-strong px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-surface-muted disabled:opacity-50"
              >
                Make active
              </button>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function ResumeBody() {
  const { data: resume, isLoading, isError, error, refetch } = useResume();
  const { data: analysis, isLoading: analysisLoading } = useResumeAnalysis();
  const { data: recruiterCard } = useRecruiterCard();
  const uploadResume = useUploadResume();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [justUploaded, setJustUploaded] = useState(false);

  const handleFile = async (file: File | undefined) => {
    if (!file) return;
    try {
      await uploadResume.mutateAsync(file);
      setJustUploaded(true);
      toast.success("Resume uploaded and parsed — it's now your active resume. Career Twin and job matches have been recomputed.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't upload resume.");
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
            <FileText className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Resume Intelligence</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Every claim on your resume, graded for real evidence -- not just keywords. Bullet strength, self-consistency,
          a genuine ATS parseability check, and exactly what a recruiter&apos;s first six-second scan would notice.
        </p>
      </div>

      <Card className="animate-fade-up">
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

      {justUploaded && <FirstMissionCallout />}

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
          <Card variant="glow-brand" className="animate-fade-up">
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
            <CardContent className="pt-0">
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
                Detected skills ({resume.resume_skills.length})
              </p>
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
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
            <div className="space-y-6">
              {analysisLoading ? (
                <Skeleton className="h-64" />
              ) : analysis?.has_resume ? (
                <>
                  <BulletStrengthPanel grades={analysis.bullet_grades} />
                  <SelfConsistencyPanel flags={analysis.self_consistency_flags} />
                  {analysis.parseability && <ParseabilityPanel parseability={analysis.parseability} />}
                  <GraphDiagnosisPanel insights={analysis.graph_diagnosis} />
                  <RewriteSuggestionsPanel />
                </>
              ) : null}

              <Card className="animate-fade-up">
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

              <ResumeHistoryCard />
            </div>

            <div className="lg:sticky lg:top-6 lg:self-start">
              {recruiterCard && <RecruiterCardPanel card={recruiterCard} />}
            </div>
          </div>
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
