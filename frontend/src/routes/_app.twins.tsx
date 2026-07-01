import React, { useState, useEffect } from "react";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { getStoredUser } from "@/lib/auth";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Activity, ArrowRightLeft, Zap, Sliders, Eye, Heart, Info, Pill, Flame, CheckCircle, AlertTriangle } from "lucide-react";
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
import { Button } from "@/components/ui/Button";
import { usePatients, usePatientSummary } from "@/hooks/usePatients";
import { simulateRecovery, type SimulationResponse } from "@/lib/api";
import type { RiskLevel, RecoveryStatus, HealthTrend } from "@/types";

export const Route = createFileRoute("/_app/twins")({
  beforeLoad: () => {
    const user = getStoredUser();
    if (!user || (user.role !== "admin" && user.role !== "doctor")) {
      throw redirect({ to: "/" });
    }
  },
  component: DigitalTwinsPage,
});

function DigitalTwinsPage() {
  const [search, setSearch]     = useState("");
  const [selectedId, setSelected] = useState<string | null>(null);
  
  // What-If Simulation State
  const [simulating, setSimulating] = useState(false);
  const [simInputs, setSimInputs] = useState({
    actual_steps: 8000,
    actual_sleep_hours: 8,
    water_intake: 2000,
    medication_taken: "Yes" as "Yes" | "No",
    weight_kg: 70,
  });
  const [simResult, setSimResult] = useState<SimulationResponse | null>(null);

  // Timeline expanded state
  const [expandedDay, setExpandedDay] = useState<number | null>(null);

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

  // Reset simulation inputs when a patient changes
  useEffect(() => {
    if (latest) {
      setSimInputs({
        actual_steps: latest.actual_steps ?? 8000,
        actual_sleep_hours: latest.actual_sleep_hours ?? 8,
        water_intake: latest.water_intake ?? 2000,
        medication_taken: (latest.medication_taken as "Yes" | "No") ?? "Yes",
        weight_kg: latest.weight_kg ?? 70,
      });
      setSimResult(null);
      setExpandedDay(null);
    }
  }, [effectiveId, latest]);

  const handleSimulate = async () => {
    if (!effectiveId) return;
    setSimulating(true);
    try {
      const res = await simulateRecovery(effectiveId, simInputs);
      setSimResult(res);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setSimulating(false);
    }
  };

  // Chart data
  const chartData = trends.map(t => ({
    day:   t.day,
    ideal: Math.round((t.ideal_health_score ?? 100) * 10) / 10,
    real:  Math.round((t.real_health_score ?? 50) * 10) / 10,
  }));

  // Radar data: compare score components on latest day vs ideal (100)
  const radarData = latest
    ? [
        { axis: "Recovery",    ideal: 100, real: Math.round(latest.recovery_score ?? 50) },
        { axis: "Compliance",  ideal: 100, real: Math.round(latest.compliance_score ?? 50) },
        { axis: "Health",      ideal: Math.round(latest.ideal_health_score ?? 100), real: Math.round(latest.real_health_score ?? 50) },
        { axis: "Low Deviation", ideal: 100, real: Math.max(0, Math.round(100 - (latest.deviation_score ?? 0))) },
        { axis: "Low Readmission", ideal: 100, real: Math.round((1 - (latest.readmission_probability ?? 0)) * 100) },
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
        <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">AI Digital Twins Platform</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Real-time patient twin divergence analysis, prediction explainability, and recovery simulators.
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
        <div className="space-y-6">
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
                    <CardDescription>Prescribed Targets & Ideal State</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { label: "Steps Target", value: `${latest.expected_steps?.toLocaleString() ?? 8000} steps` },
                  { label: "Sleep Target", value: `${latest.expected_sleep_hours ?? 8.0} hours` },
                  { label: "Water Intake Target", value: `${latest.water_intake_goal ?? 2000} ml` },
                  { label: "Target Blood Pressure", value: "105/70 mmHg" },
                  { label: "Target Heart Rate", value: "80 bpm" },
                  { label: "Target SpO₂", value: "97.5%" },
                  { label: "Target Temperature", value: "36.7 °C" },
                  { label: "Expected Weight", value: `${latest.expected_weight ?? "70"} kg` },
                ].map(item => (
                  <div key={item.label} className="flex items-center justify-between py-0.5 border-b border-[var(--color-border-subtle)] last:border-0">
                    <span className="text-xs text-[var(--color-muted)]">{item.label}</span>
                    <span className="text-xs font-semibold text-[var(--color-foreground)]">{item.value}</span>
                  </div>
                ))}
                <div className="pt-2 mt-2 border-t border-[var(--color-border-subtle)]">
                  <p className="text-xs font-semibold text-[var(--color-muted)] mb-2 uppercase tracking-wide">
                    Baseline Health expectation
                  </p>
                  <ProgressBar
                    value={Math.round(latest.ideal_health_score ?? 100)}
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
                    <CardDescription>Actual Daily Behaviors & Vitals</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { label: "Steps Logged", value: `${latest.actual_steps?.toLocaleString()} steps`, dev: latest.sleep_deviation !== undefined ? latest.actual_steps - latest.expected_steps : 0 },
                  { label: "Sleep Logged", value: `${latest.actual_sleep_hours} hours`, dev: latest.sleep_deviation !== undefined ? latest.actual_sleep_hours - latest.expected_sleep_hours : 0 },
                  { label: "Water Intake", value: `${latest.water_intake} ml`, dev: latest.water_intake - latest.water_intake_goal },
                  { label: "Blood Pressure", value: `${latest.systolic_bp}/${latest.diastolic_bp} mmHg` },
                  { label: "Heart Rate", value: `${latest.heart_rate} bpm` },
                  { label: "Blood Oxygen (SpO₂)", value: `${latest.spo2}%` },
                  { label: "Body Temperature", value: `${latest.body_temperature} °C` },
                  { label: "Patient Weight", value: `${latest.weight_kg ?? "70"} kg` },
                ].map(item => {
                  let devText = null;
                  let isPositive = false;
                  if ('dev' in item && typeof item.dev === 'number' && item.dev !== 0) {
                    isPositive = item.dev > 0;
                    devText = (isPositive ? "+" : "") + Math.round(item.dev).toLocaleString();
                  }

                  return (
                    <div key={item.label} className="flex items-center justify-between py-0.5 border-b border-[var(--color-border-subtle)] last:border-0">
                      <span className="text-xs text-[var(--color-muted)]">{item.label}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-[var(--color-foreground)]">{item.value}</span>
                        {devText && (
                          <Badge variant={isPositive ? "success" : "danger"} size="sm" className="px-1 text-[10px] leading-tight">
                            {devText}
                          </Badge>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div className="pt-2 mt-2 border-t border-[var(--color-border-subtle)]">
                  <p className="text-xs font-semibold text-[var(--color-muted)] mb-2 uppercase tracking-wide">
                    Real-time Health index
                  </p>
                  <ProgressBar
                    value={Math.round(latest.real_health_score ?? 50)}
                    showValue
                    color="var(--color-danger-500)"
                  />
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Deviation Engine Summary */}
          <motion.div variants={staggerItem} className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <ArrowRightLeft size={18} className="text-[var(--color-primary-500)]" />
                  <CardTitle className="text-sm">Deviation Engine Metrics</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4">
                {[
                  { label: "Medication Deviation", value: latest.medication_deviation === 0 ? "Adherent" : "Missed Dose", isErr: latest.medication_deviation !== 0 },
                  { label: "Exercise Deviation", value: latest.exercise_completed === "Yes" ? "Adherent" : "Missed Session", isErr: latest.exercise_completed === "No" },
                  { label: "Steps Deviation", value: `${Math.round(latest.sleep_deviation !== undefined ? Math.abs(latest.actual_steps - latest.expected_steps) : 0).toLocaleString()} steps` },
                  { label: "Sleep Deviation", value: `${latest.sleep_deviation?.toFixed(1) ?? "0.0"} hours` },
                  { label: "Water Deviation", value: `${Math.abs(latest.water_intake - latest.water_intake_goal)} ml` },
                  { label: "Heart Rate Deviation", value: `${latest.heart_rate_deviation?.toFixed(1) ?? "0.0"} bpm` },
                  { label: "BP Deviation (Systolic)", value: `${Math.abs(latest.systolic_bp - 105)} mmHg` },
                  { label: "BP Deviation (Diastolic)", value: `${Math.abs(latest.diastolic_bp - 70)} mmHg` },
                  { label: "SpO₂ Deviation", value: `${latest.spo2_deviation?.toFixed(1) ?? "0.0"} %` },
                  { label: "Weight Deviation", value: `${latest.weight_deviation?.toFixed(1) ?? "0.0"} kg` },
                ].map(item => (
                  <div key={item.label} className="p-2 rounded-xl bg-[var(--color-surface-subtle)] border border-[var(--color-border-subtle)]">
                    <p className="text-[10px] text-[var(--color-muted)] font-medium uppercase">{item.label}</p>
                    <p className={`text-xs font-bold mt-0.5 ${item.isErr ? "text-red-500" : "text-[var(--color-foreground)]"}`}>
                      {item.value}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="flex flex-col justify-between">
              <CardHeader>
                <CardTitle className="text-sm">Engine Convergence</CardTitle>
                <CardDescription>Adherence metrics summary</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 flex-1 flex flex-col justify-center">
                <div className="text-center">
                  <p className="text-xs text-[var(--color-muted)] uppercase font-semibold">Overall Deviation Score</p>
                  <p className="text-4xl font-extrabold text-[var(--color-danger-500)] mt-1">
                    {latest.deviation_score?.toFixed(1)}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-[var(--color-muted)] uppercase font-semibold">Overall Compliance Score</p>
                  <p className="text-4xl font-extrabold text-green-500 mt-1">
                    {latest.compliance_score?.toFixed(1)}%
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Explainable AI Prediction Reasons */}
          <motion.div variants={staggerItem} className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-1 bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-primary-50)]/10">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Info size={18} className="text-[var(--color-primary-500)]" />
                  <CardTitle className="text-sm">Explainable AI (XAI)</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-3 rounded-2xl bg-[var(--color-surface)] border border-[var(--color-border)] text-center">
                  <p className="text-xs text-[var(--color-muted)]">Readmission Risk Probability</p>
                  <p className="text-3xl font-extrabold text-[var(--color-primary-600)] mt-1">
                    {Math.round((latest.readmission_probability ?? 0) * 100)}%
                  </p>
                  <div className="mt-2 flex justify-center">
                    <RiskBadge level={selectedPatient.Risk_Level as RiskLevel} />
                  </div>
                </div>

                <div>
                  <p className="text-xs font-bold text-[var(--color-foreground)] mb-2">Key Risk Drivers:</p>
                  <div className="flex flex-wrap gap-1.5">
                    {latest.shap_reasons && latest.shap_reasons.length > 0 ? (
                      latest.shap_reasons.map(reason => (
                        <Badge key={reason} variant="danger" className="px-2 py-0.5 text-[10px]">
                          {reason}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-xs text-[var(--color-muted)]">No elevated risk factors detected</span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Zap size={18} className="text-amber-500" />
                  <CardTitle className="text-sm">AI Personalized Recommendations</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {latest.ai_recommendations && latest.ai_recommendations.length > 0 ? (
                  latest.ai_recommendations.map((rec, i) => (
                    <div key={i} className="flex gap-2.5 items-start p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/10 text-amber-900 dark:text-amber-300">
                      <CheckCircle size={15} className="shrink-0 mt-0.5 text-amber-500" />
                      <span className="text-xs leading-relaxed font-medium">{rec}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-6 text-xs text-[var(--color-muted)]">
                    No recommendations needed. Twin is performing perfectly.
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Recovery Simulator ("What-If" Panel) */}
          <motion.div variants={staggerItem}>
            <Card className="border-2 border-[var(--color-primary-500)]/30 bg-gradient-to-r from-[var(--color-surface)] to-[var(--color-primary-50)]/5">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Sliders size={20} className="text-[var(--color-primary-500)]" />
                  <div>
                    <CardTitle>Recovery "What-If" Simulator</CardTitle>
                    <CardDescription>Simulate how behavior changes impact recovery outcomes in real-time</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Simulator Inputs */}
                <div className="space-y-4">
                  {/* Medication */}
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-[var(--color-foreground)] flex items-center gap-1">
                      <Pill size={14} className="text-[var(--color-primary-500)]" />
                      Take Medication Today?
                    </label>
                    <select
                      value={simInputs.medication_taken}
                      onChange={e => setSimInputs(prev => ({ ...prev, medication_taken: e.target.value as "Yes" | "No" }))}
                      className="text-xs p-1 rounded bg-[var(--color-surface)] border border-[var(--color-border)]"
                    >
                      <option value="Yes">Yes (Adherent)</option>
                      <option value="No">No (Missed)</option>
                    </select>
                  </div>

                  {/* Steps */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <label className="font-semibold text-[var(--color-foreground)]">Steps Goal</label>
                      <span className="text-[var(--color-muted)]">{simInputs.actual_steps.toLocaleString()} steps</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={20000}
                      step={500}
                      value={simInputs.actual_steps}
                      onChange={e => setSimInputs(prev => ({ ...prev, actual_steps: parseInt(e.target.value) }))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>

                  {/* Sleep */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <label className="font-semibold text-[var(--color-foreground)]">Sleep Duration</label>
                      <span className="text-[var(--color-muted)]">{simInputs.actual_sleep_hours.toFixed(1)} hours</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={24}
                      step={0.5}
                      value={simInputs.actual_sleep_hours}
                      onChange={e => setSimInputs(prev => ({ ...prev, actual_sleep_hours: parseFloat(e.target.value) }))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>

                  {/* Water */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <label className="font-semibold text-[var(--color-foreground)]">Water Intake</label>
                      <span className="text-[var(--color-muted)]">{simInputs.water_intake.toLocaleString()} ml</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={5000}
                      step={100}
                      value={simInputs.water_intake}
                      onChange={e => setSimInputs(prev => ({ ...prev, water_intake: parseInt(e.target.value) }))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>

                  {/* Weight */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <label className="font-semibold text-[var(--color-foreground)]">Patient Weight</label>
                      <span className="text-[var(--color-muted)]">{simInputs.weight_kg.toFixed(1)} kg</span>
                    </div>
                    <input
                      type="range"
                      min={30}
                      max={180}
                      step={0.5}
                      value={simInputs.weight_kg}
                      onChange={e => setSimInputs(prev => ({ ...prev, weight_kg: parseFloat(e.target.value) }))}
                      className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>

                  <Button
                    onClick={handleSimulate}
                    disabled={simulating}
                    className="w-full mt-2"
                    variant="primary"
                  >
                    {simulating ? "Recalculating Outcomes..." : "Run Simulation Forecast"}
                  </Button>
                </div>

                {/* Simulator Outputs */}
                <div className="p-4 rounded-2xl bg-[var(--color-surface-subtle)] border border-[var(--color-border-subtle)] flex flex-col justify-between">
                  {simResult ? (
                    <div className="space-y-4">
                      <p className="text-xs font-bold text-[var(--color-foreground)] border-b border-[var(--color-border)] pb-2 uppercase tracking-wider flex items-center gap-1.5">
                        <Flame size={14} className="text-amber-500" />
                        Simulation Forecast Report
                      </p>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)]">
                          <p className="text-[10px] text-[var(--color-muted)] font-semibold uppercase">Recovery Score</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-lg text-[var(--color-muted)] line-through">
                              {Math.round(simResult.original_recovery_score)}
                            </span>
                            <span className="text-2xl font-extrabold text-green-500">
                              → {Math.round(simResult.simulated_recovery_score)}
                            </span>
                          </div>
                        </div>

                        <div className="p-3 bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)]">
                          <p className="text-[10px] text-[var(--color-muted)] font-semibold uppercase">Readmission Risk</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-[var(--color-muted)] font-bold">
                              {simResult.original_risk_level} ({Math.round(simResult.original_readmission_probability * 100)}%)
                            </span>
                            <span className="text-xs font-bold text-[var(--color-primary-500)]">
                              → {simResult.simulated_risk_level} ({Math.round(simResult.simulated_readmission_probability * 100)}%)
                            </span>
                          </div>
                        </div>
                      </div>

                      <div>
                        <p className="text-xs font-bold text-[var(--color-foreground)] mb-1.5">Forecast Recommendations:</p>
                        <div className="space-y-1">
                          {simResult.simulated_recommendations.map((rec, i) => (
                            <p key={i} className="text-[11px] text-[var(--color-muted)] leading-tight flex items-start gap-1">
                              <span className="text-amber-500">•</span> {rec}
                            </p>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full text-center py-12 text-[var(--color-muted)]">
                      <Sliders size={32} className="opacity-20 mb-2" />
                      <p className="text-xs font-medium">Adjust sliders and click "Run Simulation Forecast" to preview outcome estimation.</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Charts (30-day divergence chart) */}
          <motion.div variants={staggerItem} className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>30-Day Health Score Divergence</CardTitle>
                <CardDescription>Ideal Twin vs Real Twin divergence tracker</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
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

            <Card>
              <CardHeader>
                <CardTitle>Twin Comparison Radar</CardTitle>
                <CardDescription>Dimension convergence (Day {latest.day})</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="axis" tick={{ fontSize: 10 }} />
                    <Radar name="Ideal" dataKey="ideal" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} />
                    <Radar name="Real"  dataKey="real"  stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.15} />
                    <Legend />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>

          {/* AI Timeline Section */}
          <motion.div variants={staggerItem}>
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>AI Patient Recovery Timeline</CardTitle>
                    <CardDescription>Sequential day-by-day analysis and historical deviations</CardDescription>
                  </div>
                  <Badge variant="success">Day 1 → Day {latest.day}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[450px] overflow-y-auto pr-2">
                  {trends.slice().reverse().map(dayTrend => {
                    const isExpanded = expandedDay === dayTrend.day;
                    return (
                      <div
                        key={dayTrend.day}
                        className="rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface)] overflow-hidden transition-all"
                      >
                        <button
                          onClick={() => setExpandedDay(isExpanded ? null : dayTrend.day)}
                          className="w-full flex items-center justify-between p-3 text-left hover:bg-[var(--color-surface-subtle)] transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <span className="flex items-center justify-center w-8 h-8 rounded-full bg-[var(--color-primary-50)] dark:bg-[var(--color-primary-950)] text-xs font-bold text-[var(--color-primary-600)]">
                              Day {dayTrend.day}
                            </span>
                            <div>
                              <p className="text-xs font-bold text-[var(--color-foreground)]">
                                Deviation Score: {dayTrend.deviation_score?.toFixed(1) ?? "—"} (Compliance: {dayTrend.compliance_score?.toFixed(1) ?? "—"}%)
                              </p>
                              <p className="text-[10px] text-[var(--color-muted)] mt-0.5">
                                Recovery Status: {dayTrend.health_trend ?? "Stable"} · HR: {dayTrend.heart_rate ?? "—"} bpm · Sleep: {dayTrend.actual_sleep_hours ?? "—"}h
                              </p>
                            </div>
                          </div>
                          <Badge variant={dayTrend.readmission_probability > 0.45 ? "danger" : "success"} size="sm">
                            Risk: {Math.round(dayTrend.readmission_probability * 100)}%
                          </Badge>
                        </button>

                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0 }}
                              animate={{ height: "auto" }}
                              exit={{ height: 0 }}
                              className="border-t border-[var(--color-border-subtle)] bg-[var(--color-surface-subtle)] p-3 space-y-3 overflow-hidden text-xs"
                            >
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                <div>
                                  <p className="text-[9px] uppercase font-bold text-[var(--color-muted)]">Real Health Score</p>
                                  <p className="font-bold text-[var(--color-foreground)] mt-0.5">{dayTrend.real_health_score?.toFixed(1)} / {dayTrend.ideal_health_score?.toFixed(1)}</p>
                                </div>
                                <div>
                                  <p className="text-[9px] uppercase font-bold text-[var(--color-muted)]">Medication Taken</p>
                                  <p className="font-bold text-[var(--color-foreground)] mt-0.5">{dayTrend.medication_taken ?? "—"}</p>
                                </div>
                                <div>
                                  <p className="text-[9px] uppercase font-bold text-[var(--color-muted)]">Exercise Completed</p>
                                  <p className="font-bold text-[var(--color-foreground)] mt-0.5">{dayTrend.exercise_completed ?? "—"}</p>
                                </div>
                                <div>
                                  <p className="text-[9px] uppercase font-bold text-[var(--color-muted)]">Hydration logged</p>
                                  <p className="font-bold text-[var(--color-foreground)] mt-0.5">{dayTrend.water_intake ?? "0"} / {dayTrend.water_intake_goal ?? "2000"} ml</p>
                                </div>
                              </div>

                              <div className="border-t border-[var(--color-border-subtle)] pt-2">
                                <p className="text-[10px] font-bold text-[var(--color-foreground)] mb-1">AI Daily Recommendation Logs:</p>
                                <div className="space-y-1">
                                  {dayTrend.ai_recommendations && dayTrend.ai_recommendations.length > 0 ? (
                                    dayTrend.ai_recommendations.map((rec, idx) => (
                                      <p key={idx} className="text-xs text-[var(--color-muted)] leading-relaxed flex items-start gap-1">
                                        <span className="text-amber-500">•</span> {rec}
                                      </p>
                                    ))
                                  ) : (
                                    <p className="text-xs text-[var(--color-muted)]">No recommendations recorded.</p>
                                  )}
                                </div>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}
