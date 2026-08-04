"use client";

import { useState } from "react";
import Link from "next/link";
import { History, ShieldCheck, UserCog } from "lucide-react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuditEvents } from "@/hooks/use-audit";
import { useStudentProfile } from "@/hooks/use-onboarding";
import { useSetRecruiterVisibility } from "@/hooks/use-role-dashboards";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api-client";
import { formatDateTime, titleCase } from "@/lib/utils";

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
        <CardTitle>Recruiter visibility</CardTitle>
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

function SettingsBody() {
  const { user } = useAuth();
  const { data: profile, isLoading, isError, error, refetch } = useStudentProfile();
  const { data: auditEvents } = useAuditEvents(15);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Profile &amp; settings</h1>
        <p className="mt-1 text-sm text-muted">Your account and Career Twin profile details.</p>
      </div>

      <Card>
        <CardHeader className="flex-row items-center gap-2">
          <UserCog className="h-4 w-4 text-brand" aria-hidden="true" />
          <CardTitle>Account</CardTitle>
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
        <Card>
          <CardHeader>
            <CardTitle>Career profile</CardTitle>
            <CardDescription>Update your target role or goal by redoing onboarding.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted">Full name</span>
              <span className="text-foreground">{profile.full_name}</span>
            </div>
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

      <Card>
        <CardHeader className="flex-row items-center gap-2">
          <History className="h-4 w-4 text-brand" aria-hidden="true" />
          <CardTitle>Audit trail</CardTitle>
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
