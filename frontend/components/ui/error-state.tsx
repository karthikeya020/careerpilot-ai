import { AlertTriangle, ShieldOff } from "lucide-react";
import Link from "next/link";
import { Button } from "./button";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  /** True for a 403 (wrong role, not a real failure) -- renders a calm,
   * non-alarming "access restricted" state instead of a red error with a
   * "Try again" button that would just repeat the same denial forever. */
  isPermissionDenied?: boolean;
  /** Set to "h1" when this component is the entire page's content (an early
   * return with no other heading rendered) so the page still has exactly
   * one h1 for screen-reader heading navigation. Leave as the default "p"
   * when ErrorState is nested inside a page that already renders its own
   * h1 elsewhere -- promoting it there would create a second, competing h1. */
  titleAs?: "p" | "h1";
}

export function ErrorState({ title, message, onRetry, isPermissionDenied = false, titleAs: Title = "p" }: ErrorStateProps) {
  const resolvedTitle = title ?? (isPermissionDenied ? "Access restricted" : "Something went wrong");
  return (
    <div
      role="alert"
      className={
        isPermissionDenied
          ? "flex flex-col items-center justify-center gap-3 rounded-[var(--radius-md)] border border-border bg-surface-muted p-8 text-center"
          : "flex flex-col items-center justify-center gap-3 rounded-[var(--radius-md)] border border-danger/30 bg-danger/5 p-8 text-center"
      }
    >
      <div
        className={
          isPermissionDenied
            ? "flex h-11 w-11 items-center justify-center rounded-full bg-surface text-muted"
            : "flex h-11 w-11 items-center justify-center rounded-full bg-danger/10 text-danger"
        }
      >
        {isPermissionDenied ? <ShieldOff className="h-5 w-5" aria-hidden="true" /> : <AlertTriangle className="h-5 w-5" aria-hidden="true" />}
      </div>
      <div className="space-y-1">
        <Title className="text-sm font-medium text-foreground">{resolvedTitle}</Title>
        <p className="text-xs text-muted max-w-sm">{message}</p>
      </div>
      {isPermissionDenied ? (
        <Link href="/dashboard" className="text-xs font-medium text-brand hover:underline">
          Back to dashboard
        </Link>
      ) : onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}
