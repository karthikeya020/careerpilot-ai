"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronDown, FileText, Search, Sparkles, Target } from "lucide-react";
import { useMemo, useState } from "react";
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
import { JobCard, JobCardSkeleton } from "@/components/jobs/job-card";
import { TrackedJobPanel } from "@/components/jobs/tracked-job-panel";
import {
  useJobSearch,
  useJobSectors,
  useRecommendedJobs,
  useTrackJob,
  useTrackedJobs,
  useUntrackJob,
} from "@/hooks/use-job-catalog";
import { useCreateJobDescription, useJobDescriptionMatch, useJobDescriptions } from "@/hooks/use-job-description";
import { ApiError } from "@/lib/api-client";
import { jobDescriptionSchema, type JobDescriptionFormValues } from "@/lib/schemas";
import { cn, formatPercent } from "@/lib/utils";
import type { JobListingMatchOut, SkillOut } from "@/types/api";

function JobRow({
  title,
  description,
  matches,
  isLoading,
  onTrack,
  onUntrack,
  pendingId,
}: {
  title: string;
  description: string;
  matches: JobListingMatchOut[] | undefined;
  isLoading: boolean;
  onTrack: (id: string) => void;
  onUntrack: (id: string) => void;
  pendingId: string | null;
}) {
  return (
    <div className="space-y-2.5">
      <div>
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        <p className="text-xs text-muted">{description}</p>
      </div>
      <div className="flex snap-x snap-mandatory gap-4 overflow-x-auto pb-3">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <JobCardSkeleton key={i} />)
        ) : matches && matches.length > 0 ? (
          matches.map((m) => (
            <JobCard key={m.listing.id} match={m} onTrack={onTrack} onUntrack={onUntrack} isPending={pendingId === m.listing.id} />
          ))
        ) : (
          <p className="py-6 text-xs text-muted">No matches yet -- try a different sector or company.</p>
        )}
      </div>
    </div>
  );
}

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

