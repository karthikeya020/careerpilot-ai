import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { AssessmentAttemptOut, AssessmentDomainOut, AttemptProgressOut } from "@/types/api";

export function useAssessmentDomains() {
  return useQuery({
    queryKey: ["assessment-domains"],
    queryFn: () => api.get<AssessmentDomainOut[]>("/assessments/domains"),
  });
}

export function useStartAttempt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (domainSlug: string) =>
      api.post<AttemptProgressOut>("/assessments/attempts", { domain_slug: domainSlug }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useSubmitResponse() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      attemptId,
      questionId,
      responsePayload,
      timeSpentSeconds,
    }: {
      attemptId: string;
      questionId: string;
      responsePayload: Record<string, unknown>;
      timeSpentSeconds?: number;
    }) =>
      api.post<AttemptProgressOut>(`/assessments/attempts/${attemptId}/responses`, {
        question_id: questionId,
        response_payload: responsePayload,
        time_spent_seconds: timeSpentSeconds,
      }),
    onSuccess: (data) => {
      if (data.is_complete) {
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
        queryClient.invalidateQueries({ queryKey: ["career-twin"] });
        queryClient.invalidateQueries({ queryKey: ["trust-center"] });
      }
    },
  });
}

export function useAttempt(attemptId: string | null) {
  return useQuery({
    queryKey: ["assessment-attempt", attemptId],
    queryFn: () => api.get<AssessmentAttemptOut>(`/assessments/attempts/${attemptId}`),
    enabled: !!attemptId,
  });
}
