"use client";

import { CheckCircle2, Cpu, XCircle } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAdminDashboard } from "@/hooks/use-role-dashboards";
import { formatDateTime, formatPercent, titleCase } from "@/lib/utils";

function HealthBadge({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-border p-3">
      {ok ? <CheckCircle2 className="h-4 w-4 text-positive" aria-hidden="true" /> : <XCircle className="h-4 w-4 text-danger" aria-hidden="true" />}
      <span className="text-sm text-foreground">{label}</span>
      <Badge variant={ok ? "positive" : "danger"} className="ml-auto">
        {ok ? "healthy" : "unavailable"}
      </Badge>
    </div>
  );
}

function AdminBody() {
  const { data, isLoading, isError, error, refetch } = useAdminDashboard();

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) {
    return <ErrorState message={error instanceof Error ? error.message : "Couldn't load the admin dashboard."} onRetry={() => refetch()} />;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold text-foreground">
          <Cpu className="h-5 w-5 text-brand" aria-hidden="true" />
          Administrator Dashboard
        </h1>
        <p className="mt-1 text-sm text-muted">Service health, user counts, and CARE execution analytics.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <HealthBadge label="Database" ok={data.service_health.database} />
        <HealthBadge label="Redis" ok={data.service_health.redis} />
        <HealthBadge label="Neo4j" ok={data.service_health.neo4j} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Users by role ({data.total_users} total)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {Object.entries(data.users_by_role).map(([role, count]) => (
            <Badge key={role} variant="muted">
              {titleCase(role)}: {count}
            </Badge>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>CARE execution analytics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-4 text-center sm:grid-cols-4">
            <div>
              <p className="text-lg font-semibold text-foreground">{data.care_execution_stats.total_executions}</p>
              <p className="text-[11px] text-muted">Total executions</p>
            </div>
            <div>
              <p className="text-lg font-semibold text-foreground">{formatPercent(data.care_execution_stats.average_confidence)}</p>
              <p className="text-[11px] text-muted">Avg confidence</p>
            </div>
            <div>
              <p className="text-lg font-semibold text-foreground">
                {data.care_execution_stats.average_latency_ms !== null ? `${data.care_execution_stats.average_latency_ms.toFixed(0)}ms` : "—"}
              </p>
              <p className="text-[11px] text-muted">Avg latency</p>
            </div>
            <div>
              <p className="text-lg font-semibold text-foreground">{formatPercent(data.care_execution_stats.human_review_rate)}</p>
              <p className="text-[11px] text-muted">Human-review rate</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.care_execution_stats.route_frequency).map(([route, count]) => (
              <Badge key={route} variant="default">
                {route.replaceAll("_", " ")}: {count}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent audit events (7 days)</CardTitle>
        </CardHeader>
        <CardContent>
          {data.recent_audit_events.length === 0 ? (
            <EmptyState title="No audit events in the last 7 days" />
          ) : (
            <ul className="space-y-1">
              {data.recent_audit_events.map((e) => (
                <li key={e.id} className="flex justify-between text-xs">
                  <span className="text-foreground">{titleCase(e.event_type)}</span>
                  <span className="text-muted">{formatDateTime(e.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function AdminPage() {
  return (
    <Protected>
      <AdminBody />
    </Protected>
  );
}
