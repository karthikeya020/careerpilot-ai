"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarDays, Camera, GraduationCap, History, ShieldCheck, UserCog } from "lucide-react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuditEvents } from "@/hooks/use-audit";
import { useSetCameraConsent, useStudentProfile, useUpdateProfileDetails } from "@/hooks/use-onboarding";
import { useSetRecruiterVisibility } from "@/hooks/use-role-dashboards";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api-client";
import { COLLEGE_YEAR_OPTIONS, profileDetailsSchema, type ProfileDetailsFormValues } from "@/lib/schemas";
import { formatDateTime, titleCase } from "@/lib/utils";
import type { StudentProfileOut } from "@/types/api";

function PersonalDetailsCard({ profile }: { profile: StudentProfileOut }) {
  const updateProfile = useUpdateProfileDetails();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileDetailsFormValues>({
    resolver: zodResolver(profileDetailsSchema),
    defaultValues: {
      full_name: profile.full_name,
      date_of_birth: profile.date_of_birth ?? "",
      college_year: (profile.college_year as ProfileDetailsFormValues["college_year"]) ?? "",
      branch: profile.branch ?? "",
      github_username: profile.github_username ?? "",
    },
  });

  useEffect(() => {
    reset({
      full_name: profile.full_name,
      date_of_birth: profile.date_of_birth ?? "",
      college_year: (profile.college_year as ProfileDetailsFormValues["college_year"]) ?? "",
      branch: profile.branch ?? "",
      github_username: profile.github_username ?? "",
    });
  }, [profile, reset]);

  const onSubmit = async (values: ProfileDetailsFormValues) => {
    try {
      await updateProfile.mutateAsync({
        full_name: values.full_name,
        date_of_birth: values.date_of_birth ? values.date_of_birth : null,
        college_year: values.college_year ? values.college_year : null,
        branch: values.branch ? values.branch : null,
        github_username: values.github_username ? values.github_username : null,
      });
      toast.success("Personal details updated.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't update your details.");
    }
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <GraduationCap className="h-4 w-4 text-brand" aria-hidden="true" />
        <CardTitle as="h2">Personal details</CardTitle>
        <CardDescription>Keep your academic profile current — used across your Career Twin.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
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
              <Label htmlFor="date_of_birth">Date of birth</Label>
              <div className="relative">
                <CalendarDays className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" aria-hidden="true" />
                <Input id="date_of_birth" type="date" className="pl-9" {...register("date_of_birth")} />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="college_year">Year of college</Label>
              <select
                id="college_year"
                className="h-10 w-full rounded-[var(--radius-md)] border border-border bg-surface px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
                {...register("college_year")}
              >
                <option value="">Not set</option>
                {COLLEGE_YEAR_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="branch">Branch / major</Label>
            <Input id="branch" placeholder="e.g. Computer Science" {...register("branch")} aria-invalid={!!errors.branch} />
            {errors.branch ? (
              <p className="text-xs text-danger" role="alert">
                {errors.branch.message}
              </p>
            ) : null}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="github_username">GitHub username</Label>
            <Input
              id="github_username"
              placeholder="e.g. octocat"
              {...register("github_username")}
              aria-invalid={!!errors.github_username}
            />
            <p className="text-xs text-muted">Powers the GitHub activity widget on your Career Twin — real public data, no token needed.</p>
            {errors.github_username ? (
              <p className="text-xs text-danger" role="alert">
                {errors.github_username.message}
              </p>
            ) : null}
          </div>

          <Button type="submit" size="sm" disabled={!isDirty || updateProfile.isPending}>
            {updateProfile.isPending ? "Saving…" : "Save details"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function RecruiterVisibilityCard() {
  const [visible, setVisible] = useState(false);
  const setRecruiterVisibility = useSetRecruiterVisibility();

  const handleToggle = () => {
    const next = !visible;
    setRecruiterVisibility.mutate(next, {
      onSuccess: () => {
        setVisible(next);
        toast.success(next ? "Recruiters can now see your evidence summary." : "Recruiter visibility turned off.");
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't update recruiter visibility."),
    });
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <ShieldCheck className="h-4 w-4 text-brand" aria-hidden="true" />
        <CardTitle as="h2">Recruiter visibility</CardTitle>
        <CardDescription>
          When on, authorized recruiters can see your evidence summary (readiness components, confidence). No automatic hiring recommendation is ever computed.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant={visible ? "destructive" : "outline"} size="sm" onClick={handleToggle} disabled={setRecruiterVisibility.isPending}>
          {visible ? "Turn off recruiter visibility" : "Make my evidence visible to recruiters"}
        </Button>
      </CardContent>
    </Card>
  );
}

function CameraConsentCard({ profile }: { profile: StudentProfileOut }) {
  // null = no explicit choice made this visit, so it tracks the saved
  // profile value live; the override takes over once the student toggles it.
  const [override, setOverride] = useState<boolean | null>(null);
  const enabled = override ?? profile.camera_consent;
  const setCameraConsent = useSetCameraConsent();

  const handleToggle = () => {
    const next = !enabled;
    setCameraConsent.mutate(next, {
      onSuccess: () => {
        setOverride(next);
        toast.success(next ? "Camera enabled for Interview Arena." : "Camera disabled for Interview Arena.");
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't update camera consent."),
    });
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2">
        <Camera className="h-4 w-4 text-brand" aria-hidden="true" />
        <CardTitle as="h2">Camera in Interview Arena</CardTitle>
        <CardDescription>
          Optional. Records video for your own self-review, plus an honest &quot;camera on&quot; delivery metric —
          never analyzed for emotion, attention, or confidence. You can also toggle this from the ready room before
          any round.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button variant={enabled ? "destructive" : "outline"} size="sm" onClick={handleToggle} disabled={setCameraConsent.isPending}>
          {enabled ? "Disable camera" : "Enable camera"}
        </Button>
      </CardContent>
    </Card>
  );
}

function SettingsBody() {
  const { user } = useAuth();
  const { data: profile, isLoading, isError, error, refetch } = useStudentProfile();
  const { data: auditEvents } = useAuditEvents(15);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div
        className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border p-8"
        style={{ background: "radial-gradient(circle at 15% 20%, color-mix(in srgb, var(--accent-2) 18%, transparent), transparent 45%), var(--color-background)" }}
      >
        <div className="relative flex items-center gap-3">
          <span
            className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)]"
            style={{ background: "linear-gradient(135deg, var(--accent-2), var(--brand))" }}
          >
            <UserCog className="h-5 w-5 text-white" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Profile &amp; settings</h1>
        </div>
        <p className="relative mt-3 max-w-xl text-sm text-muted">Your account and Career Twin profile details.</p>
      </div>

      <Card>
        <CardHeader className="flex-row items-center gap-2">
          <UserCog className="h-4 w-4 text-brand" aria-hidden="true" />
          <CardTitle as="h2">Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted">Email</span>
            <span className="text-foreground">{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted">Roles</span>
            <span className="flex gap-1">
              {user?.roles.map((role) => (
                <Badge key={role} variant="muted">
                  {titleCase(role)}
                </Badge>
              ))}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted">Member since</span>
            <span className="text-foreground">{formatDateTime(user?.created_at)}</span>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <Skeleton className="h-56" />
      ) : isError ? (
        <ErrorState message={error instanceof Error ? error.message : "Couldn't load profile."} onRetry={() => refetch()} />
      ) : profile ? (
        <PersonalDetailsCard profile={profile} />
      ) : null}

      {profile ? (
        <Card>
          <CardHeader>
            <CardTitle as="h2">Career profile</CardTitle>
            <CardDescription>Update your target role or goal by redoing onboarding.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted">Target role</span>
              <span className="text-foreground">
                {profile.primary_target_role ? profile.primary_target_role.title : "Not set"}
              </span>
            </div>
            {profile.career_goals.map((goal) => (
              <div key={goal.id} className="rounded-[var(--radius-md)] bg-surface-muted p-3 text-xs text-muted">
                {goal.description}
                {goal.timeline_months ? ` — target: ${goal.timeline_months} months` : ""}
              </div>
            ))}
            <Button variant="outline" size="sm" asChild>
              <Link href="/onboarding">Redo onboarding</Link>
            </Button>
          </CardContent>
        </Card>
      ) : null}

      <RecruiterVisibilityCard />

      {profile && <CameraConsentCard profile={profile} />}

      <Card>
        <CardHeader className="flex-row items-center gap-2">
          <History className="h-4 w-4 text-brand" aria-hidden="true" />
          <CardTitle as="h2">Audit trail</CardTitle>
          <CardDescription>Every change to your Career Twin is logged.</CardDescription>
        </CardHeader>
        <CardContent>
          {!auditEvents || auditEvents.length === 0 ? (
            <EmptyState title="No audit events yet" />
          ) : (
            <ul className="space-y-2">
              {auditEvents.map((event) => (
                <li key={event.id} className="flex items-center justify-between border-b border-border pb-2 text-xs last:border-0">
                  <span className="text-foreground">{titleCase(event.event_type)}</span>
                  <span className="text-muted">{formatDateTime(event.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Protected>
      <SettingsBody />
    </Protected>
  );
}
