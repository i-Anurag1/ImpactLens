"use client";
import { useMemo, useState } from "react";
import type { GraphQueryResult, SymbolRef } from "../lib/api";

const COLORS: Record<string, string> = {
  changed: "#E8763B",
  direct: "#6C7BFF",
  hidden: "#E8475B",
  test: "#3FBF7F",
};

export default function DependencyGraph({
  impact,
  changedSymbols,
}: {
  impact: GraphQueryResult;
  changedSymbols: string[];
}) {
  const [selected, setSelected] = useState<string | null>(changedSymbols[0] || null);

  const { positions, width, height } = useMemo(() => {
    const levelOf = (sym: string) => {
      if (changedSymbols.includes(sym)) return 0;
      const hiddenEdge = impact.edges.find(
        (e) => e.target.symbol === sym && e.confidence < 0.85
      );
      if (hiddenEdge) return 2;
      return 1;
    };
    const byLevel: Record<number, SymbolRef[]> = { 0: [], 1: [], 2: [] };
    impact.nodes.forEach((n) => {
      const lvl = levelOf(n.symbol);
      byLevel[lvl].push(n);
    });
    const colW = 260;
    const rowH = 90;
    const pos: Record<string, { x: number; y: number; level: number }> = {};
    Object.entries(byLevel).forEach(([lvlStr, nodes]) => {
      const lvl = Number(lvlStr);
      nodes.forEach((n, i) => {
        pos[n.symbol] = { x: 40 + lvl * colW, y: 40 + i * rowH, level: lvl };
      });
    });
    const maxRows = Math.max(1, byLevel[0].length, byLevel[1].length, byLevel[2].length);
    return { positions: pos, width: 40 + 3 * colW, height: 40 + maxRows * rowH };
  }, [impact, changedSymbols]);

  const selectedNode = impact.nodes.find((n) => n.symbol === selected);
  const selectedEdges = impact.edges.filter(
    (e) => e.source.symbol === selected || e.target.symbol === selected
  );

  const nodeColor = (sym: string) => {
    if (changedSymbols.includes(sym)) return COLORS.changed;
    const hidden = impact.edges.find((e) => e.target.symbol === sym && e.confidence < 0.85);
    return hidden ? COLORS.hidden : COLORS.direct;
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div className="xl:col-span-2 bg-ink-800 border border-ink-600 rounded-sm p-4 overflow-auto">
        <svg width={width} height={height} className="min-w-full">
          {impact.edges.map((e, i) => {
            const s = positions[e.source.symbol];
            const t = positions[e.target.symbol];
            if (!s || !t) return null;
            const isHidden = e.confidence < 0.85;
            return (
              <g key={i}>
                <line
                  x1={s.x + 90}
                  y1={s.y + 16}
                  x2={t.x}
                  y2={t.y + 16}
                  stroke={isHidden ? COLORS.hidden : "#2A3346"}
                  strokeWidth={isHidden ? 1.5 : 1}
                  strokeDasharray={isHidden ? "4 3" : undefined}
                />
              </g>
            );
          })}
          {impact.nodes.map((n) => {
            const p = positions[n.symbol];
            if (!p) return null;
            const isSel = n.symbol === selected;
            return (
              <g
                key={n.symbol}
                transform={`translate(${p.x}, ${p.y})`}
                className="cursor-pointer"
                onClick={() => setSelected(n.symbol)}
              >
                <rect
                  width={180}
                  height={40}
                  rx={4}
                  fill="#171E2C"
                  stroke={isSel ? "#E8ECF3" : nodeColor(n.symbol)}
                  strokeWidth={isSel ? 2 : 1.5}
                />
                <text x={10} y={17} fill="#E8ECF3" fontSize={11} fontFamily="IBM Plex Mono, monospace">
                  {n.symbol.length > 24 ? n.symbol.slice(0, 22) + "…" : n.symbol}
                </text>
                <text x={10} y={31} fill="#8B94A8" fontSize={9} fontFamily="IBM Plex Mono, monospace">
                  {n.file.split("/").pop()}:{n.line}
                </text>
              </g>
            );
          })}
        </svg>
        <div className="mt-3 flex gap-4 text-xs text-mist-500">
          <Legend color={COLORS.changed} label="Changed" />
          <Legend color={COLORS.direct} label="Direct dependency" />
          <Legend color={COLORS.hidden} label="Hidden / indirect (low confidence)" />
        </div>
      </div>

      <div className="bg-ink-800 border border-ink-600 rounded-sm p-4">
        <p className="text-mist-500 text-xs mb-2">Node evidence</p>
        {selectedNode ? (
          <div>
            <div className="font-mono text-sm text-mist-100">{selectedNode.symbol}</div>
            <div className="evidence-line text-mist-500 mb-3">
              {selectedNode.file}:{selectedNode.line} · {selectedNode.kind}
            </div>
            <p className="text-mist-500 text-xs mb-1">Relationships</p>
            <ul className="space-y-2">
              {selectedEdges.length === 0 && (
                <li className="text-mist-500 text-xs">No traced relationships for this node.</li>
              )}
              {selectedEdges.map((e, i) => {
                const other = e.source.symbol === selected ? e.target : e.source;
                const dir = e.source.symbol === selected ? "calls" : "called by";
                return (
                  <li key={i} className="border border-ink-600 rounded-sm p-2">
                    <div className="text-xs text-mist-300">
                      {dir} <span className="font-mono text-mist-100">{other.symbol}</span>
                    </div>
                    <div className="text-[11px] text-mist-500 mt-1">
                      confidence {Math.round(e.confidence * 100)}% · {e.evidence_note}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        ) : (
          <p className="text-mist-500 text-xs">Click a node to inspect its evidence.</p>
        )}
        <div className="mt-4 pt-4 border-t border-ink-600 text-[11px] text-mist-500">
          Source: {impact.source} · Entire Graph is heuristic — confidence {Math.round(impact.confidence * 100)}%.
          {impact.limitations.map((l, i) => (
            <p key={i} className="mt-1">{l}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="h-2 w-2 rounded-full inline-block" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}
