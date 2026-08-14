"use client";

import { PartyPopper } from "lucide-react";

export function MilestoneBanner({ milestones }: { milestones: string[] }) {
  if (milestones.length === 0) return null;

  return (
    <div className="animate-fade-up flex flex-col gap-2 rounded-[var(--radius-lg)] border border-positive/30 bg-positive/10 p-4 sm:flex-row sm:items-center sm:gap-3">
      <PartyPopper className="h-5 w-5 shrink-0 text-positive" aria-hidden="true" />
      <div className="space-y-1">
        {milestones.map((m, i) => (
          <p key={i} className="text-sm font-medium text-foreground">
            {m}
          </p>
        ))}
      </div>
    </div>
  );
}
