import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  ChevronLeft, Activity, Heart, Droplets, Footprints,
  Moon, Pill, TrendingUp, TrendingDown, AlertTriangle, Brain
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, AreaChart, Area, Legend,
} from "recharts";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Avatar } from "@/components/ui/Avatar";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { RiskBadge, RecoveryBadge, TrendBadge } from "@/components/ui/StatusBadge";
import { Tabs, TabList, TabTrigger, TabPanels, TabPanel } from "@/components/ui/Tabs";
import { FloatingPanel } from "@/components/ui/FloatingPanel";
import type { RiskLevel, RecoveryStatus, HealthTrend } from "@/types";

export const Route = createFileRoute("/_app/patients/$patientId")({
  component: PatientDetailPage,
});

function PatientDetailPage() {
  const { patientId } = Route.useParams();
  const patient = MOCK_DETAIL;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Breadcrumb + header */}
      <motion.div variants={staggerItem} className="flex items-start gap-4 flex-wrap">
        <Link to="/patients">
          <Button variant="ghost" size="sm" leftIcon={<ChevronLeft size={14} />}>
            Patients
          </Button>
        </Link>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <Avatar name={patientId} size="lg" />
            <div>
              <h1 className="text-xl font-bold text-[var(--color-foreground)] tracking-tight truncate">
                {patientId}
              </h1>
              <p className="text-sm text-[var(--color-muted)]">
                {patient.age}y · {patient.gender} · {patient.disease}
              </p>
            </div>
            <RiskBadge level={patient.risk as RiskLevel} />
            <RecoveryBadge status={patient.recovery as RecoveryStatus} />
            <TrendBadge trend={patient.trend as HealthTrend} />
          </div>
        </div>
      </motion.div>

      {/* KPI strip */}
      <motion.div variants={staggerItem} className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard icon={<Activity size={16} />} label="Readmission Risk" value={`${patient.readmission}%`} color="danger" />
        <StatCard icon={<TrendingUp size={16} />} label="Compliance Score" value={`${patient.compliance}%`} color="primary" />
        <StatCard icon={<Heart size={16} />} label="Recovery Score" value={`${patient.recovery_score}%`} color="success" />
        <StatCard icon={<Brain size={16} />} label="Deviation Score" value={`${patient.deviation}`} color="warning" />
      </motion.div>

      {/* AI Recommendation panel */}
      <motion.div variants={staggerItem}>
        <FloatingPanel title="AI Recommendation" className="border-l-4 border-[var(--color-primary-500)]">
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <p className="text-sm font-semibold text-[var(--color-foreground)]">{patient.recommendation}</p>
              <p className="text-xs text-[var(--color-muted)] mt-1">
                Based on Day {patient.latest_day} data · Confidence: High
              </p>
            </div>
            <div className="space-y-2 hidden sm:block">
              <p className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">Top SHAP Features</p>
              {SHAP_FEATURES.map((f) => (
                <div key={f.feature} className="flex items-center gap-2">
                  <span className="text-xs text-[var(--color-foreground)] w-36 truncate">{f.feature}</span>
                  <div className="w-24 h-1.5 rounded-full bg-[var(--color-border-subtle)] overflow-hidden">
                    <div
                      className={`h-full rounded-full ${f.direction === "positive" ? "bg-[var(--color-success-500)]" : "bg-[var(--color-danger-500)]"}`}
                      style={{ width: `${Math.abs(f.value) * 100}%` }}
                    />
                  </div>
                  <span className={`text-xs font-semibold tabular-nums ${f.direction === "positive" ? "text-[var(--color-success-600)]" : "text-[var(--color-danger-600)]"}`}>
                    {f.direction === "positive" ? "+" : "-"}{(Math.abs(f.value) * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </FloatingPanel>
      </motion.div>

      {/* Tabs */}
      <motion.div variants={staggerItem}>
        <Tabs defaultTab="trends" variant="line">
          <TabList>
            <TabTrigger id="trends" icon={<Activity size={14} />}>Trends</TabTrigger>
            <TabTrigger id="vitals" icon={<Heart size={14} />}>Vitals</TabTrigger>
            <TabTrigger id="compliance" icon={<TrendingUp size={14} />}>Compliance</TabTrigger>
            <TabTrigger id="twin" icon={<Brain size={14} />}>Digital Twin</TabTrigger>
          </TabList>
          <TabPanels>
            {/* Trends */}
            <TabPanel id="trends">
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mt-4">
                <Card>
                  <CardHeader><CardTitle>Recovery Score over 30 Days</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={TREND_DATA}>
                        <defs>
                          <linearGradient id="recovGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid var(--color-border)", fontSize: 12 }} />
                        <Area type="monotone" dataKey="recovery" stroke="#3b82f6" fill="url(#recovGrad)" strokeWidth={2} dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader><CardTitle>Readmission Probability over 30 Days</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={TREND_DATA}>
                        <defs>
                          <linearGradient id="readGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid var(--color-border)", fontSize: 12 }} />
                        <Area type="monotone" dataKey="readmission" stroke="#f43f5e" fill="url(#readGrad)" strokeWidth={2} dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card className="lg:col-span-2">
                  <CardHeader><CardTitle>Compliance Score over 30 Days</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={180}>
                      <LineChart data={TREND_DATA}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid var(--color-border)", fontSize: 12 }} />
                        <Line type="monotone" dataKey="compliance" stroke="#22c55e" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabPanel>

            {/* Vitals */}
            <TabPanel id="vitals">
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 mt-4">
                {VITALS.map((v) => (
                  <Card key={v.label} className="text-center">
                    <CardContent className="pt-5">
                      <div className="flex justify-center mb-2 text-[var(--color-primary-500)]">{v.icon}</div>
                      <p className="text-2xl font-bold text-[var(--color-foreground)] tabular-nums">{v.value}</p>
                      <p className="text-xs text-[var(--color-muted)] mt-1">{v.label}</p>
                      <p className="text-[10px] text-[var(--color-muted-foreground)] mt-0.5">{v.unit}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabPanel>

            {/* Compliance */}
            <TabPanel id="compliance">
              <div className="space-y-4 mt-4">
                <Card>
                  <CardHeader><CardTitle>Adherence Breakdown</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    {COMPLIANCE_ITEMS.map((c) => (
                      <ProgressBar key={c.label} label={c.label} value={c.value} showValue color={c.color} />
                    ))}
                  </CardContent>
                </Card>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <Card className="text-center">
                    <CardContent className="pt-4 pb-4">
                      <p className="text-2xl font-bold text-[var(--color-foreground)]">{patient.missed_medication}</p>
                      <p className="text-xs text-[var(--color-muted)] mt-1">Missed Medications</p>
                    </CardContent>
                  </Card>
                  <Card className="text-center">
                    <CardContent className="pt-4 pb-4">
                      <p className="text-2xl font-bold text-[var(--color-foreground)]">{patient.missed_exercise}</p>
                      <p className="text-xs text-[var(--color-muted)] mt-1">Missed Exercise Days</p>
                    </CardContent>
                  </Card>
                  <Card className="text-center col-span-2">
                    <CardContent className="pt-4 pb-4 flex items-center justify-center gap-4">
                      <ProgressRing value={patient.compliance} size={72} strokeWidth={6} />
                      <div>
                        <p className="text-sm font-semibold text-[var(--color-foreground)]">Overall Compliance</p>
                        <p className="text-xs text-[var(--color-muted)]">Day {patient.latest_day} cumulative</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabPanel>

            {/* Digital Twin */}
            <TabPanel id="twin">
              <div className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Ideal vs Real Twin Comparison</CardTitle>
                    <CardDescription>Health score divergence over monitoring period</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={240}>
                      <AreaChart data={TREND_DATA}>
                        <defs>
                          <linearGradient id="idealGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                          </linearGradient>
                          <linearGradient id="realGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.15} />
                            <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid var(--color-border)", fontSize: 12 }} />
                        <Legend />
                        <Area type="monotone" dataKey="ideal" name="Ideal Twin" stroke="#3b82f6" fill="url(#idealGrad)" strokeWidth={2} dot={false} />
                        <Area type="monotone" dataKey="real" name="Real Twin" stroke="#f43f5e" fill="url(#realGrad)" strokeWidth={2} dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </motion.div>
    </motion.div>
  );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  const colors: Record<string, string> = {
    danger: "text-[var(--color-danger-500)] bg-[var(--color-danger-50)]",
    primary: "text-[var(--color-primary-600)] bg-[var(--color-primary-50)]",
    success: "text-[var(--color-success-600)] bg-[var(--color-success-50)]",
    warning: "text-[var(--color-warning-600)] bg-[var(--color-warning-50)]",
  };
  return (
    <Card className="text-center">
      <CardContent className="pt-5 pb-4">
        <div className={`inline-flex items-center justify-center w-8 h-8 rounded-xl mb-2 ${colors[color]}`}>{icon}</div>
        <p className="text-xl font-bold text-[var(--color-foreground)] tabular-nums">{value}</p>
        <p className="text-xs text-[var(--color-muted)] mt-0.5">{label}</p>
      </CardContent>
    </Card>
  );
}

/* ── Mock data ──────────────────────────────────────────────────────────── */
const MOCK_DETAIL = {
  age: 53, gender: "Male", disease: "Asthma", risk: "High", recovery: "Delayed Recovery",
  trend: "Stable", readmission: 44.3, compliance: 64.5, recovery_score: 68.9,
  deviation: 20.9, recommendation: "Increase Monitoring — Missed 5 consecutive exercise sessions. Compliance declining over last 7 days.",
  latest_day: 30, missed_medication: 5, missed_exercise: 13,
};

const SHAP_FEATURES = [
  { feature: "Compliance_Score", value: 0.42, direction: "negative" },
  { feature: "Missed_Exercise_Count", value: 0.31, direction: "negative" },
  { feature: "SpO2", value: 0.18, direction: "positive" },
];

const TREND_DATA = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  recovery: 69 + Math.sin(i * 0.4) * 8 + i * 0.1,
  compliance: 77 - i * 0.4 + Math.sin(i * 0.5) * 5,
  readmission: 32 + i * 0.4 + Math.cos(i * 0.3) * 6,
  ideal: 82 + i * 0.15,
  real: 65 - i * 0.1 + Math.sin(i * 0.6) * 4,
}));

const VITALS = [
  { label: "Heart Rate", value: "94", unit: "bpm", icon: <Heart size={20} /> },
  { label: "Systolic BP", value: "129", unit: "mmHg", icon: <Activity size={20} /> },
  { label: "SpO₂", value: "95.8", unit: "%", icon: <Droplets size={20} /> },
  { label: "Steps Today", value: "3,120", unit: "steps", icon: <Footprints size={20} /> },
  { label: "Sleep", value: "7.8", unit: "hours", icon: <Moon size={20} /> },
  { label: "Medication", value: "Yes", unit: "taken today", icon: <Pill size={20} /> },
];

const COMPLIANCE_ITEMS = [
  { label: "Medication Adherence", value: 83, color: "var(--color-primary-500)" },
  { label: "Steps Compliance", value: 52, color: "var(--color-warning-500)" },
  { label: "Sleep Target", value: 91, color: "var(--color-success-500)" },
  { label: "Water Intake", value: 72, color: "var(--color-info-500)" },
  { label: "Exercise Completion", value: 38, color: "var(--color-danger-500)" },
  { label: "Diet Compliance", value: 67, color: "var(--color-primary-400)" },
];

import React from "react";
