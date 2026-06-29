import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import type { DailyTrend } from "@/types";

interface ReadmissionChartProps {
  data: DailyTrend[];
  height?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const val = payload[0]?.value as number;
  const color = val >= 70 ? "#f43f5e" : val >= 40 ? "#f59e0b" : "#22c55e";
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 shadow-lg text-xs">
      <p className="font-semibold text-[var(--color-foreground)] mb-1">Day {label}</p>
      <p style={{ color }}>Readmission: <span className="font-bold">{val?.toFixed(1)}%</span></p>
    </div>
  );
};

export function ReadmissionChart({ data, height = 200 }: ReadmissionChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
        <defs>
          <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border-subtle)" vertical={false} />
        <XAxis
          dataKey="day"
          tick={{ fontSize: 11, fill: "var(--color-muted)" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--color-muted)" }}
          axisLine={false}
          tickLine={false}
          domain={[0, 100]}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={70} stroke="#f43f5e" strokeDasharray="4 2" strokeWidth={1.5} label={{ value: "High", position: "right", fontSize: 10, fill: "#f43f5e" }} />
        <ReferenceLine y={40} stroke="#f59e0b" strokeDasharray="4 2" strokeWidth={1.5} label={{ value: "Med", position: "right", fontSize: 10, fill: "#f59e0b" }} />
        <Line
          type="monotone"
          dataKey="readmission_probability"
          name="Readmission Risk"
          stroke="#f43f5e"
          strokeWidth={2.5}
          dot={false}
          activeDot={{ r: 5, fill: "#f43f5e" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
