import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  ActivityDayDetailOut,
  ActivityDayOut,
  AssessmentAnalyticsOut,
  AssessmentAttemptOut,
  AssessmentDomainOut,
  AttemptProgressOut,
  DailyGoalOut,
  LeetCodeRecommendationsOut,
} from "@/types/api";

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
      queryClient.invalidateQueries({ queryKey: ["assessment-activity"] });
      queryClient.invalidateQueries({ queryKey: ["assessment-analytics"] });
      queryClient.invalidateQueries({ queryKey: ["assessment-leetcode-recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["assessment-daily-goal"] });
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

export function useActivityCalendar(year: number) {
  return useQuery({
    queryKey: ["assessment-activity", year],
    queryFn: () => api.get<ActivityDayOut[]>(`/assessments/activity-calendar?year=${year}`),
  });
}

export function useActivityDay(date: string | null) {
  return useQuery({
    queryKey: ["assessment-activity-day", date],
    queryFn: () => api.get<ActivityDayDetailOut[]>(`/assessments/activity-calendar/${date}`),
    enabled: !!date,
  });
}

export function useAssessmentAnalytics() {
  return useQuery({
    queryKey: ["assessment-analytics"],
    queryFn: () => api.get<AssessmentAnalyticsOut>("/assessments/analytics"),
  });
}

export function useLeetCodeRecommendations() {
  return useQuery({
    queryKey: ["assessment-leetcode-recommendations"],
    queryFn: () => api.get<LeetCodeRecommendationsOut>("/assessments/leetcode-recommendations"),
  });
}

export function useDailyGoal() {
  return useQuery({
    queryKey: ["assessment-daily-goal"],
    queryFn: () => api.get<DailyGoalOut>("/assessments/daily-goal"),
  });
}

export function useSetDailyGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (goal: string) => api.put<DailyGoalOut>("/assessments/daily-goal", { goal }),
    onSuccess: (data) => {
      queryClient.setQueryData(["assessment-daily-goal"], data);
      queryClient.invalidateQueries({ queryKey: ["student-profile"] });
    },
  });
}
