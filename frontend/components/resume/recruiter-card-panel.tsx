"use client";

import Link from "next/link";
import { AlertCircle, CheckCircle2, Eye, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Progress } from "@/components/ui/progress";
import type { RecruiterCardOut } from "@/types/api";

function trustLabel(score: number) {
  if (score >= 0.75) return { label: "Evidence-strong", tone: "text-positive" };
  if (score >= 0.5) return { label: "Evidence-developing", tone: "text-warning" };
  return { label: "Evidence-thin", tone: "text-danger" };
}

export function RecruiterCardPanel({ card }: { card: RecruiterCardOut }) {
  return (
    <Card variant="glow-brand" className="animate-fade-up delay-1 relative overflow-hidden">
      <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-gradient-radial-brand blur-3xl opacity-70" aria-hidden="true" />
      <CardHeader className="relative flex-row items-center gap-2">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand shadow-[var(--shadow-glow-brand)]">
          <Eye className="h-4 w-4 text-brand-foreground" aria-hidden="true" />
        </span>
        <div>
          <CardTitle as="h2">What a recruiter would see</CardTitle>
          <CardDescription>A one-page, evidence-scored preview of your resume&apos;s first impression.</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="relative space-y-4">
        {!card.has_resume || card.trust_score === null ? (
          <EmptyState
            icon={ShieldCheck}
            title="Upload a resume to preview this"
            description="This card fills in the moment your resume finishes parsing."
          />
        ) : (
          <>
            <div className="flex items-center gap-4">
              <div className="relative flex h-20 w-20 shrink-0 items-center justify-center">
                <svg width="80" height="80" className="-rotate-90">
                  <circle cx="40" cy="40" r="34" fill="none" stroke="var(--color-surface-muted)" strokeWidth="7" />
                  <circle
                    cx="40" cy="40" r="34" fill="none" stroke="var(--color-brand)" strokeWidth="7" strokeLinecap="round"
                    strokeDasharray={2 * Math.PI * 34}
                    strokeDashoffset={2 * Math.PI * 34 * (1 - card.trust_score)}
                    style={{ transition: "stroke-dashoffset 700ms ease-out" }}
                  />
                </svg>
                <span className="absolute text-lg font-bold tabular-nums text-foreground">
                  {Math.round(card.trust_score * 100)}
                </span>
              </div>
              <div>
                <p className={`text-sm font-semibold ${trustLabel(card.trust_score).tone}`}>
                  {trustLabel(card.trust_score).label}
                </p>
                <p className="text-xs text-muted">Evidence-completeness score -- not a hiring likelihood.</p>
              </div>
            </div>

            <div>
              <div className="mb-1 flex items-center justify-between text-xs text-muted">
                <span>Skills with traceable evidence</span>
                <span className="font-medium text-foreground">
                  {card.verified_skill_count}/{card.total_skill_count}
                </span>
              </div>
              <Progress
                value={card.total_skill_count > 0 ? (card.verified_skill_count / card.total_skill_count) * 100 : 0}
              />
            </div>

            {card.strengths.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">First-glance strengths</p>
                {card.strengths.map((s, i) => (
                  <p key={i} className="flex items-start gap-2 text-sm text-foreground">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-positive" aria-hidden="true" /> {s}
                  </p>
                ))}
              </div>
            )}

            {card.concerns.length > 0 && (
              <div className="space-y-1.5">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">What would give a recruiter pause</p>
                {card.concerns.slice(0, 4).map((c, i) => (
                  <p key={i} className="flex items-start gap-2 text-sm text-foreground">
                    <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warning" aria-hidden="true" /> {c}
                  </p>
                ))}
              </div>
            )}

            <Link
              href="/settings"
              className="inline-flex w-fit items-center gap-1 rounded-full border border-border-strong px-2.5 py-1 text-xs font-medium text-foreground transition-colors hover:bg-surface-muted"
            >
              Control recruiter visibility in Settings
            </Link>

            <p className="border-t border-border pt-3 text-[11px] leading-relaxed text-muted">{card.disclaimer}</p>
          </>
        )}
      </CardContent>
    </Card>
  );
}
