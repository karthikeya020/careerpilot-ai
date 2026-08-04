import type { LucideIcon } from "lucide-react";
import { FileText, FlaskConical, LayoutDashboard, ListChecks, Mic, ShieldCheck, Settings, Sparkles, Target } from "lucide-react";

export interface NavLink {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_LINKS: NavLink[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/career-twin", label: "Career Twin", icon: Sparkles },
  { href: "/resume", label: "Resume", icon: FileText },
  { href: "/job-description", label: "Job Match", icon: Target },
  { href: "/assessment", label: "Assessment", icon: ListChecks },
  { href: "/interview", label: "Interview Arena", icon: Mic },
  { href: "/experiment-lab", label: "Experiment Lab", icon: FlaskConical },
  { href: "/trust-center", label: "Trust Center", icon: ShieldCheck },
  { href: "/settings", label: "Settings", icon: Settings },
];
