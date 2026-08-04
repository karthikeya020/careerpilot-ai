"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, CheckCircle2, Download, ShieldCheck, Trash2, XCircle } from "lucide-react";
import { toast } from "sonner";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useDeleteAccount,
  useDeleteInterviewAudio,
  useExportMyData,
  useResponsibleAIOverview,
} from "@/hooks/use-responsible-ai";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api-client";

function downloadJson(data: unknown, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function ResponsibleAIBody() {
  const { data: overview, isLoading, isError, error, refetch } = useResponsibleAIOverview();
  const exportData = useExportMyData();
  const deleteAudio = useDeleteInterviewAudio();
  const deleteAccount = useDeleteAccount();
  const { logout } = useAuth();
  const router = useRouter();

  const [confirmingDeletion, setConfirmingDeletion] = useState(false);
  const [password, setPassword] = useState("");

  const handleExport = () => {
    exportData.mutate(undefined, {
      onSuccess: (data) => {
        downloadJson(data, "careerpilot-my-data-export.json");
        toast.success("Your data export has downloaded.");
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't export your data."),
    });
  };

  const handleDeleteAudio = () => {
    deleteAudio.mutate(undefined, {
      onSuccess: (result) => {
        toast.success(`Deleted ${result.deleted_count} stored audio file(s). Transcripts were kept.`);
        refetch();
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't delete interview audio."),
    });
  };

  const handleDeleteAccount = () => {
    deleteAccount.mutate(password, {
      onSuccess: async () => {
        toast.success("Your account and all associated data have been deleted.");
        await logout();
        router.push("/login");
      },
      onError: (err) => toast.error(err instanceof ApiError ? err.message : "Couldn't delete your account."),
    });
  };

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !overview) {
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load the Responsible AI Center."} onRetry={() => refetch()} />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
          <ShieldCheck className="h-5 w-5 text-brand" aria-hidden="true" />
          Responsible AI Center
        </h1>
        <p className="mt-1 text-sm text-muted">
          What CareerPilot evaluates, what it deliberately does not, and full control over your data.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>What this system does and does not evaluate</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-positive">
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" /> Evaluates
            </p>
            <ul className="space-y-1.5 text-xs text-foreground">
              {overview.evaluates.map((item, i) => (
                <li key={i} className="rounded-[var(--radius-md)] bg-surface-muted p-2">
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-danger">
              <XCircle className="h-3.5 w-3.5" aria-hidden="true" /> Never evaluates
            </p>
            <ul className="space-y-1.5 text-xs text-foreground">
              {overview.non_claims.map((item, i) => (
                <li key={i} className="rounded-[var(--radius-md)] bg-surface-muted p-2">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your evidence and confidence status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {Object.entries(overview.evidence_provenance).length === 0 ? (
              <Badge variant="muted">No evidence recorded yet</Badge>
            ) : (
              Object.entries(overview.evidence_provenance).map(([type, count]) => (
                <Badge key={type} variant="default">
                  {type.replaceAll("_", " ")}: {count}
                </Badge>
              ))
            )}
          </div>
          {overview.human_review.pending_count > 0 && (
            <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-warning/40 bg-warning/10 p-3 text-sm text-warning">
              <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
              {overview.human_review.pending_count} decision(s) are flagged for human review due to persistently low confidence.
            </div>
          )}
          <p className="text-xs text-muted">
            Current Career Twin confidence:{" "}
            {overview.current_career_twin_confidence !== null ? `${(overview.current_career_twin_confidence * 100).toFixed(0)}%` : "no snapshot yet"}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Model, policy, and formula versions</CardTitle>
          <CardDescription>Every AI-adjacent output is traceable to an exact versioned formula or prompt.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2 text-xs">
          <Badge variant="muted">CARE policy {overview.versions.care_policy_version}</Badge>
          <Badge variant="muted">Career Twin formula {overview.versions.career_twin_formula_version}</Badge>
          <Badge variant="muted">Simulation engine {overview.versions.simulation_engine_version}</Badge>
          {Object.entries(overview.versions.agent_prompt_versions).map(([agent, version]) => (
            <Badge key={agent} variant="muted">
              {agent} {version}
            </Badge>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your data controls</CardTitle>
          <CardDescription>Export, withdraw audio consent, or permanently delete your account.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-border p-3">
            <div>
              <p className="text-sm font-medium text-foreground">Export all your data</p>
              <p className="text-xs text-muted">Download a full JSON export of everything CareerPilot has stored about you.</p>
            </div>
            <Button variant="outline" size="sm" onClick={handleExport} disabled={exportData.isPending}>
              <Download className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" /> Export
            </Button>
          </div>

          <div className="flex items-center justify-between rounded-[var(--radius-md)] border border-border p-3">
            <div>
              <p className="text-sm font-medium text-foreground">
                Delete interview audio ({overview.stored_interview_audio_count} stored)
              </p>
              <p className="text-xs text-muted">Removes stored audio recordings. Transcripts and evaluations are kept.</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDeleteAudio}
              disabled={deleteAudio.isPending || overview.stored_interview_audio_count === 0}
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" /> Delete audio
            </Button>
          </div>

          <div className="rounded-[var(--radius-md)] border border-danger/40 bg-danger/5 p-3">
            <p className="text-sm font-medium text-danger">Delete my account</p>
            <p className="mb-3 text-xs text-muted">
              Permanently deletes your account and every record tied to it -- resumes, evidence, Career Twin history,
              interviews, and scenarios. This cannot be undone.
            </p>
            {confirmingDeletion ? (
              <div className="flex flex-wrap items-center gap-2">
                <Input
                  type="password"
                  placeholder="Confirm your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  aria-label="Confirm password to delete account"
                  className="h-9 w-56"
                />
                <Button variant="destructive" size="sm" onClick={handleDeleteAccount} disabled={!password || deleteAccount.isPending}>
                  {deleteAccount.isPending ? "Deleting..." : "Confirm permanent deletion"}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setConfirmingDeletion(false)}>
                  Cancel
                </Button>
              </div>
            ) : (
              <Button variant="destructive" size="sm" onClick={() => setConfirmingDeletion(true)}>
                Delete my account
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ResponsibleAIPage() {
  return (
    <Protected>
      <ResponsibleAIBody />
    </Protected>
  );
}
