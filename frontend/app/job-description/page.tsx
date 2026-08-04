"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Target } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useCreateJobDescription, useJobDescriptionMatch, useJobDescriptions } from "@/hooks/use-job-description";
import { ApiError } from "@/lib/api-client";
import { jobDescriptionSchema, type JobDescriptionFormValues } from "@/lib/schemas";
import { formatPercent } from "@/lib/utils";
import type { SkillOut } from "@/types/api";

function SkillPillList({ skills, tone }: { skills: SkillOut[]; tone: "positive" | "warning" | "danger" }) {
  if (skills.length === 0) return <p className="text-xs text-muted">None</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {skills.map((skill) => (
        <Badge key={skill.id} variant={tone}>
          {skill.name}
        </Badge>
      ))}
    </div>
  );
}

function JobDescriptionBody() {
  const { data: jobDescriptions, isLoading, isError, error, refetch } = useJobDescriptions();
  const createJobDescription = useCreateJobDescription();
  const [explicitSelectedId, setSelectedId] = useState<string | undefined>(undefined);
  // Default to the most recent job description without mirroring it into
  // state via an effect -- derive it directly from the query result.
  const selectedId = explicitSelectedId ?? jobDescriptions?.[0]?.id;

  const { data: match, isLoading: matchLoading } = useJobDescriptionMatch(selectedId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<JobDescriptionFormValues>({ resolver: zodResolver(jobDescriptionSchema) });

  const onSubmit = async (values: JobDescriptionFormValues) => {
    try {
      const created = await createJobDescription.mutateAsync(values);
      setSelectedId(created.id);
      reset();
      toast.success("Job description added and matched against your resume.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't add job description.");
    }
  };

  const selected = jobDescriptions?.find((jd) => jd.id === selectedId);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Job description match</h1>
        <p className="mt-1 text-sm text-muted">
          Paste a job description to see which required skills your resume already demonstrates.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Add a job description</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="jd-title">Job title</Label>
                <Input id="jd-title" {...register("title")} aria-invalid={!!errors.title} />
                {errors.title ? (
                  <p className="text-xs text-danger" role="alert">
                    {errors.title.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="jd-company">Company (optional)</Label>
                <Input id="jd-company" {...register("company")} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="jd-text">Job description</Label>
              <Textarea id="jd-text" rows={8} {...register("raw_text")} aria-invalid={!!errors.raw_text} />
              {errors.raw_text ? (
                <p className="text-xs text-danger" role="alert">
                  {errors.raw_text.message}
                </p>
              ) : null}
            </div>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Matching…" : "Add and match"}
            </Button>
          </form>
        </CardContent>
      </Card>

      {isLoading ? (
        <Skeleton className="h-48" />
      ) : isError ? (
        <ErrorState message={error instanceof Error ? error.message : "Couldn't load job descriptions."} onRetry={() => refetch()} />
      ) : !jobDescriptions || jobDescriptions.length === 0 ? (
        <EmptyState icon={Target} title="No job descriptions yet" description="Add one above to see your match." />
      ) : (
        <>
          {jobDescriptions.length > 1 ? (
            <div className="flex flex-wrap gap-2">
              {jobDescriptions.map((jd) => (
                <Button
                  key={jd.id}
                  size="sm"
                  variant={jd.id === selectedId ? "primary" : "outline"}
                  onClick={() => setSelectedId(jd.id)}
                >
                  {jd.title}
                </Button>
              ))}
            </div>
          ) : null}

          {selected ? (
            <Card>
              <CardHeader>
                <CardTitle>{selected.title}</CardTitle>
                <CardDescription>{selected.company ?? "No company specified"}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {matchLoading || !match ? (
                  <Skeleton className="h-32" />
                ) : (
                  <>
                    <div>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="text-muted">Coverage</span>
                        <span className="font-medium text-foreground">{formatPercent(match.coverage)}</span>
                      </div>
                      <Progress value={(match.coverage ?? 0) * 100} />
                    </div>
                    <p className="text-xs text-muted">{match.explanation}</p>
                    <div className="grid gap-3 sm:grid-cols-3">
                      <div>
                        <p className="mb-1 text-xs font-semibold text-foreground">Matched</p>
                        <SkillPillList skills={match.matched_skills} tone="positive" />
                      </div>
                      <div>
                        <p className="mb-1 text-xs font-semibold text-foreground">Partial</p>
                        <SkillPillList skills={match.partial_skills} tone="warning" />
                      </div>
                      <div>
                        <p className="mb-1 text-xs font-semibold text-foreground">Missing</p>
                        <SkillPillList skills={match.missing_skills} tone="danger" />
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          ) : null}
        </>
      )}
    </div>
  );
}

export default function JobDescriptionPage() {
  return (
    <Protected>
      <JobDescriptionBody />
    </Protected>
  );
}
