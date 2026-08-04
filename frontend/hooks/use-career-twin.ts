import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";
import type { CareerTwinSnapshotOut } from "@/types/api";

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
