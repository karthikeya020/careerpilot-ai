"use client";

import { Toaster as SonnerToaster } from "sonner";
import { useTheme } from "@/lib/theme-provider";

export function Toaster() {
  const { theme } = useTheme();
  return (
    <SonnerToaster
      theme={theme}
      position="bottom-right"
      toastOptions={{
        classNames: {
          toast: "!bg-surface !text-foreground !border-border",
          description: "!text-muted",
        },
      }}
    />
  );
}
