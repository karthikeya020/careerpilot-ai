# CareerPilot Design System

CareerPilot is an **AI career operating system** — not a dashboard template, not
a chatbot. The UI should feel calm, dense with signal, and *quietly
intelligent*: motion communicates state and reasoning, never decoration.

References studied (as inspiration only, never copied wholesale): shadcn/ui
(component foundation), React Bits (micro‑interaction restraint), Aceternity UI
(one high‑impact effect per surface), Magic UI (SaaS polish), Tremor (analytics
grammar), shadcn‑dashboard (information architecture), Spectrum UI (composition).

The system lives in **one place**: `frontend/app/globals.css` (tokens +
canonical `.ds-*` primitives) and `frontend/components/ui/*` (React
primitives). Do not restyle a surface with a bespoke stack of Tailwind classes
— reach for a primitive or extend the system.

---

## 1. Color

| Role | Token | Light | Dark |
| --- | --- | --- | --- |
| Page | `--background` | `#f6f5fb` | `#060512` |
| Raised page | `--background-elevated` | `#ffffff` | `#0b0a1a` |
| Panel | `--surface` | `#ffffff` | `#0f0d1f` |
| Inset / muted | `--surface-muted` | `#f0eff8` | `#171429` |
| Glass | `--surface-glass` | `rgba(255,255,255,.7)` | `rgba(20,18,38,.55)` |
| Text | `--foreground` | `#14121f` | `#f5f3fd` |
| Secondary text | `--muted` | `#666280` | `#a29dc2` |
| Hairline | `--border` | `#e4e2ee` | `#262147` |
| Strong border | `--border-strong` | `#d4d1e6` | `#362f5e` |

**Brand** is a deep periwinkle (`--brand`) with a violet second stop
(`--brand-2`); it is the primary series colour, the active‑route accent, and
the only gradient (`.bg-gradient-brand`, 135°). **Accent** teal/cyan
(`--accent`, `--accent-2`) is for secondary data series and supporting glows.
Semantic: `--positive` `--warning` `--danger`. Focus: `--ring`.

Use `color-mix(in srgb, …)` for tints (e.g. `var(--color-brand) 10%`), never
hard‑coded hex. Every value has a light and dark answer.

---

## 2. Typography

Geist Sans (body/UI), Geist Mono (code, IDs, raw values). Body letter‑spacing
`-0.011em`; OpenType `cv02 cv03 cv04 cv11` on.

| Class | Use |
| --- | --- |
| `.text-display` | landing / entry only |
| `.text-h1` | page title (in `PageHeader`) |
| `.text-h2` | rare — full‑bleed section |
| `.text-h3` | section title (in `SectionHeader`) |
| `.ds-eyebrow` | uppercase 0.14em tracked label above a title |
| `.text-metric` / `.ds-stat` | big tabular numbers |
| default `text-sm` | body copy |
| `text-xs` / `text-[11px]` | metadata, captions, chips |

One `<h1>` per page (the `PageHeader`). Sections are `<h2 class="text-h3">`.

---

## 3. Spacing & layout

4px base. Page content: `mx-auto max-w-6xl` (wide analytics) or `max-w-2xl`
(focused flows), `space-y-8` between sections, `space-y-4` inside a section.
Panels pad `p-4`–`p-6`; the `PageHeader` pads `px-6 py-6 md:px-8 md:py-7`.
Gaps between cards: `gap-3` (tiles) / `gap-4` (cards).

---

## 4. Radius

`--radius-sm .5rem` (chips, inner tiles) · `--radius-md .9rem` (buttons,
inputs, nav items) · `--radius-lg 1.25rem` (panels/cards) · `--radius-xl
1.75rem` (page header, modals) · `--radius-full` (pills, avatars, dots).

---

## 5. Elevation

A four‑step ladder — never invent a shadow.

`--shadow-xs` resting panels · `--shadow-md` hover / raised / tooltips ·
`--shadow-lg` modals, popovers, the reel rail · `--shadow-glow-brand` the one
"this is the important thing" treatment (hero chip, active dream job).

---

## 6. Surface hierarchy

`page` → `.ds-panel` → `.ds-panel-raised`. Each step = **one** unit more
contrast and elevation. `.ds-inset` is a recessed area *inside* a panel
(muted bg, softer border). Glass (`.card-glass`, `.glass-panel`) is reserved
for overlays floating above real content.

---

## 7. Iconography

`lucide-react`, `1.5` stroke, sized `h-4 w-4` inline / `h-5 w-5` in header
chips / `h-3–3.5` in chips. Icons are functional, never ornamental; one per
nav item, one per section header at most.

---

## 8. Motion language

Tokens (`globals.css`): `--dur-fast 140ms` (hover/press/toggle) ·
`--dur-base 260ms` (element enter/exit, panels) · `--dur-slow 520ms` (hero,
orchestrated) · `--ease-out` (decelerate to rest — most UI) · `--ease-spring`
(confident overshoot — primary actions, active indicators).

Rules:
- **Motion = meaning.** An element moves because its *state or relevance
  changed*. No idle decorative loops except the single `.ds-live-dot` pulse
  (system online) and hero aurora.
- **One enter gesture:** `<Reveal>` / `.ds-reveal` — a short fade + 12px rise
  as content scrolls in, one‑shot, staggered by `delay`.
- **State transitions animate:** active nav accent slides (`layoutId`),
  numbers roll (`CountUp`), progress bars grow from 0, tab indicators glide.
- **Primary actions** get a spark + magnetic pull (`ClickSpark`, `Magnetic`)
  — used sparingly (the 2–3 real CTAs on a page).
- Everything respects `prefers-reduced-motion` (global rule zeroes durations;
  `.ds-reveal` renders in place).

---

## 9. Card language

`.ds-panel` is the card. Add `.ds-panel-interactive` for a hover lift on
clickable cards, `.ds-panel-raised` for the one hero card on a page. A card
has: an optional header row (icon chip + title + meta), a body, and at most
one primary action. No nested cards — use `.ds-inset` for sub‑regions and a
`.ds-hairline` to divide. Legacy `.card-premium` is being migrated to
`.ds-panel`.

---

## 10. Navigation language

Left rail, grouped into labelled clusters (Overview / Prepare / Intelligence /
Trust). Items use `.ds-nav-item`; the active route gets a soft brand tint and
a **3px left accent bar** (not a filled pill) — it should read like an OS
sidebar. The top bar carries the current section name on the left and a
`.ds-live-dot` "AI online" indicator + theme toggle on the right.

---

## 11. Chart language

`lib/chart-theme.ts` — one grammar for all Recharts surfaces: hairline
`3 3` grid (horizontal only), no axis lines, 10px muted tick labels, a single
elevated tooltip (`--background-elevated`, radius 12, `--shadow-md`). Series
colours come from `chartSeries` (brand first, then accent, then violet) —
never a rainbow. Radial gauges use brand with a `--surface-muted` track.

---

## 12. Doing a redesign

1. Page opens with `<PageHeader>`.
2. Content is `<Section>` blocks (`eyebrow` + `text-h3` title).
3. Numbers → `<Stat>` / `<StatGrid>`. Charts → `chart-theme` props.
4. Cards → `.ds-panel` (+ `.ds-panel-interactive` if clickable).
5. Wrap sections in `<Reveal delay={n}>` for the enter cascade.
6. Preserve every hook, query, route and handler — this is a visual layer
   over unchanged logic.
