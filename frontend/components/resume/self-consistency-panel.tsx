"use client";

import { CheckCircle2, ShieldAlert } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { SelfConsistencyFlagOut } from "@/types/api";

export function SelfConsistencyPanel({ flags }: { flags: SelfConsistencyFlagOut[] }) {
  return (
    <Card className="animate-fade-up delay-2">
      <CardHeader className="flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-warning/15">
          <ShieldAlert className="h-4 w-4 text-warning" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">Skills self-check</CardTitle>
          <CardDescription>
            Every skill in your Skills section, cross-checked against your own Experience and Projects bullets.
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {flags.length === 0 ? (
          <p className="flex items-center gap-2 text-sm font-medium text-positive">
            <CheckCircle2 className="h-4 w-4" aria-hidden="true" /> Every listed skill is backed up elsewhere on your
            resume. No keyword-stuffing detected.
          </p>
        ) : (
          <ul className="space-y-2">
            {flags.map((f) => (
              <li key={f.skill_id} className="rounded-[var(--radius-md)] border border-warning/30 bg-warning/5 p-3 text-sm text-foreground">
                {f.message}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
