"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useSkillsCatalog, useStudentProfile, useSubmitOnboarding } from "@/hooks/use-onboarding";
import { ApiError } from "@/lib/api-client";
import { onboardingSchema, type OnboardingFormValues } from "@/lib/schemas";

const SENIORITY_OPTIONS = [
  { value: "internship", label: "Internship" },
  { value: "entry_level", label: "Entry level" },
  { value: "mid_level", label: "Mid level" },
  { value: "senior", label: "Senior" },
];

function OnboardingForm() {
  const router = useRouter();
  const { data: profile } = useStudentProfile();
  const { data: skills } = useSkillsCatalog();
  const submitOnboarding = useSubmitOnboarding();

  const {
    register,
    control,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<OnboardingFormValues>({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      full_name: "",
      career_goal_description: "",
      timeline_months: 6,
      target_role_title: "",
      target_role_seniority: "entry_level",
      self_assessed_skills: [{ skill_name: "", rating: 0.5 }],
      consent_data_processing: true,
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: "self_assessed_skills" });

  useEffect(() => {
    if (profile?.full_name) setValue("full_name", profile.full_name);
  }, [profile, setValue]);

  const onSubmit = async (values: OnboardingFormValues) => {
    try {
      await submitOnboarding.mutateAsync({
        ...values,
        self_assessed_skills: values.self_assessed_skills.filter((s) => s.skill_name.trim().length > 0),
      });
      toast.success("Your Career Twin has its first snapshot.");
      router.push("/dashboard");
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Couldn't save onboarding. Try again.";
      toast.error(message);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-foreground">Set up your Career Twin</h1>
        <p className="mt-1 text-sm text-muted">
          This takes about two minutes and creates your first evidence-backed readiness snapshot.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
        <Card>
          <CardHeader>
            <CardTitle>About you</CardTitle>
            <CardDescription>Your name and target role.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="full_name">Full name</Label>
              <Input id="full_name" {...register("full_name")} aria-invalid={!!errors.full_name} />
              {errors.full_name ? (
                <p className="text-xs text-danger" role="alert">
                  {errors.full_name.message}
                </p>
              ) : null}
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="target_role_title">Target role</Label>
                <Input
                  id="target_role_title"
                  placeholder="e.g. Backend Engineering Intern"
                  {...register("target_role_title")}
                  aria-invalid={!!errors.target_role_title}
                />
                {errors.target_role_title ? (
                  <p className="text-xs text-danger" role="alert">
                    {errors.target_role_title.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="target_role_seniority">Seniority</Label>
                <select
                  id="target_role_seniority"
                  className="h-10 w-full rounded-[var(--radius-md)] border border-border bg-surface px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                  {...register("target_role_seniority")}
                >
                  {SENIORITY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Career goal</CardTitle>
            <CardDescription>What are you working toward, and on what timeline?</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="career_goal_description">Goal</Label>
              <Textarea
                id="career_goal_description"
                placeholder="e.g. Land a backend engineering internship within 6 months"
                {...register("career_goal_description")}
                aria-invalid={!!errors.career_goal_description}
              />
              {errors.career_goal_description ? (
                <p className="text-xs text-danger" role="alert">
                  {errors.career_goal_description.message}
                </p>
              ) : null}
            </div>
            <div className="space-y-1.5 sm:w-48">
              <Label htmlFor="timeline_months">Timeline (months)</Label>
              <Input
                id="timeline_months"
                type="number"
                min={1}
                max={120}
                {...register("timeline_months", { valueAsNumber: true })}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Self-assessed skills</CardTitle>
            <CardDescription>
              Rate a few skills yourself (0 = none, 1 = expert). This is one input among several — your resume
              carries more weight once uploaded.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <datalist id="skill-options">
              {skills?.map((skill) => (
                <option key={skill.id} value={skill.name} />
              ))}
            </datalist>
            {fields.map((field, index) => (
              <div key={field.id} className="flex items-end gap-2">
                <div className="flex-1 space-y-1.5">
                  <Label htmlFor={`skill-name-${index}`} className="sr-only">
                    Skill name
                  </Label>
                  <Input
                    id={`skill-name-${index}`}
                    list="skill-options"
                    placeholder="e.g. Python"
                    {...register(`self_assessed_skills.${index}.skill_name` as const)}
                  />
                </div>
                <div className="w-28 space-y-1.5">
                  <Label htmlFor={`skill-rating-${index}`} className="sr-only">
                    Self rating
                  </Label>
                  <Input
                    id={`skill-rating-${index}`}
                    type="number"
                    step={0.1}
                    min={0}
                    max={1}
                    {...register(`self_assessed_skills.${index}.rating` as const, { valueAsNumber: true })}
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label="Remove skill"
                  onClick={() => remove(index)}
                  disabled={fields.length === 1}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => append({ skill_name: "", rating: 0.5 })}
            >
              <Plus className="h-4 w-4" /> Add another skill
            </Button>
          </CardContent>
        </Card>

        <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-border bg-surface-muted p-4">
          <input
            id="consent"
            type="checkbox"
            className="mt-0.5 h-4 w-4 rounded border-border"
            {...register("consent_data_processing")}
          />
          <Label htmlFor="consent" className="text-xs font-normal text-muted">
            I consent to CareerPilot AI storing my resume, self-assessment, and derived evidence to build my
            Career Twin.
          </Label>
        </div>

        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Saving…" : "Generate my Career Twin"}
        </Button>
      </form>
    </div>
  );
}

export default function OnboardingPage() {
  return (
    <Protected>
      <OnboardingForm />
    </Protected>
  );
}
