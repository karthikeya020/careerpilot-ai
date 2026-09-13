import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { LeetCodeAnalysisOut, LeetCodeCompletionOut } from "@/types/api";

const COMPLETIONS_KEY = ["assessment-leetcode-completions"];

export function useLeetCodeCompletions() {
  return useQuery({
    queryKey: COMPLETIONS_KEY,
    queryFn: () => api.get<LeetCodeCompletionOut[]>("/assessments/leetcode-completions"),
  });
}

export interface MarkCompleteInput {
  slug: string;
  title: string;
  difficulty: string;
  concept_slug?: string | null;
  domain_slug?: string | null;
}

export function useMarkComplete() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: MarkCompleteInput) =>
      api.post<LeetCodeCompletionOut>("/assessments/leetcode-completions", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COMPLETIONS_KEY });
    },
  });
}

export function useUnmarkComplete() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => api.delete<void>(`/assessments/leetcode-completions/${slug}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COMPLETIONS_KEY });
    },
  });
}

export function useLeetCodeAnalysis(slug: string | null) {
  return useQuery({
    queryKey: ["assessment-leetcode-analysis", slug],
    queryFn: () => api.get<LeetCodeAnalysisOut>(`/assessments/leetcode-completions/${slug}/analysis`),
    enabled: !!slug,
  });
}

export function useAnalyzeCode(slug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { code: string; language?: string | null }) =>
      api.post<LeetCodeAnalysisOut>(`/assessments/leetcode-completions/${slug}/analyze`, input),
    onSuccess: (data) => {
      queryClient.setQueryData(["assessment-leetcode-analysis", slug], data);
      queryClient.invalidateQueries({ queryKey: COMPLETIONS_KEY });
    },
  });
}
