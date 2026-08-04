import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { AuditEventOut } from "@/types/api";

export function useAuditEvents(limit = 25) {
  return useQuery({
    queryKey: ["audit", limit],
    queryFn: () => api.get<AuditEventOut[]>(`/audit?limit=${limit}`),
  });
}
