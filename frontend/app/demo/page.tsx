"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { AuthShell } from "@/components/layout/auth-shell";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";

const DEMO_EMAIL = "demo.student@careerpilot.ai";
const DEMO_PASSWORD = "DemoPass!2026";

export default function DemoPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const enterDemo = async () => {
    setIsLoading(true);
    try {
      await login(DEMO_EMAIL, DEMO_PASSWORD);
      toast.success("Welcome, Aanya — this is the seeded demo account.");
      router.push("/dashboard");
    } catch (error) {
      const message =
        error instanceof ApiError
          ? "Demo account isn't seeded yet. Ask the presenter to run the seed script."
          : "Couldn't reach the CareerPilot API. Is the backend running?";
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      title="Explore the demo"
      subtitle="See a fully populated Career Twin without creating an account."
      footer={<span>Presenting live? This uses the deterministic seeded demo student.</span>}
    >
      <div className="space-y-4 rounded-[var(--radius-md)] border border-border bg-surface-muted p-4 text-sm text-muted">
        <p>
          This signs in as <span className="font-medium text-foreground">Aanya Sharma</span>, a seeded student
          with a parsed resume, a matched job description, and a real Career Twin snapshot.
        </p>
        <dl className="space-y-1 text-xs">
          <div className="flex justify-between">
            <dt>Email</dt>
            <dd className="font-mono text-foreground">{DEMO_EMAIL}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Password</dt>
            <dd className="font-mono text-foreground">{DEMO_PASSWORD}</dd>
          </div>
        </dl>
      </div>
      <Button className="mt-4 w-full" size="lg" onClick={enterDemo} disabled={isLoading}>
        {isLoading ? "Signing in…" : "Continue as demo student"}
      </Button>
    </AuthShell>
  );
}
