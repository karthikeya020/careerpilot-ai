"use client";

import Link from "next/link";
import { Mic, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { JobGapSimulator } from "@/components/jobs/job-gap-simulator";
import { formatPercent } from "@/lib/utils";
import type { TrackedJobOut } from "@/types/api";

export function TrackedJobPanel({ tracked, onRemove }: { tracked: TrackedJobOut; onRemove: () => void }) {
  const { listing } = tracked.match;

  return (
    <Card variant="glow-brand" className="animate-fade-up relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-radial-brand opacity-20" aria-hidden="true" />
      <CardHeader className="relative flex-row items-start justify-between gap-2">
        <div>
          <CardTitle as="h3" className="text-base">
            {listing.company} &mdash; {listing.title}
          </CardTitle>
          <p className="mt-0.5 text-xs text-muted">
            {listing.package_min_lpa}-{listing.package_max_lpa} LPA &middot; Readiness {formatPercent(tracked.match.readiness)}
          </p>
        </div>
        <button
          type="button"
          onClick={onRemove}
          className="rounded-[var(--radius-sm)] p-1 text-muted transition-colors hover:bg-surface-muted hover:text-foreground"
          aria-label={`Stop tracking ${listing.company}`}
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </CardHeader>
      <CardContent className="relative space-y-4">
        <Button asChild size="sm" variant="outline">
          <Link href={`/interview?mode=company_context&company=${encodeURIComponent(listing.company)}`}>
            <Mic className="h-3.5 w-3.5" aria-hidden="true" /> Prepare for this job in Interview Arena
          </Link>
        </Button>

        {listing.emphasis_domains.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] text-muted">Recommended practice topics:</span>
            {listing.emphasis_domains.map((d) => (
              <Badge key={d} variant="muted">
                {d.toUpperCase()}
              </Badge>
            ))}
          </div>
        )}

        <div className="border-t border-border pt-4">
          <JobGapSimulator listingId={listing.id} />
        </div>
      </CardContent>
    </Card>
  );
}
