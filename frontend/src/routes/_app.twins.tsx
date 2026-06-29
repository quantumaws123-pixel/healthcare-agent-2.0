import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "framer-motion";
import { Brain, Activity, TrendingUp, TrendingDown, ArrowRightLeft } from "lucide-react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { SearchBar } from "@/components/ui/SearchBar";

export const Route = createFileRoute("/_app/twins")({
  component: DigitalTwinsPage,
});

function DigitalTwinsPage() {
  const [selected, setSelected] = useState("HDT-AHD-2026-501118");

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <motion.div variants={staggerItem}>
        <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">Digital Twins</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">Ideal vs Real recovery comparison engine</p>
      </motion.div>

      {/* Patient selector */}
      <motion.div variants={staggerItem} className="w-64">
        <SearchBar placeholder="Search patient…" />
      </motion.div>

      {/* Twin comparison cards */}
      <motion.div variants={staggerItem} className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Ideal Twin */}
        <Card className="border-t-4 border-[var(--color-primary-500)]">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-[var(--color-primary-50)] flex items-center justify-center">
                <Brain size={16} className="text-[var(--color-primary-500)]" />
              </div>
              <div>
                <CardTitle>Ideal Digital Twin</CardTitle>
                <CardDescription>Doctor's prescribed recovery plan</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {IDEAL_TWIN.map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm text-[var(--color-muted)]">{item.label}</span>
                <span className="text-sm font-semibold text-[var(--color-foreground)]">{item.value}</span>
              </div>
            ))}
            <div className="pt-2 mt-2 border-t border-[var(--color-border-subtle)]">
              <p className="text-xs font-semibold text-[var(--color-muted)] mb-2 uppercase tracking-wide">Expected Health Score</p>
              <ProgressBar value={87.5} showValue color="var(--color-primary-500)" />
            </div>
          </CardContent>
        </Card>

        {/* Real Twin */}
        <Card className="border-t-4 border-[var(--color-danger-400)]">
          <CardHeader>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-[var(--color-danger-50)] flex items-center justify-center">
                <Activity size={16} className="text-[var(--color-danger-500)]" />
              </div>
              <div>
                <CardTitle>Real Digital Twin</CardTitle>
                <CardDescription>Actual patient behaviour & vitals</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {REAL_TWIN.map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm text-[var(--color-muted)]">{item.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-[var(--color-foreground)]">{item.value}</span>
                  {item.delta && (
                    <Badge variant={item.deltaPositive ? "success" : "danger"} size="sm">
                      {item.deltaPositive ? "↑" : "↓"} {item.delta}
                    </Badge>
                  )}
                </div>
              </div>
            ))}
            <div className="pt-2 mt-2 border-t border-[var(--color-border-subtle)]">
              <p className="text-xs font-semibold text-[var(--color-muted)] mb-2 uppercase tracking-wide">Real Health Score</p>
              <ProgressBar value={66.6} showValue color="var(--color-danger-500)" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Deviation summary */}
      <motion.div variants={staggerItem}>
        <Card className="bg-gradient-to-r from-[var(--color-primary-50)] to-[var(--color-danger-50)]">
          <CardContent className="pt-5 flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <ArrowRightLeft size={20} className="text-[var(--color-muted)]" />
              <div>
                <p className="text-sm font-semibold text-[var(--color-foreground)]">Deviation Score: 20.9</p>
                <p className="text-xs text-[var(--color-muted)]">Ideal − Real health score gap on Day 30</p>
              </div>
            </div>
            <Badge variant="warning" size="md">Compliance Score: 64.5%</Badge>
          </CardContent>
        </Card>
      </motion.div>

      {/* Radar chart */}
      <motion.div variants={staggerItem}>
        <Card>
          <CardHeader>
            <CardTitle>Twin Comparison Radar</CardTitle>
            <CardDescription>Multi-dimensional adherence vs prescription</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={RADAR_DATA}>
                <PolarGrid />
                <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11 }} />
                <Radar name="Ideal" dataKey="ideal" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} />
                <Radar name="Real" dataKey="real" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.15} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </motion.div>

      {/* Trend comparison */}
      <motion.div variants={staggerItem}>
        <Card>
          <CardHeader>
            <CardTitle>30-Day Health Score Divergence</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={TWIN_TREND}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis domain={[40, 100]} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                <Legend />
                <Area type="monotone" dataKey="ideal" name="Ideal Twin" stroke="#3b82f6" fill="#3b82f620" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="real" name="Real Twin" stroke="#f43f5e" fill="#f43f5e20" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}

const IDEAL_TWIN = [
  { label: "Expected Steps/day", value: "7,500" },
  { label: "Expected Sleep", value: "7.8 hrs" },
  { label: "Water Intake Goal", value: "2.5 L" },
  { label: "Medication", value: "Salbutamol 200mcg" },
  { label: "Exercise Plan", value: "Controlled aerobic" },
  { label: "Diet", value: "Anti-inflammatory" },
];

const REAL_TWIN = [
  { label: "Actual Steps/day", value: "3,120", delta: "58%", deltaPositive: false },
  { label: "Actual Sleep", value: "8.0 hrs", delta: "3%", deltaPositive: true },
  { label: "Water Intake", value: "1.9 L", delta: "24%", deltaPositive: false },
  { label: "Medication Taken", value: "Yes", delta: null, deltaPositive: true },
  { label: "Exercise Completed", value: "No", delta: null, deltaPositive: false },
  { label: "Diet Compliance", value: "64.5%", delta: "23%", deltaPositive: false },
];

const RADAR_DATA = [
  { axis: "Steps", ideal: 100, real: 52 },
  { axis: "Sleep", ideal: 100, real: 103 },
  { axis: "Water", ideal: 100, real: 76 },
  { axis: "Medication", ideal: 100, real: 83 },
  { axis: "Exercise", ideal: 100, real: 38 },
  { axis: "Diet", ideal: 100, real: 65 },
];

const TWIN_TREND = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  ideal: 81 + i * 0.2,
  real: 66 - i * 0.05 + Math.sin(i * 0.5) * 3,
}));
