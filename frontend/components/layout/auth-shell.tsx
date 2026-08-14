import Link from "next/link";
import type { ReactNode } from "react";
import { GaugeCircle, ShieldCheck, Sparkles } from "lucide-react";
import { Logo } from "@/components/brand/logo";
import { ThemeToggle } from "./theme-toggle";

const FEATURE_BULLETS = [
  { icon: GaugeCircle, label: "Six-component readiness, every score evidence-traced" },
  { icon: Sparkles, label: "A knowledge graph that explains root causes, not just gaps" },
  { icon: ShieldCheck, label: "No hiring predictions. No rankings. No fabricated numbers." },
];

function EntryVisual() {
  const nodes = [
    { cx: 50, cy: 6, r: 3, delay: "0s" },
    { cx: 86, cy: 26, r: 2.2, delay: "0.4s" },
    { cx: 92, cy: 64, r: 2.8, delay: "0.8s" },
    { cx: 64, cy: 92, r: 2.4, delay: "1.2s" },
    { cx: 20, cy: 88, r: 2.6, delay: "1.6s" },
    { cx: 6, cy: 50, r: 2.2, delay: "2s" },
    { cx: 16, cy: 16, r: 2.8, delay: "2.4s" },
  ];
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[22rem]" aria-hidden="true">
      <div className="absolute inset-[14%] rounded-full bg-gradient-radial-brand blur-3xl opacity-80 animate-pulse-glow" />
      <div className="absolute inset-[26%] rounded-full bg-gradient-brand opacity-90 shadow-[var(--shadow-glow-brand)] animate-float" />
      <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
        <circle cx="50" cy="50" r="46" fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="0.5" />
        <circle cx="50" cy="50" r="34" fill="none" stroke="rgba(255,255,255,0.14)" strokeWidth="0.5" strokeDasharray="2 3" />
        {nodes.map((n, i) => (
          <g key={i}>
            <line x1="50" y1="50" x2={n.cx} y2={n.cy} stroke="white" strokeOpacity="0.28" strokeWidth="0.4" />
            <circle cx={n.cx} cy={n.cy} r={n.r} className="animate-pulse-glow" style={{ animationDelay: n.delay }} fill="white" fillOpacity="0.85" />
          </g>
        ))}
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-xs font-semibold uppercase tracking-[0.22em] text-white drop-shadow-sm">Career Twin</span>
      </div>
    </div>
  );
}

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="flex min-h-screen">
      <aside className="bg-grain bg-mesh-animated relative hidden w-[46%] shrink-0 flex-col justify-between overflow-hidden p-10 text-white lg:flex">
        <div className="absolute inset-0 bg-gradient-to-br from-[color-mix(in_srgb,var(--brand)_92%,black)] via-[color-mix(in_srgb,var(--brand-2)_75%,black)] to-[color-mix(in_srgb,var(--accent)_60%,black)]" />
        <div className="relative z-[2] flex items-center gap-2.5 text-sm font-semibold">
          <span className="flex h-8 w-8 items-center justify-center rounded-[var(--radius-sm)] bg-white/15 backdrop-blur">
            <Logo size={22} variant="mark" />
          </span>
          CareerPilot AI
        </div>

        <div className="relative z-[2] flex flex-col items-center gap-8 py-6">
          <EntryVisual />
          <div className="max-w-sm text-center">
            <h2 className="text-h2 font-bold leading-tight text-white">
              The Career Operating System that shows its work.
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-white/75">
              Every readiness score, mission, and match traces back to a real evidence record — never a guess.
            </p>
          </div>
        </div>

        <ul className="relative z-[2] space-y-3">
          {FEATURE_BULLETS.map(({ icon: Icon, label }) => (
            <li key={label} className="flex items-center gap-3 rounded-[var(--radius-md)] border border-white/15 bg-white/10 px-3.5 py-2.5 text-xs font-medium text-white/90 backdrop-blur">
              <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              {label}
            </li>
          ))}
        </ul>
      </aside>

      <div className="bg-mesh flex flex-1 flex-col">
        <header className="flex items-center justify-between px-6 py-5">
          <Link href="/" className="flex items-center gap-2.5 font-semibold text-foreground lg:hidden">
            <Logo size={32} />
            CareerPilot AI
          </Link>
          <span className="hidden lg:block" />
          <ThemeToggle />
        </header>
        <main className="flex flex-1 items-center justify-center px-4 py-8">
          <div className="animate-scale-in card-glass w-full max-w-sm rounded-[var(--radius-xl)] p-7">
            <div className="mb-6 text-center">
              <h1 className="text-h2 text-foreground">{title}</h1>
              <p className="mt-1 text-sm text-muted">{subtitle}</p>
            </div>
            {children}
            <p className="mt-6 text-center text-sm text-muted">{footer}</p>
          </div>
        </main>
      </div>
    </div>
  );
}
