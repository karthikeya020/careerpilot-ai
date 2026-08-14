# CareerPilot AI — Design System

The single source of visual truth for every screen. Tokens live in
`frontend/app/globals.css`; primitives live in `frontend/components/ui/*`.
Every page should compose these rather than inventing new colors,
radii, shadows, or animation timings.

## Color tokens

Defined as CSS custom properties on `:root` (light) and `.dark`, mapped
into Tailwind via `@theme inline` so they're usable as `bg-*`/`text-*`/
`border-*` utility classes.

| Token | Role |
|---|---|
| `--background` / `--background-elevated` | Page background, layered surface |
| `--surface` / `--surface-muted` / `--surface-glass` | Card backgrounds — solid, muted, and glass (blurred, for auth screens and hero overlays) |
| `--foreground` / `--muted` | Primary and secondary text |
| `--border` / `--border-strong` | Default and emphasized borders |
| `--brand` / `--brand-2` | Primary gradient pair (violet → magenta in dark theme, violet → purple in light) |
| `--accent` / `--accent-2` | Secondary gradient pair (teal/cyan) — used for non-brand emphasis (placement/faculty dashboards) |
| `--positive` / `--warning` / `--danger` | Semantic status colors, tuned per-theme for contrast as *text* |

Dark theme is deliberately more saturated and glow-heavy ("deep, layered,
luxurious" per the brief) than light theme, which stays closer to a
neutral off-white with the same hue relationships.

**Never hardcode a hex color in a component.** If a new semantic needs a
color, add a token to `globals.css` in both `:root` and `.dark`, not an
inline hex.

## Typography scale

`text-display`, `text-h1`, `text-h2`, `text-h3`, `text-projector`,
`text-projector-lg`, `text-metric`, `text-metric-lg` — all `clamp()`-based
so they scale between mobile and projector widths without a separate
breakpoint system. `text-projector*` and `text-metric*` are deliberately
oversized for Competition Mode and hero stat tiles; regular page headers
use `text-h1`/`text-h2`/`text-h3`.

Every page's `<h1>` should use `text-h1` (not a raw `text-2xl
font-semibold` — that was the old flat style still being retired from a
few secondary pages). First-level `Card` on a page should use `CardTitle
as="h2"` to keep heading order correct for screen readers.

## Surface treatments

- `.card-premium` — the default card: solid surface, 1px border, medium
  shadow, subtle hover lift when combined with `.card-premium-hover`
  (wired via `<Card interactive>`).
- `.card-glass` — blurred/translucent, used for hero overlays and the
  auth-flow card (`AuthShell`).
- `.card-glow-brand` / `.card-glow-accent` — adds a colored glow shadow
  and tinted border, reserved for the page's single most important card
  (a signature reveal, the primary CTA card) — not every card, or the
  emphasis is lost.
- `.bg-mesh` — the soft multi-blob radial-gradient background used on
  page hero sections and the app shell's overall backdrop.
- `.bg-grid` — faint grid overlay, used sparingly for technical/data
  screens (Trust Center, Research Lab) to signal "system internals."

## Motion system

All animations respect `prefers-reduced-motion` globally (see the
`@media` block at the bottom of `globals.css` — durations collapse to
0.01ms) — **individual components never need their own reduced-motion
handling** as long as they use the shared `.animate-*` classes.

| Class | Use |
|---|---|
| `.animate-fade-up` | Default entrance for cards/sections, staggered via `.delay-1`…`.delay-8` |
| `.animate-scale-in` | Emphasis entrance (icon badges, result reveals) |
| `.animate-pulse-glow` | Sustained attention (recording indicator, root-cause spotlight) |
| `.animate-draw-line` | Connector lines in node-chain visualizations (GraphRAG, Trust Center timeline) — set `--line-length` per use |
| `.animate-gradient` | Indeterminate progress (CARE-processing state) |
| `.skeleton-shimmer` | Loading skeletons |

Stagger delays (`delay-1`…`delay-8`, 80ms apart) are used for sequential
reveal — most visibly in the GraphRAG node chain and the Trust Center
execution timeline, where each step should feel like it's activating in
order, not appearing all at once.

## Core primitives (`components/ui/*`)

- **`Card`** — `variant`: `default` | `glass` | `glow-brand` | `glow-accent`; `interactive` adds hover lift. Composed with `CardHeader`/`CardTitle`/`CardDescription`/`CardContent`/`CardFooter`.
- **`Badge`** — `variant`: `default` | `positive` | `warning` | `danger` | `muted` | `outline`. Used for status, route labels, and stored-fact/inference indicators.
- **`Button`** — `variant`: `primary` (gradient) | `secondary` | `ghost` | `outline` | `destructive` | `link`; `size`: `sm` | `default` | `lg` | `xl` | `icon`.
- **`Progress`** — always needs an `aria-label` (axe-audited requirement — see `CURRENT_CHECKPOINT.md`).
- **`EmptyState`** / **`ErrorState`** — every data-driven page must handle loading/empty/error. `ErrorState` takes `isPermissionDenied` for 403s (renders calmly, no "Try again" loop) and `titleAs="h1"` when it's the page's only content.
- **`Skeleton`** — shimmer placeholder, sized to approximate the real content's layout.

## Page anatomy convention

Every top-level page (`/graphrag`, `/experiment-lab`, `/research-lab`,
etc.) follows the same shape, established in this pass and the one
before it:

1. A `bg-mesh` hero block: icon badge in a `bg-gradient-brand` square,
   `text-h1` title, one-sentence `text-muted` subtitle, relevant status
   badges.
2. Primary content in `Card`s, `animate-fade-up` with incrementing
   `delay-N`.
3. The single most important card (a live result, a root-cause chain, a
   signature reveal) gets `variant="glow-brand"`.
4. Loading → `Skeleton`; empty → `EmptyState` with an actionable CTA;
   error → `ErrorState`, `isPermissionDenied` for 403s.

## Role-dashboard accent convention

The four role dashboards share the same card/type system but each gets a
distinct accent gradient in its hero block so they feel purposefully
different while staying part of one product: Admin uses the primary
brand gradient, Faculty uses `--accent-2`→`--accent` (teal/cyan,
"teaching"), Placement uses `--accent`→`--accent-2` (institutional),
Recruiter uses `--brand-2`→`--brand` (magenta, "external-facing"). The
student Career OS dashboard remains the visual hero of the product — none
of the role dashboards reuse its `glow-brand` treatment.
