import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  AblationSuiteOut,
  AdversarialSuiteOut,
  CalibrationReportOut,
  DriftCanaryOut,
  EfficiencyFrontierOut,
  EvaluationRunSummaryOut,
  FairnessProbeOut,
  FallbackFidelityOut,
  GraphVsVectorExperimentOut,
  LiveCriticToggleOut,
  LiveCriticToggleRequest,
  ResearchReportOut,
  RoutingExperimentOut,
  ThresholdTuningOut,
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

export function useRunEfficiencyFrontier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<EfficiencyFrontierOut>("/research/experiments/efficiency-frontier"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["research-runs"] }),
  });
}

export function useRunThresholdTuning() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<ThresholdTuningOut>("/research/experiments/threshold-tuning"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["research-runs"] }),
  });
}

export function useRunAdversarialSuite() {
  return useMutation({
    mutationFn: () => api.post<AdversarialSuiteOut>("/research/experiments/adversarial"),
  });
}

export function useRunFallbackFidelity() {
  return useMutation({
    mutationFn: () => api.post<FallbackFidelityOut>("/research/experiments/fallback-fidelity"),
  });
}

export function useRunFairnessProbe() {
  return useMutation({
    mutationFn: () => api.post<FairnessProbeOut>("/research/experiments/fairness-probe"),
  });
}

export function useRunDriftCanary() {
  return useMutation({
    mutationFn: () => api.post<DriftCanaryOut>("/research/experiments/drift-canary"),
  });
}

export function useRunLiveCriticToggle() {
  return useMutation({
    mutationFn: (input: LiveCriticToggleRequest) => api.post<LiveCriticToggleOut>("/research/experiments/live-critic-toggle", input),
  });
}

export function useResearchReport() {
  return useQuery({
    queryKey: ["research-report"],
    queryFn: () => api.get<ResearchReportOut>("/research/report"),
    enabled: false,
  });
}
