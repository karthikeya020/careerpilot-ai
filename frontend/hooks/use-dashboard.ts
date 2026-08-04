import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { DashboardOut } from "@/types/api";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardOut>("/dashboard"),
  });
}
