import type { LucideIcon } from "lucide-react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * The metric language (Tremor-influenced): label on top, one big tabular
 * number, an optional delta chip and a hint line. Deltas colour by
 * direction; a null delta shows nothing. Consistent everywhere a number
 * is the point.
 */
export function Stat({
  label,
  value,
  delta,
  hint,
  icon: Icon,
  accent = "var(--color-brand)",
  className,
}: {
  label: string;
  value: ReactNode;
  delta?: number | null;
  hint?: ReactNode;
  icon?: LucideIcon;
  accent?: string;
  className?: string;
}) {
  const hasDelta = typeof delta === "number" && Number.isFinite(delta);
  const dir = !hasDelta ? "flat" : delta > 0.0005 ? "up" : delta < -0.0005 ? "down" : "flat";
  const DeltaIcon = dir === "up" ? ArrowUpRight : dir === "down" ? ArrowDownRight : Minus;
  const deltaColor =
    dir === "up" ? "var(--color-positive)" : dir === "down" ? "var(--color-danger)" : "var(--color-muted)";

  return (
    <div className={cn("ds-panel p-4", className)}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-[11px] font-medium text-muted">{label}</p>
        {Icon ? (
          <span
            className="flex h-6 w-6 items-center justify-center rounded-[var(--radius-sm)]"
            style={{ background: `color-mix(in srgb, ${accent} 14%, transparent)`, color: accent }}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
          </span>
        ) : null}
      </div>
      <p className="ds-stat mt-2 text-[1.65rem] text-foreground">{value}</p>
      <div className="mt-1.5 flex items-center gap-1.5 text-[11px]">
        {hasDelta ? (
          <span className="inline-flex items-center gap-0.5 font-medium" style={{ color: deltaColor }}>
            <DeltaIcon className="h-3 w-3" aria-hidden="true" />
            {Math.abs(delta! * 100) >= 0.1 ? `${(delta! * 100).toFixed(1)}%` : "flat"}
          </span>
        ) : null}
        {hint ? <span className="truncate text-muted">{hint}</span> : null}
      </div>
    </div>
  );
}

export function StatGrid({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("grid gap-3 sm:grid-cols-2 lg:grid-cols-4", className)}>{children}</div>;
}
