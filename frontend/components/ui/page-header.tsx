import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Every route opens with this. A calm elevated band — thin aurora wash, an
 * icon chip, an eyebrow, the page title, one line of context, optional
 * actions. Replaces the ad-hoc `bg-mesh` hero each page reinvented.
 */
export function PageHeader({
  icon: Icon,
  eyebrow,
  title,
  description,
  actions,
  className,
}: {
  icon?: LucideIcon;
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "ds-panel-raised relative overflow-hidden rounded-[var(--radius-xl)] px-6 py-6 md:px-8 md:py-7",
        className,
      )}
    >
      <div
        className="pointer-events-none absolute -right-24 -top-28 h-64 w-64 rounded-full opacity-60 blur-3xl"
        style={{ background: "var(--color-brand)" }}
        aria-hidden="true"
      />
      <div className="relative flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-3">
            {Icon ? (
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-gradient-brand text-brand-foreground shadow-[var(--shadow-glow-brand)]">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
            ) : null}
            <div>
              {eyebrow ? <p className="ds-eyebrow">{eyebrow}</p> : null}
              <h1 className="text-h1 text-foreground">{title}</h1>
            </div>
          </div>
          {description ? <p className="mt-3 max-w-2xl text-sm text-muted">{description}</p> : null}
        </div>
        {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
      </div>
    </header>
  );
}
