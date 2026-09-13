import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { LeetCodeProfileOut } from "@/types/api";

export function useLeetCodeProfile() {
  return useQuery({
    queryKey: ["leetcode-profile"],
    queryFn: () => api.get<LeetCodeProfileOut>("/students/me/leetcode-profile"),
  });
}
