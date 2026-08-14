import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { SkillOut, StudentProfileOut } from "@/types/api";

export function useStudentProfile() {
  return useQuery({
    queryKey: ["student-profile"],
    queryFn: () => api.get<StudentProfileOut>("/students/me"),
  });
}

export function useSkillsCatalog() {
  return useQuery({
    queryKey: ["skills"],
    queryFn: () => api.get<SkillOut[]>("/skills"),
    staleTime: 5 * 60_000,
  });
}

export interface OnboardingInput {
  full_name: string;
  career_goal_description: string;
  timeline_months?: number | null;
  target_role_title: string;
  target_role_seniority: string;
  self_assessed_skills: { skill_name: string; rating: number }[];
  consent_data_processing: boolean;
}

export function useSubmitOnboarding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: OnboardingInput) => api.post<StudentProfileOut>("/onboarding", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-profile"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["career-twin"] });
      queryClient.invalidateQueries({ queryKey: ["missions"] });
    },
  });
}

export interface ProfileDetailsInput {
  full_name?: string;
  date_of_birth?: string | null;
  college_year?: string | null;
  branch?: string | null;
  github_username?: string | null;
}

export function useUpdateProfileDetails() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ProfileDetailsInput) => api.patch<StudentProfileOut>("/students/me", input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-profile"] });
    },
  });
}

export function useSetCameraConsent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (enabled: boolean) => api.put<void>("/students/me/camera-consent", { enabled }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student-profile"] });
    },
  });
}
