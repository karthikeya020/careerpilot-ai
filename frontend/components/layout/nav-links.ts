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
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";

export interface NavLink {
  href: string;
  label: string;
  icon: LucideIcon;
}

export interface NavGroup {
  label: string;
  links: NavLink[];
}

/** Navigation clusters -- see design system §10. */
export const NAV_GROUPS: NavGroup[] = [
  {
    label: "Overview",
    links: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/career-twin", label: "Career Twin", icon: Sparkles },
    ],
  },
  {
    label: "Prepare",
    links: [
      { href: "/resume", label: "Resume", icon: FileText },
      { href: "/job-description", label: "Job Match", icon: Target },
      { href: "/assessment", label: "Assessment", icon: ListChecks },
      { href: "/interview", label: "Interview Arena", icon: Mic },
    ],
  },
  {
    label: "Intelligence",
    links: [
      { href: "/graphrag", label: "GraphRAG", icon: Network },
      { href: "/experiment-lab", label: "Experiment Lab", icon: FlaskConical },
      { href: "/research-lab", label: "Research Lab", icon: Microscope },
    ],
  },
  {
    label: "Trust",
    links: [
      { href: "/trust-center", label: "Trust Center", icon: ShieldCheck },
      { href: "/responsible-ai", label: "Responsible AI", icon: Scale },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

/** Flat list — kept for anything that just needs every destination. */
export const NAV_LINKS: NavLink[] = NAV_GROUPS.flatMap((g) => g.links);
