"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronDown, FileText, PlayCircle, Search, Sparkles, Target } from "lucide-react";
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
import { ClickSpark, CountUp, JobFxStyles, Magnetic } from "@/components/ui/fx";
import { PageHeader } from "@/components/ui/page-header";
import { Reveal } from "@/components/ui/reveal";
import { SectionHeader } from "@/components/ui/section";
import { JobCard, JobCardSkeleton } from "@/components/jobs/job-card";
import { JobReelRail } from "@/components/jobs/job-reel-rail";
import { JobSearchBar, type JobSearchState } from "@/components/jobs/job-search-bar";
import { LiveJobCard, LiveJobCardSkeleton } from "@/components/jobs/live-job-card";
import { TrackedJobPanel } from "@/components/jobs/tracked-job-panel";
import { liveFiltersActive, useLiveJobSearch } from "@/hooks/use-live-jobs";
import { useRecommendedJobs, useTrackJob, useTrackedJobs, useUntrackJob } from "@/hooks/use-job-catalog";
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
    <div className="space-y-4">
      <SectionHeader title={title} description={description} />
      <div className="edge-fade-x -mx-1 flex snap-x snap-mandatory gap-4 overflow-x-auto px-1 pb-3">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <JobCardSkeleton key={i} />)
        ) : matches && matches.length > 0 ? (
          matches.map((m) => (
            <JobCard
              key={m.listing.id}
              match={m}
              onTrack={onTrack}
              onUntrack={onUntrack}
              isPending={pendingId === m.listing.id}
            />
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

const EMPTY_QUERY: JobSearchState = {
  raw: "",
  q: "",
  sector: "",
  location: "",
  remote: false,
  skills: [],
  minPackage: 0,
};

function JobMatchBody() {
  const { data: recommended, isLoading: recommendedLoading } = useRecommendedJobs();
  const [query, setQuery] = useState<JobSearchState>(EMPTY_QUERY);
  const searching = liveFiltersActive(query);
  const { data: liveResults, isLoading: liveLoading, isError: liveError } = useLiveJobSearch(query);
  const { data: tracked, isLoading: trackedLoading } = useTrackedJobs();
  const [selectedTrackedId, setSelectedTrackedId] = useState<string | null>(null);

  const trackJob = useTrackJob();
  const untrackJob = useUntrackJob();
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [reelsOpen, setReelsOpen] = useState(false);

  const openReel = () => {
    setReelsOpen(true);
    window.dispatchEvent(new CustomEvent("careerpilot:reel", { detail: true }));
  };
  const closeReel = () => {
    setReelsOpen(false);
    window.dispatchEvent(new CustomEvent("careerpilot:reel", { detail: false }));
  };

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
    <div className="mx-auto max-w-6xl space-y-10">
      <JobFxStyles />

      <Reveal>
        <PageHeader
          icon={Target}
          eyebrow="Careers"
          title="Job Match"
          description="Every role is scored against your actual resume evidence — no typing required. Track up to 5 dream jobs and see exactly how ready you are and what closes the gap."
          actions={
            <Magnetic>
              <ClickSpark>
                <Button onClick={openReel} size="sm" className="ds-press bg-gradient-brand">
                  <PlayCircle className="h-4 w-4" aria-hidden="true" /> Scroll Jobs
                </Button>
              </ClickSpark>
            </Magnetic>
          }
        />
      </Reveal>

      {reelsOpen && <JobReelRail onClose={closeReel} />}

      <Reveal delay={60}>
        <JobSearchBar onSearch={setQuery} />
      </Reveal>

      {searching ? (
        <Reveal className="space-y-4">
          <SectionHeader
            eyebrow="Live from company boards"
            title={
              <span className="inline-flex flex-wrap items-baseline gap-1.5">
                <Search className="h-4 w-4 self-center text-brand" aria-hidden="true" />
                {liveResults ? (
                  <>
                    <CountUp value={liveResults.total} className="tabular-nums" /> live opening
                    {liveResults.total === 1 ? "" : "s"}
                  </>
                ) : (
                  "Searching…"
                )}
                {query.raw && (
                  <span className="text-sm font-normal text-muted">for &ldquo;{query.raw}&rdquo;</span>
                )}
              </span>
            }
          />
          {liveLoading ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <LiveJobCardSkeleton key={i} />
              ))}
            </div>
          ) : liveError ? (
            <ErrorState message="Couldn't reach the live job feed. Try again in a bit." />
          ) : !liveResults || liveResults.jobs.length === 0 ? (
            <EmptyState
              icon={Search}
              title="No live openings match"
              description="Loosen a filter or try a broader term — the feed only carries roles currently open on company boards."
            />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {liveResults.jobs.map((job, i) => (
                <div
                  key={job.id}
                  className="animate-fade-up"
                  style={{ animationDelay: `${Math.min(i, 8) * 55}ms` }}
                >
                  <LiveJobCard job={job} />
                </div>
              ))}
            </div>
          )}
        </Reveal>
      ) : (
        <>
          <Reveal delay={90}>
            <JobRow
              title="Recommended for you"
              description="Ranked by how well your resume already matches, across every sector."
              matches={recommended}
              isLoading={recommendedLoading}
              onTrack={handleTrack}
              onUntrack={handleUntrack}
              pendingId={pendingId}
            />
          </Reveal>

          <Reveal delay={60}>
            <section className="space-y-4">
              <SectionHeader
                eyebrow="Tracked"
                title={
                  <span className="inline-flex items-center gap-1.5">
                    <Sparkles className="h-4 w-4 text-brand" aria-hidden="true" /> My Dream Jobs
                  </span>
                }
                description="Up to 5 jobs we continuously track your readiness for."
              />
              {trackedLoading ? (
                <Skeleton className="h-16" />
              ) : !tracked || tracked.length === 0 ? (
                <EmptyState
                  icon={Target}
                  title="No dream jobs yet"
                  description="Click 'I want this job' on any card above to start tracking it."
                />
              ) : (
                <div className="space-y-4">
                  <div className="edge-fade-x -mx-1 flex snap-x gap-2 overflow-x-auto px-1 pb-1">
                    {tracked.map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setSelectedTrackedId(t.match.listing.id)}
                        className={cn(
                          "ds-press flex shrink-0 snap-start items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                          (selectedTracked?.match.listing.id ?? tracked[0].match.listing.id) === t.match.listing.id
                            ? "border-brand bg-brand-soft text-brand"
                            : "border-border text-muted hover:border-brand/40 hover:text-foreground",
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
                    <TrackedJobPanel
                      tracked={selectedTracked}
                      onRemove={() => handleUntrack(selectedTracked.match.listing.id)}
                    />
                  )}
                </div>
              )}
            </section>
          </Reveal>

          <Reveal delay={60}>
            <ManualJobDescriptionSection />
          </Reveal>
        </>
      )}
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
