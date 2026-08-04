import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { ResponsibleAIOverviewOut } from "@/types/api";

export function useResponsibleAIOverview() {
  return useQuery({
    queryKey: ["responsible-ai-overview"],
    queryFn: () => api.get<ResponsibleAIOverviewOut>("/responsible-ai/overview"),
  });
}

export function useExportMyData() {
  return useMutation({
    mutationFn: () => api.get<Record<string, unknown>>("/responsible-ai/export"),
  });
}

export function useDeleteInterviewAudio() {
  return useMutation({
    mutationFn: () => api.delete<{ deleted_count: number }>("/responsible-ai/interview-audio"),
  });
}

export function useDeleteAccount() {
  return useMutation({
    mutationFn: (password: string) => api.delete<void>("/responsible-ai/account", { password }),
  });
}
