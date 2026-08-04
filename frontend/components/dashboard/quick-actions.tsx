import Link from "next/link";
import { FileText, Sparkles, Target, UserCog } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const ACTIONS = [
  { href: "/resume", label: "Upload resume", icon: FileText },
  { href: "/job-description", label: "Add job description", icon: Target },
  { href: "/career-twin", label: "View Career Twin", icon: Sparkles },
  { href: "/settings", label: "Edit profile", icon: UserCog },
];

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick actions</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        {ACTIONS.map((action) => (
          <Button key={action.href} variant="secondary" size="sm" className="justify-start" asChild>
            <Link href={action.href}>
              <action.icon className="h-4 w-4 shrink-0" /> <span className="truncate">{action.label}</span>
            </Link>
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}
