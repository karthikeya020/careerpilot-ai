import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";
import type { ResumeOut, ResumeSummaryOut } from "@/types/api";

function invalidateProfileDependents(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ["resume"] });
  queryClient.invalidateQueries({ queryKey: ["resume-history"] });
  queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  queryClient.invalidateQueries({ queryKey: ["career-twin"] });
  queryClient.invalidateQueries({ queryKey: ["missions"] });
  queryClient.invalidateQueries({ queryKey: ["job-descriptions"] });
}

export function useResume() {
  return useQuery({
    queryKey: ["resume"],
    queryFn: () => api.get<ResumeOut>("/resumes/me"),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) return false;
      return failureCount < 2;
    },
  });
}

export function useResumeHistory() {
  return useQuery({
    queryKey: ["resume-history"],
    queryFn: () => api.get<ResumeSummaryOut[]>("/resumes"),
  });
}

export function useUploadResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.post<ResumeOut>("/resumes", formData, { isFormData: true });
    },
    onSuccess: () => invalidateProfileDependents(queryClient),
  });
}

export function useActivateResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (resumeId: string) => api.post<ResumeOut>(`/resumes/${resumeId}/activate`),
    onSuccess: () => invalidateProfileDependents(queryClient),
  });
}
