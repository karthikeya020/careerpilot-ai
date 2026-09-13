import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Section framing — the one way sections are titled across CareerPilot.
 * eyebrow (optional) → title → description, with an optional right-aligned
 * action. Keeps rhythm consistent so a page reads as one document.
 */
export function SectionHeader({
  eyebrow,
  title,
  description,
  action,
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-end justify-between gap-4", className)}>
      <div className="min-w-0">
        {eyebrow ? <p className="ds-eyebrow mb-1">{eyebrow}</p> : null}
        <h2 className="text-h3 text-foreground">{title}</h2>
        {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function Section({
  eyebrow,
  title,
  description,
  action,
  children,
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cn("space-y-4", className)}>
      <SectionHeader eyebrow={eyebrow} title={title} description={description} action={action} />
      {children}
    </section>
  );
}
