import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { JobDescriptionOut, MatchResultOut } from "@/types/api";

export function useJobDescriptions() {
  return useQuery({
    queryKey: ["job-descriptions"],
    queryFn: () => api.get<JobDescriptionOut[]>("/job-descriptions"),
  });
}

export function useJobDescriptionMatch(jobDescriptionId: string | undefined) {
  return useQuery({
    queryKey: ["job-descriptions", jobDescriptionId, "match"],
    queryFn: () => api.get<MatchResultOut>(`/job-descriptions/${jobDescriptionId}/match`),
    enabled: Boolean(jobDescriptionId),
  });
}

interface CreateJobDescriptionInput {
  title: string;
  company?: string;
  raw_text: string;
}

export function useCreateJobDescription() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateJobDescriptionInput) => api.post<JobDescriptionOut>("/job-descriptions", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job-descriptions"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["career-twin"] });
      queryClient.invalidateQueries({ queryKey: ["missions"] });
    },
  });
}
