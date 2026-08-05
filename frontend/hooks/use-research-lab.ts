import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  AblationSuiteOut,
  CalibrationReportOut,
  EvaluationRunSummaryOut,
  GraphVsVectorExperimentOut,
  RoutingExperimentOut,
} from "@/types/api";

export function useEvaluationRuns() {
  return useQuery({
    queryKey: ["research-runs"],
    queryFn: () => api.get<EvaluationRunSummaryOut[]>("/research/runs"),
  });
}

export function useCalibration() {
  return useQuery({
    queryKey: ["research-calibration"],
    queryFn: () => api.get<CalibrationReportOut>("/research/calibration"),
  });
}

export function useRunRoutingExperiment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<RoutingExperimentOut>("/research/experiments/routing"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["research-runs"] });
      queryClient.invalidateQueries({ queryKey: ["research-calibration"] });
    },
  });
}

export function useRunGraphVsVectorExperiment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<GraphVsVectorExperimentOut>("/research/experiments/graph-vs-vector"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["research-runs"] });
      queryClient.invalidateQueries({ queryKey: ["research-calibration"] });
    },
  });
}

export function useRunAblationSuite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<AblationSuiteOut>("/research/experiments/ablations"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["research-runs"] });
      queryClient.invalidateQueries({ queryKey: ["research-calibration"] });
    },
  });
}
