import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { ResourceOut } from "@/types/api";

export function useResources() {
  return useQuery({
    queryKey: ["resources"],
    queryFn: () => api.get<ResourceOut[]>("/resources"),
    staleTime: 5 * 60_000,
  });
}
