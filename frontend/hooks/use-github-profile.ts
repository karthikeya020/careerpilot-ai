import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { GithubProfileOut } from "@/types/api";

export function useGithubProfile() {
  return useQuery({
    queryKey: ["github-profile"],
    queryFn: () => api.get<GithubProfileOut>("/students/me/github-profile"),
  });
}
