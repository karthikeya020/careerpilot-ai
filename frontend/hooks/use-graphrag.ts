import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  ConceptInsightOut,
  GraphSnapshotOut,
  PracticeProgressOut,
  RootCauseResultOut,
  StudentGraphOverviewOut,
} from "@/types/api";

export function useGraphHealth() {
  return useQuery({
    queryKey: ["graphrag", "health"],
    queryFn: () => api.get<{ available: boolean }>("/graph/health"),
    staleTime: 60_000,
  });
}

export function useRootCause(questionId: string | null) {
  return useQuery({
    queryKey: ["graphrag", "root-cause", questionId],
    queryFn: () => api.get<RootCauseResultOut>(`/graph/root-cause/${questionId}`),
    enabled: !!questionId,
    retry: 1,
  });
}

export function useConceptNeighborhood(slug: string | null) {
  return useQuery({
    queryKey: ["graphrag", "concept-neighborhood", slug],
    queryFn: () => api.get<GraphSnapshotOut>(`/graph/concept/${slug}/neighborhood`),
    enabled: !!slug,
    retry: 1,
  });
}

export function useStudentGraphOverview() {
  return useQuery({
    queryKey: ["graphrag", "student-overview"],
    queryFn: () => api.get<StudentGraphOverviewOut>("/graph/student-overview"),
  });
}

export function useConceptInsight(slug: string | null) {
  return useQuery({
    queryKey: ["graphrag", "concept-insight", slug],
    queryFn: () => api.get<ConceptInsightOut>(`/graph/concept/${slug}/insight`),
    enabled: !!slug,
    retry: 1,
  });
}

export function useStartConceptPractice() {
  return useMutation({
    mutationFn: (conceptSlug: string) => api.post<PracticeProgressOut>(`/graph/practice/${conceptSlug}/start`, {}),
  });
}

export function useAnswerConceptPractice() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      conceptSlug,
      attemptId,
      questionId,
      responsePayload,
      timeSpentSeconds,
    }: {
      conceptSlug: string;
      attemptId: string;
      questionId: string;
      responsePayload: Record<string, unknown>;
      timeSpentSeconds?: number;
    }) =>
      api.post<PracticeProgressOut>(`/graph/practice/${conceptSlug}/attempts/${attemptId}/answer`, {
        question_id: questionId,
        response_payload: responsePayload,
        time_spent_seconds: timeSpentSeconds,
      }),
    onSuccess: (data) => {
      if (data.is_complete) {
        queryClient.invalidateQueries({ queryKey: ["graphrag", "student-overview"] });
        queryClient.invalidateQueries({ queryKey: ["graphrag", "concept-insight"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
        queryClient.invalidateQueries({ queryKey: ["career-twin"] });
        queryClient.invalidateQueries({ queryKey: ["trust-center"] });
      }
    },
  });
}
