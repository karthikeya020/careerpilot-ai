"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Briefcase, Building2, FileText, Mic, Shuffle, Users } from "lucide-react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/hooks/use-dashboard";
import { useStartInterview } from "@/hooks/use-interview";
import { useJobDescriptions } from "@/hooks/use-job-description";
import { ApiError } from "@/lib/api-client";
import type { InterviewMode } from "@/types/api";

const MODE_INFO: Record<InterviewMode, { label: string; description: string; icon: typeof Mic }> = {
  hr: { label: "HR / Behavioral", description: "STAR-style behavioral questions about teamwork, conflict, and ownership.", icon: Users },
  technical: { label: "Technical", description: "Concept-based technical questions drawn from your assessment domains.", icon: Briefcase },
  resume: { label: "Resume-based", description: "Questions probing specific claims and projects on your uploaded resume.", icon: FileText },
  role_specific: { label: "Target-role-specific", description: "Questions tailored to your primary target role.", icon: Briefcase },
  company_context: { label: "Company context", description: "Questions grounded in a specific job description you've added.", icon: Building2 },
  mixed: { label: "Mixed", description: "A blend of behavioral, technical, resume, and role-specific questions.", icon: Shuffle },
};

const MODE_ORDER: InterviewMode[] = ["hr", "technical", "resume", "role_specific", "company_context", "mixed"];

function InterviewSetup() {
  const router = useRouter();
  const { data: dashboard, isLoading: dashboardLoading } = useDashboard();
  const { data: jobDescriptions } = useJobDescriptions();
  const startInterview = useStartInterview();
  const [selectedJdId, setSelectedJdId] = useState<string>("");

  const targetRoleId = dashboard?.target_role?.id ?? null;

  const handleStart = (mode: InterviewMode) => {
    const needsJd = mode === "company_context";
    if (needsJd && !selectedJdId) {
      toast.error("Add a job description first, or pick a different mode.");
      return;
    }
    startInterview.mutate(
      {
        mode,
        target_role_id: targetRoleId,
        job_description_id: selectedJdId || null,
      },
      {
        onSuccess: (data) => {
          router.push(`/interview/${data.session.id}`);
        },
        onError: (err) => {
          toast.error(err instanceof ApiError ? err.message : "Couldn't start the interview.");
        },
      }
    );
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
          <Mic className="h-5 w-5 text-brand" aria-hidden="true" />
          Interview Arena
        </h1>
        <p className="mt-1 text-sm text-muted">
          Practice a mock interview with voice or typed answers. Multi-agent specialists evaluate each answer and
          your Career Twin updates when the evidence justifies it.
        </p>
      </div>

      {dashboardLoading ? (
        <Skeleton className="h-10 w-64" />
      ) : (
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted">
          {dashboard?.target_role ? (
            <Badge variant="default">Target role: {dashboard.target_role.title}</Badge>
          ) : (
            <Badge variant="muted">No target role set -- role-specific questions will be generic</Badge>
          )}
          {jobDescriptions && jobDescriptions.length > 0 ? (
            <select
              className="rounded-[var(--radius-md)] border border-border bg-surface px-2 py-1 text-xs text-foreground"
              value={selectedJdId}
              onChange={(e) => setSelectedJdId(e.target.value)}
              aria-label="Job description for company-context mode"
            >
              <option value="">No job description selected</option>
              {jobDescriptions.map((jd) => (
                <option key={jd.id} value={jd.id}>
                  {jd.title}
                  {jd.company ? ` @ ${jd.company}` : ""}
                </option>
              ))}
            </select>
          ) : (
            <Badge variant="muted">No job description added -- company-context mode needs one</Badge>
          )}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {MODE_ORDER.map((mode) => {
          const info = MODE_INFO[mode];
          const Icon = info.icon;
          return (
            <Card key={mode}>
              <CardHeader className="flex-row items-center gap-2">
                <Icon className="h-4 w-4 text-brand" aria-hidden="true" />
                <div>
                  <CardTitle>{info.label}</CardTitle>
                  <CardDescription>{info.description}</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <Button onClick={() => handleStart(mode)} disabled={startInterview.isPending}>
                  {startInterview.isPending ? "Starting..." : "Start interview"}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

export default function InterviewPage() {
  return (
    <Protected>
      <InterviewSetup />
    </Protected>
  );
}
