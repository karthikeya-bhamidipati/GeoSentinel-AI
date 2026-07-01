"use client";

// =============================================================================
// GeoSentinel AI — Change Chart
// =============================================================================

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { AreaStatRow } from "@/types";
import { LAND_COVER_CLASSES } from "@/types";

interface ChangeChartProps {
  rows: AreaStatRow[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const value = payload[0].value as number;
    return (
      <div
        style={{
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-sm)",
          padding: "8px 12px",
          fontSize: "0.75rem",
        }}
      >
        <div
          style={{ fontWeight: 600, marginBottom: 4, color: "var(--color-text)" }}
        >
          {label}
        </div>
        <div style={{ color: value >= 0 ? "var(--color-green)" : "var(--color-red)" }}>
          {value >= 0 ? "+" : ""}{value.toFixed(2)} km²
        </div>
      </div>
    );
  }
  return null;
};

export function ChangeChart({ rows }: ChangeChartProps) {
  const data = rows
    .filter((r) => r.class_id > 0) // Skip background
    .map((r) => ({
      name: r.class_name,
      change: parseFloat(r.change_km2.toFixed(3)),
      color:
        LAND_COVER_CLASSES[r.class_id]?.color ?? "#64748b",
    }));

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 4 }}>
        <XAxis
          dataKey="name"
          tick={{ fontSize: 10, fill: "var(--color-text-muted)" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: "var(--color-text-muted)" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={0} stroke="var(--color-border)" />
        <Bar dataKey="change" radius={[3, 3, 0, 0]}>
          {data.map((entry, i) => (
            <Cell
              key={`cell-${i}`}
              fill={entry.change >= 0 ? "var(--color-green)" : "var(--color-red)"}
              opacity={0.85}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
