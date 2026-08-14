import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  AllocationRequest,
  ExperimentScenarioOut,
  PredictionAccuracyOut,
  TargetPlanOut,
  TargetPlanRequest,
} from "@/types/api";

export function useActivityTypes() {
  return useQuery({
    queryKey: ["experiment-activity-types"],
    queryFn: () => api.get<string[]>("/experiments/activity-types"),
  });
}

export function useExperimentScenarios() {
  return useQuery({
    queryKey: ["experiment-scenarios"],
    queryFn: () => api.get<ExperimentScenarioOut[]>("/experiments/scenarios"),
  });
}

interface RunScenarioInput {
  name: string;
  allocations: AllocationRequest[];
  target_role_id?: string | null;
  time_horizon_days?: number;
}

export function useRunScenario() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: RunScenarioInput) => api.post<ExperimentScenarioOut>("/experiments/scenarios", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["experiment-scenarios"] });
    },
  });
}

export function useCompareScenarios(scenarioIds: string[]) {
  return useQuery({
    queryKey: ["experiment-compare", scenarioIds],
    queryFn: () => {
      const params = new URLSearchParams();
      scenarioIds.forEach((id) => params.append("scenario_ids", id));
      return api.get<ExperimentScenarioOut[]>(`/experiments/compare?${params.toString()}`);
    },
    enabled: scenarioIds.length > 0,
  });
}

export function usePlanTarget() {
  return useMutation({
    mutationFn: (input: TargetPlanRequest) => api.post<TargetPlanOut>("/experiments/target-plan", input),
  });
}

export function usePredictionAccuracy(scenarioId: string | null) {
  return useQuery({
    queryKey: ["experiment-prediction-accuracy", scenarioId],
    queryFn: () => api.get<PredictionAccuracyOut>(`/experiments/scenarios/${scenarioId}/prediction-accuracy`),
    enabled: !!scenarioId,
  });
}
