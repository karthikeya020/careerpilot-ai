"use client";

import { Activity, CheckCircle2, Cpu, Database, Network, Server, XCircle } from "lucide-react";
import { Protected } from "@/components/layout/protected";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useAdminDashboard } from "@/hooks/use-role-dashboards";
import { ApiError } from "@/lib/api-client";
import { cn, formatDateTime, formatPercent, titleCase } from "@/lib/utils";

const SERVICE_ICONS: Record<string, typeof Database> = {
  Database: Database,
  Redis: Server,
  Neo4j: Network,
};

function HealthCard({ label, ok }: { label: string; ok: boolean }) {
  const Icon = SERVICE_ICONS[label] ?? Database;
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-[var(--radius-md)] border p-3",
        ok ? "border-positive/30 bg-positive/5" : "border-danger/30 bg-danger/5",
      )}
    >
      <span className={cn("flex h-9 w-9 items-center justify-center rounded-full", ok ? "bg-positive/15 text-positive" : "bg-danger/15 text-danger")}>
        <Icon className="h-4 w-4" aria-hidden="true" />
      </span>
      <div className="flex-1">
        <p className="text-sm font-medium text-foreground">{label}</p>
        <p className="text-[11px] text-muted">{ok ? "healthy" : "unavailable"}</p>
      </div>
      {ok ? <CheckCircle2 className="h-4 w-4 text-positive" aria-hidden="true" /> : <XCircle className="h-4 w-4 text-danger" aria-hidden="true" />}
    </div>
  );
}

function AdminBody() {
  const { data, isLoading, isError, error, refetch } = useAdminDashboard();

  if (isLoading) return <Skeleton className="h-96" />;
  if (isError || !data) {
    const isPermissionDenied = error instanceof ApiError && error.status === 403;
    return (
      <ErrorState
        message={isPermissionDenied ? "This dashboard is only available to administrator accounts." : error instanceof Error ? error.message : "Couldn't load the admin dashboard."}
        onRetry={isPermissionDenied ? undefined : () => refetch()}
        isPermissionDenied={isPermissionDenied}
        titleAs="h1"
      />
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="animate-fade-up relative overflow-hidden rounded-[var(--radius-xl)] border border-border bg-mesh p-8 md:p-10">
        <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
        <div className="relative flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
            <Cpu className="h-5 w-5 text-brand-foreground" aria-hidden="true" />
          </span>
          <h1 className="text-h1 text-foreground">Administrator Dashboard</h1>
        </div>
        <p className="relative mt-3 max-w-2xl text-sm text-muted">Service health, user counts, and CARE execution analytics.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <HealthCard label="Database" ok={data.service_health.database} />
        <HealthCard label="Redis" ok={data.service_health.redis} />
        <HealthCard label="Neo4j" ok={data.service_health.neo4j} />
      </div>

      <Card className="animate-fade-up delay-1">
        <CardHeader>
          <CardTitle as="h2">Users by role ({data.total_users} total)</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {Object.entries(data.users_by_role).map(([role, count]) => (
            <Badge key={role} variant="muted">
              {titleCase(role)}: {count}
            </Badge>
          ))}
        </CardContent>
      </Card>

      <Card className="animate-fade-up delay-2">
        <CardHeader>
          <CardTitle as="h2" className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-brand" aria-hidden="true" /> CARE execution analytics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-center sm:grid-cols-4">
            <div>
              <p className="text-metric text-foreground">{data.care_execution_stats.total_executions}</p>
              <p className="text-[11px] text-muted">Total executions</p>
            </div>
            <div>
              <p className="text-metric text-foreground">{formatPercent(data.care_execution_stats.average_confidence)}</p>
              <p className="text-[11px] text-muted">Avg confidence</p>
            </div>
            <div>
              <p className="text-metric text-foreground">
                {data.care_execution_stats.average_latency_ms !== null ? `${data.care_execution_stats.average_latency_ms.toFixed(0)}ms` : "—"}
              </p>
              <p className="text-[11px] text-muted">Avg latency</p>
            </div>
            <div>
              <p className="text-metric text-foreground">{formatPercent(data.care_execution_stats.human_review_rate)}</p>
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

      <Card className="animate-fade-up delay-3">
        <CardHeader>
          <CardTitle as="h2">Recent audit events (7 days)</CardTitle>
        </CardHeader>
        <CardContent>
          {data.recent_audit_events.length === 0 ? (
            <EmptyState title="No audit events in the last 7 days" />
          ) : (
            <ul className="space-y-1">
              {data.recent_audit_events.map((e) => (
                <li key={e.id} className="flex justify-between rounded-[var(--radius-sm)] px-2 py-1 text-xs hover:bg-surface-muted">
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
