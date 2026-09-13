/**
 * Chart language — one visual grammar for every Recharts surface so
 * analytics read as one system (Tremor-influenced): hairline grid, muted
 * small-caps axes, a single elevated tooltip, brand as the primary series.
 *
 * Usage:
 *   <CartesianGrid {...chartGrid} />
 *   <XAxis {...chartAxis} />
 *   <Tooltip {...chartTooltip} />
 */

export const chartColors = {
  primary: "var(--color-brand)",
  secondary: "var(--color-accent-2)",
  tertiary: "var(--color-brand-2)",
  positive: "var(--color-positive)",
  warning: "var(--color-warning)",
  danger: "var(--color-danger)",
  grid: "var(--color-border)",
  axis: "var(--color-muted)",
} as const;

/** Ordered categorical palette — never a rainbow, always brand-anchored. */
export const chartSeries = [
  chartColors.primary,
  chartColors.secondary,
  chartColors.tertiary,
  chartColors.positive,
  chartColors.warning,
];

export const chartGrid = {
  strokeDasharray: "3 3",
  stroke: chartColors.grid,
  vertical: false as const,
};

export const chartAxis = {
  tick: { fill: chartColors.axis, fontSize: 10 },
  tickLine: false as const,
  axisLine: false as const,
};

export const chartTooltip = {
  cursor: { stroke: chartColors.grid, strokeWidth: 1 },
  contentStyle: {
    background: "var(--color-background-elevated)",
    border: "1px solid var(--color-border)",
    borderRadius: 12,
    boxShadow: "var(--shadow-md)",
    fontSize: 12,
    padding: "8px 10px",
  },
  labelStyle: { color: "var(--color-muted)", fontSize: 10, marginBottom: 2 },
};
