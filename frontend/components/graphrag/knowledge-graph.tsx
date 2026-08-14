"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import type { ConceptEdgeOut, ConceptNodeOut, ConceptStatus } from "@/types/api";

const NODE_RADIUS = 20;
const ROW_HEIGHT = 84;
const COL_MIN_WIDTH = 168;
const COL_GAP = 46;
const TOP_PADDING = 46;
const BOTTOM_PADDING = 40;

const STATUS_COLOR: Record<ConceptStatus, string> = {
  strong: "var(--color-positive)",
  developing: "var(--color-warning)",
  weak: "var(--color-danger)",
  unknown: "var(--color-border-strong)",
};

const DOMAIN_ORDER = ["sql", "python", "javascript", "dsa", "oop", "java"];

interface PositionedNode extends ConceptNodeOut {
  x: number;
  y: number;
}

interface LayoutResult {
  positioned: PositionedNode[];
  width: number;
  height: number;
  domainBands: { slug: string; name: string; x: number; width: number }[];
}

function computeLayout(nodes: ConceptNodeOut[]): LayoutResult {
  const domainSlugs = Array.from(new Set(nodes.map((n) => n.domain_slug))).sort((a, b) => {
    const ai = DOMAIN_ORDER.indexOf(a);
    const bi = DOMAIN_ORDER.indexOf(b);
    if (ai === -1 && bi === -1) return a.localeCompare(b);
    if (ai === -1) return 1;
    if (bi === -1) return -1;
    return ai - bi;
  });

  const positioned: PositionedNode[] = [];
  const domainBands: LayoutResult["domainBands"] = [];
  let cursorX = 24;
  let maxDepthOverall = 0;

  for (const domainSlug of domainSlugs) {
    const domainNodes = nodes.filter((n) => n.domain_slug === domainSlug);
    const byDepth = new Map<number, ConceptNodeOut[]>();
    for (const n of domainNodes) {
      const list = byDepth.get(n.depth) ?? [];
      list.push(n);
      byDepth.set(n.depth, list);
    }
    const maxRowCount = Math.max(1, ...Array.from(byDepth.values()).map((l) => l.length));
    const colWidth = Math.max(COL_MIN_WIDTH, maxRowCount * 96);

    for (const [depth, rowNodes] of byDepth) {
      maxDepthOverall = Math.max(maxDepthOverall, depth);
      rowNodes.forEach((n, i) => {
        const slotWidth = colWidth / rowNodes.length;
        positioned.push({
          ...n,
          x: cursorX + slotWidth * (i + 0.5),
          y: TOP_PADDING + depth * ROW_HEIGHT,
        });
      });
    }

    domainBands.push({
      slug: domainSlug,
      name: domainNodes[0]?.domain_name ?? domainSlug,
      x: cursorX,
      width: colWidth,
    });
    cursorX += colWidth + COL_GAP;
  }

  return {
    positioned,
    width: cursorX,
    height: TOP_PADDING + (maxDepthOverall + 1) * ROW_HEIGHT + BOTTOM_PADDING,
    domainBands,
  };
}

interface KnowledgeGraphProps {
  nodes: ConceptNodeOut[];
  edges: ConceptEdgeOut[];
  selectedSlug: string | null;
  onSelectNode: (slug: string) => void;
}

