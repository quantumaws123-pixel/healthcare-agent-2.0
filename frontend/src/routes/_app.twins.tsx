import React, { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Brain, Activity, ArrowRightLeft } from "lucide-react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { SearchBar } from "@/components/ui/SearchBar";
import { RiskBadge, RecoveryBadge, TrendBadge } from "@/components/ui/StatusBadge";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { usePatients, usePatientSummary } from "@/hooks/usePatients";
import type { RiskLevel, RecoveryStatus, HealthTrend } from "@/types";

export const Route = createFileRoute("/_app/twins")({
  component: DigitalTwinsPage,
});

function DigitalTwinsPage() {
  const [search, setSearch]     = useState("");
  const [selectedId, setSelected] = useState<string | null>(null);

  // Load high-risk patients as the default list to pick from
  const { data: patientsData, isLoading: patientsLoading } = usePatients({
    page_size: 20,
  });

  const patientList = patientsData?.data ?? [];

  // Filter list by search
  const filtered = search
    ? patientList.filter(p => p.Patient_ID.toLowerCase().includes(search.toLowerCase()))
    : patientList;

  // Auto-select first patient when list loads and none selected yet
  const effectiveId = selectedId ?? filtered[0]?.Patient_ID ?? null;

  // Load 30-day trend for the selected patient
  const { data: summaryData, isLoading: summaryLoading } = usePatientSummary(effectiveId ?? "");

  const trends      = summaryData?.daily_trends ?? [];
  const latest      = trends[trends.length - 1];
  const first       = trends[0];

  // Chart data
  const chartData = trends.map(t => ({
    day:   t.day,
    ideal: Math.round(t.ideal_health_score * 10) / 10,
    real:  Math.round(t.real_health_score  * 10) / 10,
  }));

  // Radar data: compare score components on latest day vs ideal (100)
  const radarData = latest
    ? [
        { axis: "Recovery",    ideal: 100, real: Math.round(latest.recovery_score) },
        { axis: "Compliance",  ideal: 100, real: Math.round(latest.compliance_score) },
        { axis: "Health",      ideal: Math.round(latest.ideal_health_score), real: Math.round(latest.real_health_score) },
        { axis: "Low Deviation", ideal: 100, real: Math.max(0, Math.round(100 - latest.deviation_score)) },
        { axis: "Low Readmission", ideal: 100, real: Math.round((1 - latest.readmission_probability) * 100) },
      ]
    : [];

  const selectedPatient = patientList.find(p => p.Patient_ID === effectiveId);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <motion.div variants={staggerItem}>
        <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">Digital Twins</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Ideal vs Real recovery comparison — select any patient below
        </p>
      </motion.div>

      {/* Patient selector */}
      <motion.div variants={staggerItem} className="space-y-3">
        <div className="w-72">
          <SearchBar
            placeholder="Search patient ID…"
            value={search}
            onChange={setSearch}
          />
        </div>
        {/* Patient picker */}
        {patientsLoading ? (
          <div className="flex gap-2 flex-wrap">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-8 w-40 rounded-xl bg-gray-200 dark:bg-gray-700 animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="flex gap-2 flex-wrap">
            {filtered.slice(0, 10).map(p => (
              <button
                key={p.Patient_ID}
                onClick={() => setSelected(p.Patient_ID)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
                  p.Patient_ID === effectiveId
                    ? "bg-[var(--color-primary-500)] text-white border-[var(--color-primary-500)]"
                    : "bg-[var(--color-surface)] text-[var(--color-foreground)] border-[var(--color-border)] hover:border-[var(--color-primary-400)]"
                }`}
              >
                {p.Patient_ID.split("-").slice(-1)[0]}
              </button>
            ))}
            {filtered.length > 10 && (
              <span className="px-3 py-1.5 text-xs text-[var(--color-muted)]">
                +{filtered.length - 10} more
              </span>
            )}
          </div>
        )}
      </motion.div>

      {/* Selected patient header */}
      {selectedPatient && (
        <motion.div variants={staggerItem}>
          <Card className="bg-gradient-to-r from-[var(--color-primary-50)] to-transparent dark:from-[var(--color-primary-900)]/20">
            <CardContent className="pt-4 flex items-center gap-4 flex-wrap">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-[var(--color-foreground)] truncate">
                  {selectedPatient.Patient_ID}
                </p>
                <p className="text-xs text-[var(--color-muted)]">
                  {selectedPatient.Disease_Type} · {selectedPatient.Age}y · Day {selectedPatient.Latest_Day}
                </p>
              </div>
              <RiskBadge level={selectedPatient.Risk_Level as RiskLevel} />
              <RecoveryBadge status={selectedPatient.Recovery_Status as RecoveryStatus} />
              {latest && <TrendBadge trend={latest.health_trend as HealthTrend} />}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {summaryLoading ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <SkeletonCard /><SkeletonCard />
        </div>
      ) : !latest ? (
        <EmptyState
          title="Select a patient"
          description="Click any patient above to load their Digital Twin comparison."
          size="md"
          className="py-16"
        />
      ) : (
        <>
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
                    <CardDescription>Doctor's prescribed target</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { label: "Ideal Health Score (Day 1)",    value: first?.ideal_health_score.toFixed(1) ?? "—" },
                  { label: "Ideal Health Score (Latest)",   value: latest.ideal_health_score.toFixed(1) },
                  { label: "Target Recovery Score",         value: "100.0" },
                  { label: "Target Compliance",             value: "100%" },
                  { label: "Target Readmission Risk",       value: "0%" },
                ].map(item => (
                  <div key={item.label} className="flex items-center justify-between">
                    <span className="text-sm text-[var(--color-muted)]">{item.label}</span>
                    <span className="text-sm font-semibold text-[var(--color-foreground)]">{item.value}</span>
                  </div>
                ))}
                <div className="pt-2 mt-2 border-t border-[var(--color-border-subtle)]">
                  <p className="text-xs font-semibold text-[var(--color-muted)] mb-2 uppercase tracking-wide">
                    Expected Health Score
                  </p>
                  <ProgressBar
                    value={Math.round(latest.ideal_health_score)}
                    showValue
                    color="var(--color-primary-500)"
                  />
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
                    <CardDescription>Actual patient state</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { label: "Real Health Score (Day 1)",     value: first?.real_health_score.toFixed(1) ?? "—",  delta: first ? `${(first.real_health_score - first.ideal_health_score).toFixed(1)}` : null },
                  { label: "Real Health Score (Latest)",    value: latest.real_health_score.toFixed(1),         delta: `${(latest.real_health_score - latest.ideal_health_score).toFixed(1)}` },
                  { label: "Recovery Score",                value: `${latest.recovery_score.toFixed(1)}`,       delta: `${(latest.recovery_score - 100).toFixed(1)}` },
                  { label: "Compliance Score",              value: `${latest.compliance_score.toFixed(1)}%`,    delta: `${(latest.compliance_score - 100).toFixed(1)}` },
                  { label: "Readmission Risk",              value: `${Math.round(latest.readmission_probability * 100)}%`, delta: `+${Math.round(latest.readmission_probability * 100)}` },
                ].map(item => (
                  <div key={item.label} className="flex items-center justify-between">
                    <span className="text-sm text-[var(--color-muted)]">{item.label}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-[var(--color-foreground)]">{item.value}</span>
                      {item.delta && (
                        <Badge
                          variant={parseFloat(item.delta) >= 0 ? "danger" : "success"}
                          size="sm"
                        >
                          {parseFloat(item.delta) >= 0 ? "↓" : "↑"} {item.delta}
                        </Badge>
                      )}
                    </div>
                  </div>
                ))}
                <div className="pt-2 mt-2 border-t border-[var(--color-border-subtle)]">
                  <p className="text-xs font-semibold text-[var(--color-muted)] mb-2 uppercase tracking-wide">
                    Real Health Score
                  </p>
                  <ProgressBar
                    value={Math.round(latest.real_health_score)}
                    showValue
                    color="var(--color-danger-500)"
                  />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Deviation summary */}
          <motion.div variants={staggerItem}>
            <Card className="bg-gradient-to-r from-[var(--color-primary-50)] to-[var(--color-danger-50)] dark:from-[var(--color-primary-900)]/20 dark:to-[var(--color-danger-900)]/20">
              <CardContent className="pt-5 flex items-center justify-between flex-wrap gap-4">
                <div className="flex items-center gap-3">
                  <ArrowRightLeft size={20} className="text-[var(--color-muted)]" />
                  <div>
                    <p className="text-sm font-semibold text-[var(--color-foreground)]">
                      Deviation Score: {latest.deviation_score.toFixed(1)}
                    </p>
                    <p className="text-xs text-[var(--color-muted)]">
                      Ideal {latest.ideal_health_score.toFixed(1)} − Real {latest.real_health_score.toFixed(1)} on Day {latest.day}
                    </p>
                  </div>
                </div>
                <Badge variant="warning" size="md">
                  Compliance: {latest.compliance_score.toFixed(1)}%
                </Badge>
              </CardContent>
            </Card>
          </motion.div>

          {/* Radar chart — real derived data */}
          <motion.div variants={staggerItem}>
            <Card>
              <CardHeader>
                <CardTitle>Twin Comparison Radar</CardTitle>
                <CardDescription>Real vs ideal across all score dimensions (Day {latest.day})</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={280}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11 }} />
                    <Radar name="Ideal" dataKey="ideal" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} />
                    <Radar name="Real"  dataKey="real"  stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.15} />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>

          {/* 30-day divergence chart — real data */}
          <motion.div variants={staggerItem}>
            <Card>
              <CardHeader>
                <CardTitle>30-Day Health Score Divergence</CardTitle>
                <CardDescription>Ideal vs Real health scores over the monitoring period</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                    <Legend />
                    <Area type="monotone" dataKey="ideal" name="Ideal Twin" stroke="#3b82f6" fill="#3b82f620" strokeWidth={2} dot={false} />
                    <Area type="monotone" dataKey="real"  name="Real Twin"  stroke="#f43f5e" fill="#f43f5e20" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>
        </>
      )}
    </motion.div>
  );
}
