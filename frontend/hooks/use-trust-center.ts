import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { CareExecutionDetailOut, CareExecutionSummaryOut, TwinChangeExplanationOut } from "@/types/api";

export function useCareExecutions(limit = 20) {
  return useQuery({
    queryKey: ["trust-center", "executions", limit],
    queryFn: () => api.get<CareExecutionSummaryOut[]>(`/trust-center/executions?limit=${limit}`),
  });
}

export function useCareExecutionDetail(executionId: string | null) {
  return useQuery({
    queryKey: ["trust-center", "execution", executionId],
    queryFn: () => api.get<CareExecutionDetailOut>(`/trust-center/executions/${executionId}`),
    enabled: !!executionId,
  });
}

export function useTwinExplanation(snapshotId: string | null) {
  return useQuery({
    queryKey: ["trust-center", "twin-explanation", snapshotId],
    queryFn: () => api.get<TwinChangeExplanationOut>(`/trust-center/twin-explanation/${snapshotId}`),
    enabled: !!snapshotId,
  });
}
