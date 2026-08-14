"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ChevronRight, LogOut, Menu, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { toast } from "sonner";
import { Logo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import { NAV_LINKS } from "./nav-links";
import { PageTransitionSweep } from "./page-transition-sweep";
import { ThemeToggle } from "./theme-toggle";

function BrandMark() {
  return (
    <Link href="/dashboard" className="flex items-center gap-2.5 font-semibold text-foreground">
      <Logo size={32} />
      <span className="text-[15px] tracking-tight">CareerPilot</span>
    </Link>
  );
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Primary" className="flex flex-1 flex-col gap-1">
      {NAV_LINKS.map((link) => {
        const isActive = pathname === link.href;
        const Icon = link.icon;
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={isActive ? "page" : undefined}
            onClick={onNavigate}
            className={cn(
              "group flex items-center gap-3 rounded-[var(--radius-md)] px-3 py-2 text-sm font-medium transition-all duration-150",
              isActive
                ? "bg-brand-soft text-brand shadow-[inset_0_0_0_1px_color-mix(in_srgb,var(--brand)_25%,transparent)]"
                : "text-muted hover:bg-surface-muted hover:text-foreground hover:translate-x-0.5",
            )}
          >
            <Icon
              className={cn("h-4 w-4 transition-transform", isActive && "text-brand")}
              aria-hidden="true"
            />
            {link.label}
            <ChevronRight
              className={cn(
                "ml-auto h-3.5 w-3.5 shrink-0 -translate-x-2 opacity-0 transition-all duration-200 ease-out",
                "group-hover:translate-x-0 group-hover:opacity-100",
                isActive ? "translate-x-0 opacity-70 text-brand" : "text-muted",
              )}
              aria-hidden="true"
            />
          </Link>
        );
      })}
    </nav>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    toast.success("Signed out");
    router.push("/login");
  };

  return (
    <div className="flex min-h-screen bg-mesh">
      <PageTransitionSweep />

      <aside className="print-hidden hidden w-64 shrink-0 flex-col border-r border-border bg-surface/80 backdrop-blur-xl p-4 md:flex">
        <div className="mb-6 px-1">
          <BrandMark />
        </div>
        <NavList />
        <div className="mt-auto space-y-2 border-t border-border pt-4">
          <p className="truncate px-1 text-xs text-muted">{user?.email}</p>
          <Button variant="ghost" size="sm" className="w-full justify-start" onClick={handleLogout}>
            <LogOut className="h-4 w-4" /> Sign out
          </Button>
        </div>
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileOpen(false)} aria-hidden="true" />
          <div className="relative z-50 flex w-64 flex-col bg-surface p-4">
            <div className="mb-6 flex items-center justify-between">
              <BrandMark />
              <Button variant="ghost" size="icon" onClick={() => setMobileOpen(false)} aria-label="Close menu">
                <X className="h-4 w-4" />
              </Button>
            </div>
            <NavList onNavigate={() => setMobileOpen(false)} />
            <div className="mt-auto space-y-2 border-t border-border pt-4">
              <p className="truncate px-1 text-xs text-muted">{user?.email}</p>
              <Button variant="ghost" size="sm" className="w-full justify-start" onClick={handleLogout}>
                <LogOut className="h-4 w-4" /> Sign out
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      <div className="flex flex-1 flex-col">
        <header className="print-hidden sticky top-0 z-30 flex h-14 items-center justify-between border-b border-border bg-surface/70 backdrop-blur-xl px-4 md:justify-end">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-2">
            <ThemeToggle />
          </div>
        </header>
        <main className="flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
