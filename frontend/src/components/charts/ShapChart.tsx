import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { ShapFeature } from "@/types";

interface ShapChartProps {
  features: ShapFeature[];
  height?: number;
}

export function ShapChart({ features, height = 180 }: ShapChartProps) {
  const data = [...features]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, 8)
    .map((f) => ({
      feature: f.feature.replace(/_/g, " "),
      value: Math.abs(f.shap_value),
      raw: f.shap_value,
      direction: f.direction,
    }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <XAxis type="number" tick={{ fontSize: 10, fill: "var(--color-muted)" }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="feature"
          width={130}
          tick={{ fontSize: 10, fill: "var(--color-muted)" }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          formatter={(v: any, _: any, props: any) => [
            `${props.payload.raw > 0 ? "+" : ""}${props.payload.raw.toFixed(3)}`,
            "SHAP",
          ]}
          contentStyle={{
            fontSize: 11,
            borderRadius: 12,
            border: "1px solid var(--color-border)",
            background: "var(--color-surface)",
          }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.map((d, i) => (
            <Cell
              key={i}
              fill={d.direction === "positive" ? "#f43f5e" : "#22c55e"}
              fillOpacity={0.85}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
