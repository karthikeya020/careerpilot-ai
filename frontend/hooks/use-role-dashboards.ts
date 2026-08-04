import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { AdminDashboardOut, FacultyDashboardOut, PlacementDashboardOut, RecruiterCandidateOut } from "@/types/api";

export function useFacultyDashboard() {
  return useQuery({
    queryKey: ["faculty-dashboard"],
    queryFn: () => api.get<FacultyDashboardOut>("/faculty/dashboard"),
  });
}

export function usePlacementDashboard() {
  return useQuery({
    queryKey: ["placement-dashboard"],
    queryFn: () => api.get<PlacementDashboardOut>("/placement/dashboard"),
  });
}

export function useRecruiterCandidates() {
  return useQuery({
    queryKey: ["recruiter-candidates"],
    queryFn: () => api.get<RecruiterCandidateOut[]>("/recruiter/candidates"),
  });
}

export function useAdminDashboard() {
  return useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: () => api.get<AdminDashboardOut>("/admin/dashboard"),
  });
}

export function useSetRecruiterVisibility() {
  return useMutation({
    mutationFn: (visible: boolean) => api.put<void>("/students/me/recruiter-visibility", { visible }),
  });
}
