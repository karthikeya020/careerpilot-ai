"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Braces, Briefcase, Building2, FileText, Mic, Shuffle, Sparkles, Users } from "lucide-react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/hooks/use-dashboard";
import { useStartInterview } from "@/hooks/use-interview";
import { useJobDescriptions } from "@/hooks/use-job-description";
import { useStaggerReveal } from "@/hooks/use-stagger-reveal";
import { ApiError } from "@/lib/api-client";
import type { InterviewMode } from "@/types/api";

const MODE_INFO: Record<InterviewMode, { label: string; description: string; icon: typeof Mic; accent: string }> = {
  hr: {
    label: "HR / Behavioral",
    description: "STAR-style behavioral questions about teamwork, conflict, and ownership.",
    icon: Users,
    accent: "var(--color-accent-2)",
  },
  technical: {
    label: "Technical",
    description: "Concept-based technical questions drawn from your assessment domains.",
    icon: Briefcase,
    accent: "var(--color-brand)",
  },
  dsa: {
    label: "DSA / CS Fundamentals",
    description: "Classic data structures and algorithms questions, explained verbally -- no code editor.",
    icon: Braces,
    accent: "var(--color-brand-2)",
  },
  resume: {
    label: "Resume-based",
    description: "Questions probing specific claims and projects on your uploaded resume.",
    icon: FileText,
    accent: "var(--color-positive)",
  },
  role_specific: {
    label: "Target-role-specific",
    description: "Questions tailored to your primary target role.",
    icon: Briefcase,
    accent: "var(--color-brand-2)",
  },
  company_context: {
    label: "Company context",
    description: "Questions grounded in a specific job description you've added.",
    icon: Building2,
    accent: "var(--color-warning)",
  },
  mixed: {
    label: "Mixed",
    description: "A blend of behavioral, technical, resume, and role-specific questions.",
    icon: Shuffle,
    accent: "var(--color-accent)",
  },
};

const MODE_ORDER: InterviewMode[] = ["hr", "technical", "dsa", "resume", "role_specific", "company_context", "mixed"];

function InterviewSetup() {
  const router = useRouter();
  const params = useSearchParams();
  const { data: dashboard, isLoading: dashboardLoading } = useDashboard();
  const { data: jobDescriptions } = useJobDescriptions();
  const startInterview = useStartInterview();
  const cardsRef = useStaggerReveal<HTMLDivElement>(true, { delay: 70, y: 24 });
  const [selectedJdId, setSelectedJdId] = useState<string>("");
  const [startingMode, setStartingMode] = useState<InterviewMode | null>(null);

  const targetRoleId = dashboard?.target_role?.id ?? null;

  // Deep-linked from Job Match's "Prepare for this job" -- e.g.
  // /interview?mode=company_context&company=Google skips straight to a
  // company-tailored interview for that tracked dream job, no manual JD
  // selection required.
  const prefillMode = params.get("mode");
  const prefillCompany = params.get("company");

  const handleStart = (mode: InterviewMode, companyNameOverride?: string) => {
    const needsJd = mode === "company_context" && !companyNameOverride;
    if (needsJd && !selectedJdId) {
      toast.error("Add a job description first, or pick a different mode.");
      return;
    }
    setStartingMode(mode);
    startInterview.mutate(
      {
        mode,
        target_role_id: targetRoleId,
        job_description_id: companyNameOverride ? null : selectedJdId || null,
        company_name: companyNameOverride || null,
      },
      {
        onSuccess: (data) => {
          router.push(`/interview/${data.session.id}`);
        },
        onError: (err) => {
          setStartingMode(null);
          toast.error(err instanceof ApiError ? err.message : "Couldn't start the interview.");
        },
      }
    );
  };

  useEffect(() => {
    if (
      prefillMode === "company_context" &&
      prefillCompany &&
      !startInterview.isPending &&
      !startInterview.isSuccess
    ) {
      handleStart("company_context", prefillCompany);
    }
    // Only ever auto-start once, from the initial deep-link params.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefillMode, prefillCompany]);

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
            <Mic className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Interview Arena</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Practice a mock interview with voice or typed answers. Multi-agent specialists evaluate each answer and
          your Career Twin updates when the evidence justifies it.
        </p>

        <div className="relative mt-5 flex flex-wrap items-center gap-2">
          {dashboardLoading ? (
            <Skeleton className="h-8 w-64" />
          ) : dashboard?.target_role ? (
            <Badge className="gap-1">
              <Sparkles className="h-3 w-3" aria-hidden="true" /> Target role: {dashboard.target_role.title}
            </Badge>
          ) : (
            <Badge variant="muted">No target role set — role-specific questions will be generic</Badge>
          )}
          {jobDescriptions && jobDescriptions.length > 0 ? (
            <select
              className="rounded-[var(--radius-md)] border border-border bg-surface px-2 py-1.5 text-xs text-foreground"
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
            <Badge variant="muted">No job description added — company-context mode needs one</Badge>
          )}
        </div>
      </div>

      <div ref={cardsRef} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {MODE_ORDER.map((mode) => {
          const info = MODE_INFO[mode];
          const Icon = info.icon;
          const isStarting = startingMode === mode && startInterview.isPending;
          return (
            <Card key={mode} interactive className="relative overflow-hidden">
              <div
                className="absolute inset-x-0 top-0 h-1"
                style={{ background: `linear-gradient(90deg, ${info.accent}, transparent)` }}
                aria-hidden="true"
              />
              <CardHeader className="flex-row items-start gap-3">
                <span
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-md)]"
                  style={{ background: `color-mix(in srgb, ${info.accent} 16%, transparent)` }}
                >
                  <Icon className="h-4 w-4" style={{ color: info.accent }} aria-hidden="true" />
                </span>
                <div>
                  <CardTitle as="h2">{info.label}</CardTitle>
                  <CardDescription>{info.description}</CardDescription>
                </div>
              </CardHeader>
              <CardContent>
                <Button onClick={() => handleStart(mode)} disabled={startInterview.isPending} className="w-full">
                  {isStarting ? "Starting…" : "Start interview"}
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
      <Suspense fallback={<Skeleton className="h-64" />}>
        <InterviewSetup />
      </Suspense>
    </Protected>
  );
}
