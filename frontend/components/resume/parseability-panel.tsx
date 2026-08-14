"use client";

import { AlertTriangle, ScanEye } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ParseabilityOut } from "@/types/api";

function gaugeColor(score: number) {
  if (score >= 0.75) return "var(--color-positive)";
  if (score >= 0.5) return "var(--color-warning)";
  return "var(--color-danger)";
}

export function ParseabilityPanel({ parseability }: { parseability: ParseabilityOut }) {
  const pct = Math.round(parseability.score * 100);
  const circumference = 2 * Math.PI * 26;
  const offset = circumference * (1 - parseability.score);

  return (
    <Card className="animate-fade-up delay-3">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-brand-soft">
          <ScanEye className="h-4 w-4 text-brand" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">Parseability -- the real ATS check</CardTitle>
          <CardDescription>
            If our parser struggles to read this file cleanly, an automated recruiter filter almost certainly does
            too.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-start">
        <div className="relative flex h-16 w-16 shrink-0 items-center justify-center">
          <svg width="64" height="64" className="-rotate-90">
            <circle cx="32" cy="32" r="26" fill="none" stroke="var(--color-surface-muted)" strokeWidth="6" />
            <circle
              cx="32" cy="32" r="26" fill="none" stroke={gaugeColor(parseability.score)} strokeWidth="6"
              strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset}
              style={{ transition: "stroke-dashoffset 600ms ease-out" }}
            />
          </svg>
          <span className="absolute text-sm font-bold tabular-nums text-foreground">{pct}%</span>
        </div>
        <div className="flex-1 space-y-2">
          {parseability.warnings.length === 0 ? (
            <p className="text-sm text-positive">Extracted cleanly -- no layout issues detected.</p>
          ) : (
            parseability.warnings.map((w, i) => (
              <p key={i} className="flex items-start gap-2 text-sm text-foreground">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" aria-hidden="true" /> {w}
              </p>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
