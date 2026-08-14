import type { LucideIcon } from "lucide-react";
import {
  FileText,
  FlaskConical,
  LayoutDashboard,
  ListChecks,
  Mic,
  Microscope,
  Network,
  Scale,
  ShieldCheck,
  Settings,
  Sparkles,
  Target,
} from "lucide-react";

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
  { href: "/graphrag", label: "GraphRAG", icon: Network },
  { href: "/interview", label: "Interview Arena", icon: Mic },
  { href: "/experiment-lab", label: "Experiment Lab", icon: FlaskConical },
  { href: "/research-lab", label: "Research Lab", icon: Microscope },
  { href: "/trust-center", label: "Trust Center", icon: ShieldCheck },
  { href: "/responsible-ai", label: "Responsible AI", icon: Scale },
  { href: "/settings", label: "Settings", icon: Settings },
];