function ManualJobDescriptionSection() {
  const [open, setOpen] = useState(false);
  const { data: jobDescriptions, isLoading, isError, error, refetch } = useJobDescriptions();
  const createJobDescription = useCreateJobDescription();
  const [explicitSelectedId, setSelectedId] = useState<string | undefined>(undefined);
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
    <Card>
      <CardHeader>
        <button type="button" onClick={() => setOpen((o) => !o)} className="flex w-full items-center justify-between gap-2 text-left">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted" aria-hidden="true" />
            <CardTitle as="h2" className="text-sm">
              Have a specific job posting instead? Paste it directly
            </CardTitle>
          </div>
          <ChevronDown className={cn("h-4 w-4 shrink-0 text-muted transition-transform", open && "rotate-180")} aria-hidden="true" />
        </button>
      </CardHeader>
      {open && (
        <CardContent className="animate-fade-in space-y-4">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="jd-title">Job title</Label>
                <Input id="jd-title" {...register("title")} aria-invalid={!!errors.title} />
                {errors.title && (
                  <p className="text-xs text-danger" role="alert">
                    {errors.title.message}
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="jd-company">Company (optional)</Label>
                <Input id="jd-company" {...register("company")} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="jd-text">Job description</Label>
              <Textarea id="jd-text" rows={6} {...register("raw_text")} aria-invalid={!!errors.raw_text} />
              {errors.raw_text && (
                <p className="text-xs text-danger" role="alert">
                  {errors.raw_text.message}
                </p>
              )}
            </div>
            <Button type="submit" size="sm" disabled={isSubmitting}>
              {isSubmitting ? "Matching…" : "Add and match"}
            </Button>
          </form>

          {isLoading ? (
            <Skeleton className="h-32" />
          ) : isError ? (
            <ErrorState message={error instanceof Error ? error.message : "Couldn't load job descriptions."} onRetry={() => refetch()} />
          ) : jobDescriptions && jobDescriptions.length > 0 ? (
            <>
              {jobDescriptions.length > 1 && (
                <div className="flex flex-wrap gap-2">
                  {jobDescriptions.map((jd) => (
                    <Button key={jd.id} size="sm" variant={jd.id === selectedId ? "primary" : "outline"} onClick={() => setSelectedId(jd.id)}>
                      {jd.title}
                    </Button>
                  ))}
                </div>
              )}
              {selected && (
                <Card>
                  <CardHeader>
                    <CardTitle as="h3" className="text-sm">
                      {selected.title}
                    </CardTitle>
                    <CardDescription>{selected.company ?? "No company specified"}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {matchLoading || !match ? (
                      <Skeleton className="h-28" />
                    ) : (
                      <>
                        <div>
                          <div className="mb-1 flex items-center justify-between text-sm">
                            <span className="text-muted">Coverage</span>
                            <span className="font-medium text-foreground">{formatPercent(match.coverage)}</span>
                          </div>
                          <Progress value={(match.coverage ?? 0) * 100} aria-label={`Coverage: ${formatPercent(match.coverage)}`} />
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
              )}
            </>
          ) : (
            <EmptyState icon={Target} title="No job descriptions pasted yet" />
          )}
        </CardContent>
      )}
    </Card>
  );
}

function JobMatchBody() {
  const { data: sectors } = useJobSectors();
  const { data: recommended, isLoading: recommendedLoading } = useRecommendedJobs();
  const [sector, setSector] = useState("");
  const [company, setCompany] = useState("");
  const [packageTier, setPackageTier] = useState("");
  const { data: searchResults, isLoading: searchLoading } = useJobSearch({ sector, company, packageTier });
  const { data: tracked, isLoading: trackedLoading } = useTrackedJobs();
  const [selectedTrackedId, setSelectedTrackedId] = useState<string | null>(null);

  const trackJob = useTrackJob();
  const untrackJob = useUntrackJob();
  const [pendingId, setPendingId] = useState<string | null>(null);

  const handleTrack = (listingId: string) => {
    setPendingId(listingId);
    trackJob.mutate(listingId, {
      onSuccess: () => toast.success("Added to your dream jobs. We'll keep tracking your readiness for it."),
      onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't track this job."),
      onSettled: () => setPendingId(null),
    });
  };

  const handleUntrack = (listingId: string) => {
    setPendingId(listingId);
    untrackJob.mutate(listingId, {
      onSettled: () => setPendingId(null),
    });
  };

  const selectedTracked = useMemo(
    () => tracked?.find((t) => t.match.listing.id === selectedTrackedId) ?? tracked?.[0],
    [tracked, selectedTrackedId],
  );

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
            <Target className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Job Match</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">
          Every role below is scored against your actual resume evidence -- no typing required. Track up to 5 dream
          jobs and we'll keep showing you exactly how ready you are and what closes the gap.
        </p>
      </div>

      <JobRow
        title="Recommended for you"
        description="Ranked by how well your resume already matches, across every sector."
        matches={recommended}
        isLoading={recommendedLoading}
        onTrack={handleTrack}
        onUntrack={handleUntrack}
        pendingId={pendingId}
      />

      <Card>
        <CardHeader>
          <CardTitle as="h2" className="flex items-center gap-1.5 text-sm">
            <Search className="h-4 w-4 text-brand" aria-hidden="true" /> Search by sector, dream company, or package
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="space-y-1.5">
              <Label htmlFor="sector-select">Sector</Label>
              <select
                id="sector-select"
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                className="w-full rounded-[var(--radius-md)] border border-border bg-surface px-3 py-2 text-sm text-foreground"
              >
                <option value="">Any sector</option>
                {sectors?.map((s) => (
                  <option key={s.slug} value={s.slug}>
                    {s.label} ({s.listing_count})
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="dream-company">Dream company</Label>
              <Input
                id="dream-company"
                placeholder="e.g. Google, Zerodha, Deloitte..."
                value={company}
                onChange={(e) => setCompany(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="package-select">Package</Label>
              <select
                id="package-select"
                value={packageTier}
                onChange={(e) => setPackageTier(e.target.value)}
                className="w-full rounded-[var(--radius-md)] border border-border bg-surface px-3 py-2 text-sm text-foreground"
              >
                <option value="">Any package</option>
                <option value="10">10+ LPA</option>
                <option value="20">20+ LPA</option>
                <option value="30">30+ LPA</option>
                <option value="40">40+ LPA</option>
              </select>
            </div>
          </div>

          <JobRow
            title={company || sector || packageTier ? "Matching your search" : "Browse all sectors"}
            description="Always at least 10 results -- we pad with the closest matches so you can compare."
            matches={searchResults}
            isLoading={searchLoading}
            onTrack={handleTrack}
            onUntrack={handleUntrack}
            pendingId={pendingId}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle as="h2" className="flex items-center gap-1.5 text-base">
            <Sparkles className="h-4 w-4 text-brand" aria-hidden="true" /> My Dream Jobs
          </CardTitle>
          <CardDescription>Up to 5 jobs we continuously track your readiness for.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {trackedLoading ? (
            <Skeleton className="h-16" />
          ) : !tracked || tracked.length === 0 ? (
            <EmptyState icon={Target} title="No dream jobs yet" description="Click 'I want this job' on any card above to start tracking it." />
          ) : (
            <>
              <div className="flex snap-x gap-2 overflow-x-auto pb-1">
                {tracked.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setSelectedTrackedId(t.match.listing.id)}
                    className={cn(
                      "flex shrink-0 snap-start items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                      (selectedTracked?.match.listing.id ?? tracked[0].match.listing.id) === t.match.listing.id
                        ? "border-brand bg-brand-soft text-brand"
                        : "border-border text-muted hover:text-foreground",
                    )}
                  >
                    {t.match.listing.company}
                    <Badge variant="outline" className="ml-0.5">
                      {formatPercent(t.match.readiness)}
                    </Badge>
                  </button>
                ))}
              </div>
              {selectedTracked && (
                <TrackedJobPanel tracked={selectedTracked} onRemove={() => handleUntrack(selectedTracked.match.listing.id)} />
              )}
            </>
          )}
        </CardContent>
      </Card>

      <ManualJobDescriptionSection />
    </div>
  );
}

export default function JobDescriptionPage() {
  return (
    <Protected>
      <JobMatchBody />
    </Protected>
  );
}
