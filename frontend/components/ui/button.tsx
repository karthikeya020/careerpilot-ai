import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-md)] text-sm font-medium transition-all duration-200 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        primary:
          "bg-gradient-brand text-brand-foreground shadow-[var(--shadow-glow-brand)] hover:brightness-110 hover:-translate-y-px",
        secondary: "bg-surface-muted text-foreground hover:bg-border/60 border border-border hover:-translate-y-px",
        ghost: "hover:bg-surface-muted text-foreground",
        outline: "border border-border bg-transparent hover:bg-surface-muted hover:border-border-strong text-foreground",
        // Fixed red-600 rather than the shared --danger token: --danger is
        // tuned to be readable as *text* on dark surfaces (dark theme uses
        // a light red, #f87171) but that same light red under white button
        // text falls to ~2.8:1 contrast, well under WCAG AA's 4.5:1. A
        // fixed, theme-invariant background keeps this button legible in
        // both themes without touching --danger's other (correct) uses.
        destructive: "bg-red-600 text-white hover:opacity-90",
        link: "text-brand underline-offset-4 hover:underline p-0 h-auto",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-12 px-6 text-base",
        xl: "h-14 px-8 text-base rounded-[var(--radius-lg)]",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size }), className)} ref={ref} {...props} />;
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
