import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { LearningMissionOut } from "@/types/api";

export function useCompleteMission() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (missionId: string) => api.post<LearningMissionOut>(`/missions/${missionId}/complete`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
