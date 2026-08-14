# Projector Visual Audit

Status tracker for the CLAUDE.md "projector-first visual validation"
requirement (1920×1080, 1366×768, 1512×795, 100%/125% zoom, dark/light
theme, fullscreen Competition Mode). Updated honestly at each pass — see
inline notes for what's real vs. still outstanding.

## What the type system already guarantees (verified by source, not screenshot)

Every page built or redesigned across both visual passes uses the
`clamp()`-based scale in `frontend/app/globals.css` (`text-h1`,
`text-h2`, `text-h3`, `text-projector`, `text-projector-lg`,
`text-metric`, `text-metric-lg`) rather than fixed pixel sizes — this
means headline and metric text mathematically scales between mobile and
projector widths without a separate breakpoint, by construction, not by
per-page tuning. Competition Mode specifically uses `text-projector*`
throughout for exactly this reason.

## Live-verified this pass (2026-08-05, premium visual transformation pass)

Verified in a real browser against the Docker stack at this environment's
fixed browser-automation viewport (1512×795, the closest of the four
target resolutions to what was actually testable here):

| Screen | Dark theme | Notes |
|---|---|---|
| `/graphrag` empty state | ✅ | Centered empty-state card, readable at viewport width |
| `/graphrag` root-cause reveal | ✅ | Node chain, badges, and technical-view toggle all legible; no horizontal overflow |
| `/interview` mode selection | ✅ | 3-column grid readable, no crowding |
| `/interview/[id]` question + evaluation | ✅ | Dimension-score grid and strengths/improvements columns readable |
| `/trust-center` execution timeline | ✅ | New timeline component readable at this width |
| `/research-lab` general/technical toggle | ✅ | Toggle buttons and calibration bars legible |
| `/experiment-lab` scenario reveal | ✅ | Current/simulated/confidence-range triad readable |
| `/responsible-ai` evaluates/does-not-evaluate | ✅ | Two-column grid legible |
| `/competition` opening + GraphRAG slide | ✅ | Large projector-scale type confirmed via `text-projector-lg`/`text-projector` classes rendering correctly |

## Not verified this pass — stated honestly

- **1920×1080, 1366×768 exact-resolution testing**: this environment's
  browser automation tool renders at a fixed viewport
  (1512×795) and its window-resize call was confirmed in the prior pass
  not to change the actual CSS viewport (`window.innerWidth` stayed
  constant after a resize request) — a tooling limitation, not a skipped
  step. **MANUAL ACTION REQUIRED**: re-check at the exact venue
  resolution on the actual presentation laptop before presenting.
- **100%/125% browser zoom**: not tested this pass. The `clamp()`-based
  type scale should respond correctly to zoom (it's relative to viewport
  width, and browser zoom effectively changes the CSS viewport), but this
  is a reasoned expectation from the CSS, not a verified observation.
- **Light theme at projector resolution**: light-theme tokens exist and
  were spot-checked in normal browsing, but no dedicated light-theme
  projector-width screenshot was captured this pass.
- **Fullscreen Competition Mode specifically** (as opposed to the
  windowed view used for verification above): the fullscreen API call
  (`document.documentElement.requestFullscreen()`) was not exercised via
  browser automation this pass — Competition Mode's non-fullscreen
  rendering was verified instead.
- **Content-below-the-fold, modal height, chart-label crowding** at the
  three named resolutions specifically: not systematically re-checked
  this pass beyond the general no-horizontal-overflow observation above.

## Recommendation before a live event

Run a 10-minute manual pass on the actual presentation laptop: open
Competition Mode fullscreen at the venue's real resolution, click through
all 14 steps once at 100% zoom and once at 125%, in both themes if the
venue lighting is uncertain. This audit's live-verified rows give
reasonable confidence nothing is fundamentally broken, but they are not a
substitute for that final on-hardware check.
