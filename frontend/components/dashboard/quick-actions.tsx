import Link from "next/link";
import { FileText, Presentation, Sparkles, Target, UserCog } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ACTIONS = [
  { href: "/resume", label: "Upload resume", icon: FileText },
  { href: "/job-description", label: "Add job description", icon: Target },
  { href: "/career-twin", label: "View Career Twin", icon: Sparkles },
  { href: "/settings", label: "Edit profile", icon: UserCog },
  { href: "/competition", label: "Competition Mode", icon: Presentation },
];

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick actions</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-2">
        {ACTIONS.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            className="group flex flex-col items-start gap-2 rounded-[var(--radius-md)] border border-border bg-surface-muted p-3 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-[var(--shadow-glow-brand)]"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] bg-surface text-brand transition-colors group-hover:bg-gradient-brand group-hover:text-brand-foreground">
              <action.icon className="h-4 w-4" aria-hidden="true" />
            </span>
            <span className="text-xs font-medium leading-tight text-foreground">{action.label}</span>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
