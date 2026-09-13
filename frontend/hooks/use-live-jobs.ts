import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  JobRoadmapOut,
  LiveJobFeedOut,
  LiveJobOut,
  LiveJobSearchOut,
  SkillMatchOut,
  TrackedJobOut,
} from "@/types/api";

export interface LiveJobFilters {
  q?: string;
  sector?: string;
  location?: string;
  remote?: boolean;
  skills?: string[];
  minPackage?: number;
  kind?: "all" | "jobs" | "internships";
}

export function liveFiltersActive(f: LiveJobFilters): boolean {
  return Boolean(
    f.q?.trim() ||
      f.sector ||
      f.location?.trim() ||
      f.remote ||
      (f.skills && f.skills.length > 0) ||
      f.minPackage ||
      (f.kind && f.kind !== "all"),
  );
}

export function useLiveJobSearch(filters: LiveJobFilters) {
  const params = new URLSearchParams();
  if (filters.q?.trim()) params.set("q", filters.q.trim());
  if (filters.sector) params.set("sector", filters.sector);
  if (filters.location?.trim()) params.set("location", filters.location.trim());
  if (filters.remote) params.set("remote", "true");
  if (filters.skills?.length) params.set("skills", filters.skills.join(","));
  if (filters.minPackage) params.set("min_package", String(filters.minPackage));
  if (filters.kind && filters.kind !== "all") params.set("kind", filters.kind);
  const qs = params.toString();
  return useQuery({
    queryKey: ["job-catalog", "live-search", qs],
    queryFn: () => api.get<LiveJobSearchOut>(`/job-catalog/live/search${qs ? `?${qs}` : ""}`),
    enabled: liveFiltersActive(filters),
  });
}

export function useTrackLiveJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post<TrackedJobOut>("/job-catalog/live/track", { id }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["job-catalog"] }),
  });
}

const PAGE_SIZE = 6;

export type LiveFeedKind = "jobs" | "internships";

export function useLiveJobFeed(kind: LiveFeedKind = "jobs") {
  return useInfiniteQuery({
    queryKey: ["job-catalog", "live-feed", kind],
    queryFn: ({ pageParam }) =>
      api.get<LiveJobFeedOut>(`/job-catalog/live?cursor=${pageParam}&limit=${PAGE_SIZE}&kind=${kind}`),
    initialPageParam: 0,
    // The backend wraps the cursor, so there is always a next page -- endless.
    getNextPageParam: (last) => last.next_cursor,
    staleTime: 5 * 60_000,
  });
}

export function useSkillMatch(skills: string[]) {
  const key = [...skills].sort().join(",");
  return useQuery({
    queryKey: ["job-catalog", "skill-match", key],
    queryFn: () => api.get<SkillMatchOut>(`/job-catalog/skill-match?skills=${encodeURIComponent(key)}`),
    enabled: skills.length > 0,
    staleTime: 5 * 60_000,
  });
}

export function useLiveJobDetail(id: string | null) {
  return useQuery({
    queryKey: ["job-catalog", "live-detail", id],
    queryFn: () => api.get<LiveJobOut>(`/job-catalog/live-detail?id=${encodeURIComponent(id ?? "")}`),
    enabled: !!id,
  });
}

interface RoadmapArgs {
  listingId?: string | null;
  company?: string;
  title?: string;
  sector?: string;
  seniority?: string | null;
  skills?: string[];
}

export function useJobRoadmap(args: RoadmapArgs, enabled = true) {
  const { listingId, company, title, sector, seniority, skills } = args;
  return useQuery({
    queryKey: ["job-catalog", "roadmap", listingId ?? `${company}|${title}`],
    queryFn: () => {
      if (listingId) return api.get<JobRoadmapOut>(`/job-catalog/${listingId}/roadmap`);
      const params = new URLSearchParams({
        company: company ?? "",
        title: title ?? "",
        sector: sector ?? "startup",
        skills: (skills ?? []).join(","),
      });
      if (seniority) params.set("seniority", seniority);
      return api.get<JobRoadmapOut>(`/job-catalog/roadmap?${params.toString()}`);
    },
    enabled: enabled && (!!listingId || (!!company && !!title)),
    staleTime: 10 * 60_000,
  });
}