export function KnowledgeGraph({ nodes, edges, selectedSlug, onSelectNode }: KnowledgeGraphProps) {
  const layout = useMemo(() => computeLayout(nodes), [nodes]);
  const posBySlug = useMemo(() => new Map(layout.positioned.map((n) => [n.slug, n])), [layout.positioned]);

  return (
    <div className="overflow-x-auto rounded-[var(--radius-lg)] border border-border bg-surface-muted/40">
      <svg width={layout.width} height={layout.height} role="img" aria-label="Your knowledge graph, colored by mastery">
        <defs>
          <marker id="kg-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--color-border-strong)" />
          </marker>
        </defs>

        {layout.domainBands.map((band) => (
          <g key={band.slug}>
            <rect
              x={band.x - 10}
              y={8}
              width={band.width + 20}
              height={layout.height - 16}
              rx={14}
              fill="var(--color-surface)"
              stroke="var(--color-border)"
              strokeWidth={1}
            />
            <text x={band.x + band.width / 2} y={26} textAnchor="middle" fontSize={11} fontWeight={700} fill="var(--color-muted)">
              {band.name.toUpperCase()}
            </text>
          </g>
        ))}

        {edges.map((edge, i) => {
          const source = posBySlug.get(edge.source);
          const target = posBySlug.get(edge.target);
          if (!source || !target) return null;
          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const dist = Math.hypot(dx, dy) || 1;
          const x1 = source.x + (dx / dist) * NODE_RADIUS;
          const y1 = source.y + (dy / dist) * NODE_RADIUS;
          const x2 = target.x - (dx / dist) * (NODE_RADIUS + 7);
          const y2 = target.y - (dy / dist) * (NODE_RADIUS + 7);
          const isHighlighted = selectedSlug === edge.source || selectedSlug === edge.target;
          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={isHighlighted ? "var(--color-brand)" : "var(--color-border-strong)"}
              strokeWidth={isHighlighted ? 2 : 1.25}
              opacity={isHighlighted ? 0.9 : 0.5}
              markerEnd="url(#kg-arrow)"
            />
          );
        })}

        {layout.positioned.map((node, i) => {
          const isSelected = selectedSlug === node.slug;
          const color = STATUS_COLOR[node.status];
          return (
            <g
              key={node.slug}
              className="cursor-pointer"
              style={{ animation: `kg-fade-in 420ms ease both`, animationDelay: `${Math.min(i * 12, 400)}ms` }}
              onClick={() => onSelectNode(node.slug)}
              role="button"
              tabIndex={0}
              aria-label={`${node.name}: ${node.status}${node.mastery !== null ? `, ${Math.round(node.mastery * 100)}% mastery` : ""}`}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") onSelectNode(node.slug);
              }}
            >
              <title>
                {node.name} -- {node.status}
                {node.mastery !== null ? ` (${Math.round(node.mastery * 100)}%)` : " (not yet assessed)"}
              </title>
              {node.is_target_role_relevant && (
                <circle cx={node.x} cy={node.y} r={NODE_RADIUS + 5} fill="none" stroke="var(--color-brand)" strokeWidth={1.5} strokeDasharray="2 3" opacity={0.8} />
              )}
              {isSelected && (
                <circle cx={node.x} cy={node.y} r={NODE_RADIUS + 8} fill="none" stroke="var(--color-brand)" strokeWidth={2} className="animate-pulse-glow" />
              )}
              <circle
                cx={node.x}
                cy={node.y}
                r={NODE_RADIUS}
                fill={node.status === "unknown" ? "var(--color-surface)" : color}
                fillOpacity={node.status === "unknown" ? 1 : 0.18}
                stroke={color}
                strokeWidth={isSelected ? 3 : 2}
              />
              <circle cx={node.x} cy={node.y} r={5.5} fill={color} />
              <text
                x={node.x}
                y={node.y + NODE_RADIUS + 15}
                textAnchor="middle"
                fontSize={10.5}
                fontWeight={isSelected ? 700 : 500}
                fill={isSelected ? "var(--color-foreground)" : "var(--color-muted)"}
              >
                {node.name.length > 16 ? `${node.name.slice(0, 15)}…` : node.name}
              </text>
            </g>
          );
        })}
      </svg>
      <style>{`
        @keyframes kg-fade-in {
          from { opacity: 0; transform: scale(0.85); }
          to { opacity: 1; transform: scale(1); }
        }
        svg g { transform-origin: center; }
      `}</style>
    </div>
  );
}

export function KnowledgeGraphLegend() {
  const items: { status: ConceptStatus; label: string }[] = [
    { status: "strong", label: "Strong" },
    { status: "developing", label: "Developing" },
    { status: "weak", label: "Needs work" },
    { status: "unknown", label: "Not assessed yet" },
  ];
  return (
    <div className="flex flex-wrap items-center gap-3 text-[11px] text-muted">
      {items.map((item) => (
        <span key={item.status} className="flex items-center gap-1.5">
          <span
            className={cn("h-2.5 w-2.5 rounded-full", item.status === "unknown" && "border")}
            style={{
              background: item.status === "unknown" ? "transparent" : STATUS_COLOR[item.status],
              borderColor: item.status === "unknown" ? STATUS_COLOR[item.status] : undefined,
            }}
          />
          {item.label}
        </span>
      ))}
      <span className="flex items-center gap-1.5">
        <span className="h-2.5 w-2.5 rounded-full border border-dashed border-brand" />
        Relevant to your target role
      </span>
    </div>
  );
}
