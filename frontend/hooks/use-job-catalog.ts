import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { JobGapPlanOut, JobListingMatchOut, SectorOut, TrackedJobOut } from "@/types/api";

export function useJobSectors() {
  return useQuery({
    queryKey: ["job-catalog", "sectors"],
    queryFn: () => api.get<SectorOut[]>("/job-catalog/sectors"),
    staleTime: 5 * 60_000,
  });
}

export function useRecommendedJobs() {
  return useQuery({
    queryKey: ["job-catalog", "recommended"],
    queryFn: () => api.get<JobListingMatchOut[]>("/job-catalog/recommended"),
  });
}

interface JobSearchInput {
  sector?: string;
  company?: string;
  packageTier?: string;
}

export function useJobSearch({ sector, company, packageTier }: JobSearchInput) {
  const params = new URLSearchParams();
  if (sector) params.set("sector", sector);
  if (company) params.set("company", company);
  if (packageTier) params.set("package_tier", packageTier);
  const qs = params.toString();

  return useQuery({
    queryKey: ["job-catalog", "search", sector ?? null, company ?? null, packageTier ?? null],
    queryFn: () => api.get<JobListingMatchOut[]>(`/job-catalog/search${qs ? `?${qs}` : ""}`),
  });
}

export function useTrackedJobs() {
  return useQuery({
    queryKey: ["job-catalog", "tracked"],
    queryFn: () => api.get<TrackedJobOut[]>("/job-catalog/tracked"),
  });
}

function invalidateJobQueries(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ["job-catalog"] });
}

export function useTrackJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (listingId: string) => api.post<TrackedJobOut>(`/job-catalog/tracked/${listingId}`, {}),
    onSuccess: () => invalidateJobQueries(queryClient),
  });
}

export function useUntrackJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (listingId: string) => api.delete<void>(`/job-catalog/tracked/${listingId}`),
    onSuccess: () => invalidateJobQueries(queryClient),
  });
}

export function useJobGapPlan(listingId: string | null, weeklyHours: number) {
  return useQuery({
    queryKey: ["job-catalog", "gap-plan", listingId, weeklyHours],
    queryFn: () => api.get<JobGapPlanOut>(`/job-catalog/${listingId}/gap-plan?weekly_hours=${weeklyHours}`),
    enabled: !!listingId,
  });
}
