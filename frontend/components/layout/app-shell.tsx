"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ChevronRight, LogOut, Menu, X } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { toast } from "sonner";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import { NAV_GROUPS, NAV_LINKS } from "./nav-links";
import { PageTransitionSweep } from "./page-transition-sweep";
import { ThemeToggle } from "./theme-toggle";

function BrandMark() {
  return (
    <Link href="/dashboard" className="flex items-center gap-2.5 font-semibold text-foreground">
      <Logo size={30} />
      <span className="text-[15px] tracking-tight">CareerPilot</span>
    </Link>
  );
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Primary" className="flex flex-1 flex-col gap-5 overflow-y-auto py-1">
      {NAV_GROUPS.map((group) => (
        <div key={group.label} className="space-y-1">
          <p className="ds-eyebrow px-3 text-[10px]">{group.label}</p>
          {group.links.map((link) => {
            const isActive = pathname === link.href;
            const Icon = link.icon;
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={isActive ? "page" : undefined}
                data-active={isActive}
                onClick={onNavigate}
                className={cn(
                  "ds-nav-item ds-focus group flex items-center gap-3 px-3 py-2 text-sm font-medium",
                  isActive ? "text-foreground" : "text-muted hover:bg-surface-muted hover:text-foreground",
                )}
              >
                <Icon
                  className={cn("h-4 w-4 shrink-0 transition-colors", isActive && "text-brand")}
                  aria-hidden="true"
                />
                <span className="truncate">{link.label}</span>
                <ChevronRight
                  className={cn(
                    "ml-auto h-3.5 w-3.5 shrink-0 -translate-x-2 opacity-0 transition-all duration-200 ease-out",
                    "group-hover:translate-x-0 group-hover:opacity-100",
                    isActive ? "translate-x-0 text-brand opacity-70" : "text-muted",
                  )}
                  aria-hidden="true"
                />
              </Link>
            );
          })}
        </div>
      ))}
    </nav>
  );
}

function UserBlock({ email, onLogout }: { email?: string; onLogout: () => void }) {
  return (
    <div className="mt-auto space-y-2 border-t border-border pt-4">
      <p className="truncate px-1 text-xs text-muted">{email}</p>
      <Button variant="ghost" size="sm" className="ds-focus w-full justify-start" onClick={onLogout}>
        <LogOut className="h-4 w-4" /> Sign out
      </Button>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  // The Job Match "Scroll Jobs" rail docks to the right third of the screen;
  // while it's open the sidebar collapses left and the content column shifts.
  const [reelDocked, setReelDocked] = useState(false);
  useEffect(() => {
    const handler = (e: Event) => setReelDocked(!!(e as CustomEvent).detail);
    window.addEventListener("careerpilot:reel", handler);
    return () => window.removeEventListener("careerpilot:reel", handler);
  }, []);

  const handleLogout = async () => {
    await logout();
    toast.success("Signed out");
    router.push("/login");
  };

  const currentLabel = NAV_LINKS.find((l) => l.href === pathname)?.label ?? "CareerPilot";

  return (
    <div className="flex min-h-screen bg-background">
      <PageTransitionSweep />

      <aside
        className={cn(
          "print-hidden hidden shrink-0 flex-col border-r border-border bg-surface/70 backdrop-blur-xl md:flex",
          "overflow-hidden transition-[width,padding,opacity] duration-300 ease-out",
          reelDocked ? "md:w-0 md:border-0 md:p-0 md:opacity-0" : "w-64 p-4 opacity-100",
        )}
        aria-hidden={reelDocked}
      >
        <div className="mb-6 px-1">
          <BrandMark />
        </div>
        <NavList />
        <UserBlock email={user?.email} onLogout={handleLogout} />
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div className="absolute inset-0 bg-foreground/40 backdrop-blur-sm" onClick={() => setMobileOpen(false)} aria-hidden="true" />
          <div className="relative z-50 flex w-72 flex-col bg-surface p-4">
            <div className="mb-6 flex items-center justify-between">
              <BrandMark />
              <Button variant="ghost" size="icon" onClick={() => setMobileOpen(false)} aria-label="Close menu">
                <X className="h-4 w-4" />
              </Button>
            </div>
            <NavList onNavigate={() => setMobileOpen(false)} />
            <UserBlock email={user?.email} onLogout={handleLogout} />
          </div>
        </div>
      ) : null}

      <div
        className="flex flex-1 flex-col transition-[margin] duration-300 ease-out"
        style={{ marginRight: reelDocked ? "min(42vw, 560px)" : undefined }}
      >
        <header className="print-hidden sticky top-0 z-30 flex h-14 items-center justify-between gap-3 border-b border-border bg-background/70 px-4 backdrop-blur-xl">
          <div className="flex min-w-0 items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <span className="truncate text-sm font-medium text-muted">{currentLabel}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-1.5 text-[11px] text-muted sm:flex">
              <span className="ds-live-dot" aria-hidden="true" />
              AI online
            </span>
            <ThemeToggle />
          </div>
        </header>
        <main className="flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
