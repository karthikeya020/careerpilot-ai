import { z } from "zod";

export const registerSchema = z.object({
  fullName: z.string().min(1, "Enter your full name"),
  email: z.string().email("Enter a valid email address"),
  password: z
    .string()
    .min(8, "At least 8 characters")
    .refine((v) => /[a-zA-Z]/.test(v), "Include at least one letter")
    .refine((v) => /[0-9]/.test(v), "Include at least one digit"),
});
export type RegisterFormValues = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Enter your password"),
});
export type LoginFormValues = z.infer<typeof loginSchema>;

export const selfAssessedSkillSchema = z.object({
  skill_name: z.string().min(1),
  rating: z.number().min(0).max(1),
});

export const onboardingSchema = z.object({
  full_name: z.string().min(1, "Enter your full name"),
  career_goal_description: z.string().min(10, "Describe your goal in at least 10 characters"),
  timeline_months: z
    .number({ error: "Enter a number" })
    .min(1)
    .max(120)
    .nullable()
    .optional(),
  target_role_title: z.string().min(1, "Enter a target role"),
  target_role_seniority: z.enum(["internship", "entry_level", "mid_level", "senior"]),
  self_assessed_skills: z.array(selfAssessedSkillSchema),
  consent_data_processing: z.boolean(),
});
export type OnboardingFormValues = z.infer<typeof onboardingSchema>;

export const COLLEGE_YEAR_OPTIONS = [
  { value: "1st_year", label: "1st year" },
  { value: "2nd_year", label: "2nd year" },
  { value: "3rd_year", label: "3rd year" },
  { value: "4th_year", label: "4th year" },
  { value: "5th_year", label: "5th year" },
  { value: "graduated", label: "Graduated" },
] as const;

export const profileDetailsSchema = z.object({
  full_name: z.string().min(1, "Enter your full name"),
  date_of_birth: z.string().optional().or(z.literal("")),
  college_year: z.enum(["1st_year", "2nd_year", "3rd_year", "4th_year", "5th_year", "graduated"]).optional().or(z.literal("")),
  branch: z.string().max(150).optional().or(z.literal("")),
  github_username: z
    .string()
    .max(39)
    .regex(/^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$/, "Enter a valid GitHub username")
    .optional()
    .or(z.literal("")),
});
export type ProfileDetailsFormValues = z.infer<typeof profileDetailsSchema>;

export const jobDescriptionSchema = z.object({
  title: z.string().min(1, "Enter a job title"),
  company: z.string().optional(),
  raw_text: z.string().min(30, "Paste at least a few sentences of the job description"),
});
export type JobDescriptionFormValues = z.infer<typeof jobDescriptionSchema>;
