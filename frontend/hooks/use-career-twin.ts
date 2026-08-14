import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";
import type { CareerTwinSnapshotOut, ComponentProjectionOut, RoleAlignmentOut, SnapshotProofOut } from "@/types/api";

export function useCareerTwin() {
  return useQuery({
    queryKey: ["career-twin"],
    queryFn: () => api.get<CareerTwinSnapshotOut>("/career-twin"),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status === 404) return false;
      return failureCount < 2;
    },
  });
}

export function useCareerTwinHistory() {
  return useQuery({
    queryKey: ["career-twin", "history"],
    queryFn: () => api.get<CareerTwinSnapshotOut[]>("/career-twin/history"),
  });
}

export function useMultiRoleAlignment() {
  return useQuery({
    queryKey: ["career-twin", "multi-role"],
    queryFn: () => api.get<RoleAlignmentOut[]>("/career-twin/multi-role"),
  });
}

export function useTimeToTarget() {
  return useQuery({
    queryKey: ["career-twin", "time-to-target"],
    queryFn: () => api.get<ComponentProjectionOut[]>("/career-twin/time-to-target"),
  });
}

export function useSnapshotProof(snapshotId: string | null) {
  return useQuery({
    queryKey: ["career-twin", "proof", snapshotId],
    queryFn: () => api.get<SnapshotProofOut>(`/career-twin/${snapshotId}/proof`),
    enabled: !!snapshotId,
  });
}
