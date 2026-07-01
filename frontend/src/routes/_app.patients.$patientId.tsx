import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { getStoredUser } from "@/lib/auth";
import { useState } from "react";
import { motion } from "framer-motion";
import {
  ChevronLeft, Activity, Heart, Brain, TrendingUp, ClipboardList, FileText, Stethoscope,
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, AreaChart, Area, Legend,
} from "recharts";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Avatar } from "@/components/ui/Avatar";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { RiskBadge, RecoveryBadge, TrendBadge } from "@/components/ui/StatusBadge";
import { Tabs, TabList, TabTrigger, TabPanels, TabPanel } from "@/components/ui/Tabs";
import { FloatingPanel } from "@/components/ui/FloatingPanel";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonCard, SkeletonKPICard } from "@/components/ui/Skeleton";
import { usePatientSummary } from "@/hooks/usePatients";
import {
  getMedicalHistory, getCarePlan, hospitalQueryKeys,
} from "@/lib/api";
import { CarePlanEditor } from "@/components/doctor/CarePlanEditor";
import type { RiskLevel, RecoveryStatus, HealthTrend } from "@/types";

export const Route = createFileRoute("/_app/patients/$patientId")({
  beforeLoad: () => {
    const user = getStoredUser();
    if (!user || (user.role !== "admin" && user.role !== "doctor")) {
      throw redirect({ to: "/" });
    }
  },
  component: PatientDetailPage,
});

// Recommendation text derived from real readmission probability
function getRecommendation(prob: number, trend: string): string {
  if (prob > 0.85) return "Hospital Readmission Risk — Immediate escalation required. Alert attending physician and prepare readmission protocol.";
  if (prob > 0.70) return "Immediate Doctor Review — Critical risk threshold exceeded. Schedule urgent consultation and consider medication adjustment.";
  if (prob > 0.50) return "Increase Monitoring — Moderate-to-high risk. Ensure daily vital checks and review compliance over the last 7 days.";
  if (prob > 0.30) return "Increase Monitoring — Patient shows moderate readmission risk. Follow up on exercise and medication adherence.";
  return "Continue Current Treatment — Patient is recovering well within expected parameters.";
}

function PatientDetailPage() {
  const { patientId } = Route.useParams();
  const queryClient = useQueryClient();
  const { data: summaryData, isLoading, error } = usePatientSummary(patientId);
  const [carePlanOpen, setCarePlanOpen] = useState(false);

  const { data: medicalHistory } = useQuery({
    queryKey: hospitalQueryKeys.medicalHistory(patientId),
    queryFn: () => getMedicalHistory(patientId),
    enabled: Boolean(patientId),
  });

  const { data: carePlan } = useQuery({
    queryKey: hospitalQueryKeys.carePlan(patientId),
    queryFn: () => getCarePlan(patientId),
    enabled: Boolean(patientId),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex gap-4 items-center">
          <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 animate-pulse" />
          <div className="w-48 h-5 rounded bg-gray-200 dark:bg-gray-700 animate-pulse" />
        </div>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonKPICard key={i} />)}
        </div>
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (error || !summaryData) {
    return (
      <div className="py-12">
        <EmptyState
          title="Patient not found"
          description="The requested patient could not be retrieved. It may not exist in the database."
          size="md"
        />
      </div>
    );
  }

  const trends = summaryData.daily_trends ?? [];
  const latest = trends[trends.length - 1] ?? {
    day: 1,
    compliance_score: 0,
    deviation_score: 0,
    recovery_score: 0,
    health_trend: "Stable" as HealthTrend,
    readmission_probability: 0,
    real_health_score: 0,
    ideal_health_score: 0,
  };

  // Chart data — readmission as percentage for readability
  const chartData = trends.map((t) => ({
    day: t.day,
    recovery:    Math.round(t.recovery_score * 10) / 10,
    compliance:  Math.round(t.compliance_score * 10) / 10,
    readmission: Math.round(t.readmission_probability * 1000) / 10,
    ideal:       Math.round(t.ideal_health_score * 10) / 10,
    real:        Math.round(t.real_health_score * 10) / 10,
  }));

  // Compliance trend: compare first 7 days avg vs last 7 days avg
  const first7Avg = trends.slice(0, 7).reduce((s, t) => s + t.compliance_score, 0) / Math.max(7, trends.slice(0, 7).length);
  const last7Avg  = trends.slice(-7).reduce((s, t) => s + t.compliance_score, 0) / Math.max(7, trends.slice(-7).length);
  const complianceTrend = last7Avg - first7Avg;

  // Missed medication estimate: days where readmission spiked > 0.1 above prev
  const missedMeds = trends.filter((t, i) =>
    i > 0 && t.readmission_probability - trends[i - 1].readmission_probability > 0.1
  ).length;

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
                {summaryData.patient_name || patientId}
              </h1>
              <p className="text-sm text-[var(--color-muted)]">
                {summaryData.disease_type} · {trends.length} days monitored
              </p>
            </div>
            <RiskBadge level={summaryData.current_risk_level as RiskLevel} />
            <RecoveryBadge status={summaryData.current_recovery_status as RecoveryStatus} />
            <TrendBadge trend={latest.health_trend as HealthTrend} />
          </div>
        </div>
        <Button
          size="sm"
          variant="secondary"
          leftIcon={<ClipboardList size={14} />}
          onClick={() => setCarePlanOpen(true)}
        >
          {carePlan ? "Update Care Plan" : "Create Care Plan"}
        </Button>
      </motion.div>

      {/* KPI strip — real values from latest day */}
      <motion.div variants={staggerItem} className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard icon={<Activity size={16} />} label="Readmission Risk"  value={`${Math.round(latest.readmission_probability * 100)}%`} color="danger" />
        <StatCard icon={<TrendingUp size={16} />} label="Compliance Score" value={`${Math.round(latest.compliance_score)}%`} color="primary" />
        <StatCard icon={<Heart size={16} />} label="Recovery Score"    value={`${Math.round(latest.recovery_score)}%`} color="success" />
        <StatCard icon={<Brain size={16} />} label="Deviation Score"   value={latest.deviation_score.toFixed(1)} color="warning" />
      </motion.div>

      {/* AI Recommendation panel — derived from real data */}
      <motion.div variants={staggerItem}>
        <FloatingPanel
          title="AI Clinical Recommendation"
          className="border-l-4 border-[var(--color-primary-500)]"
        >
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <p className="text-sm font-semibold text-[var(--color-foreground)]">
                {getRecommendation(latest.readmission_probability, latest.health_trend)}
              </p>
              <div className="flex items-center gap-4 mt-2 flex-wrap">
                <p className="text-xs text-[var(--color-muted)]">
                  Day {latest.day} of {trends.length} · Trend: {latest.health_trend}
                </p>
                <p className="text-xs text-[var(--color-muted)]">
                  Compliance {complianceTrend >= 0 ? "▲" : "▼"} {Math.abs(complianceTrend).toFixed(1)}% vs first week
                </p>
              </div>
            </div>
          </div>
        </FloatingPanel>
      </motion.div>

      {/* Tabs */}
      <motion.div variants={staggerItem}>
        <Tabs defaultTab="trends" variant="line">
          <TabList>
            <TabTrigger id="trends"     icon={<Activity size={14} />}>Trends</TabTrigger>
            <TabTrigger id="compliance" icon={<TrendingUp size={14} />}>Compliance</TabTrigger>
            <TabTrigger id="twin"       icon={<Brain size={14} />}>Digital Twin</TabTrigger>
            <TabTrigger id="careplan"   icon={<ClipboardList size={14} />}>Care Plan</TabTrigger>
            <TabTrigger id="history"    icon={<FileText size={14} />}>Medical History</TabTrigger>
          </TabList>
          <TabPanels>

            {/* ── Trends ── */}
            <TabPanel id="trends">
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mt-4">
                <Card>
                  <CardHeader><CardTitle>Recovery Score — {trends.length} Days</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="recovGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid var(--color-border)", fontSize: 12 }} />
                        <Area type="monotone" dataKey="recovery" name="Recovery Score" stroke="#3b82f6" fill="url(#recovGrad)" strokeWidth={2} dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader><CardTitle>Readmission Probability — {trends.length} Days</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="readGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%"  stopColor="#f43f5e" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip
                          contentStyle={{ borderRadius: "12px", border: "1px solid var(--color-border)", fontSize: 12 }}
                          formatter={(v: number) => [`${v}%`, "Readmission Risk"]}
                        />
                        <Area type="monotone" dataKey="readmission" name="Readmission %" stroke="#f43f5e" fill="url(#readGrad)" strokeWidth={2} dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card className="lg:col-span-2">
                  <CardHeader><CardTitle>Compliance Score — {trends.length} Days</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={180}>
                      <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid var(--color-border)", fontSize: 12 }} />
                        <Line type="monotone" dataKey="compliance" name="Compliance %" stroke="#22c55e" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabPanel>

            {/* ── Compliance ── */}
            <TabPanel id="compliance">
              <div className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Compliance Overview</CardTitle>
                    <CardDescription>Day {latest.day} latest values</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-5">
                    <ProgressBar
                      label="Overall Compliance Score"
                      value={Math.round(latest.compliance_score)}
                      showValue
                      color="var(--color-primary-500)"
                    />
                    <ProgressBar
                      label="Recovery Score"
                      value={Math.round(latest.recovery_score)}
                      showValue
                      color="var(--color-success-500)"
                    />
                    <ProgressBar
                      label="Real Health Score"
                      value={Math.round(latest.real_health_score)}
                      showValue
                      color="var(--color-warning-500)"
                    />
                    <div className="pt-2 border-t border-[var(--color-border-subtle)]">
                      <ProgressBar
                        label="Deviation from Ideal"
                        value={Math.round(latest.deviation_score)}
                        showValue
                        color="var(--color-danger-500)"
                      />
                    </div>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
                  <Card className="text-center">
                    <CardContent className="pt-4 pb-4">
                      <p className="text-2xl font-bold text-[var(--color-foreground)]">{trends.length}</p>
                      <p className="text-xs text-[var(--color-muted)] mt-1">Days Monitored</p>
                    </CardContent>
                  </Card>
                  <Card className="text-center">
                    <CardContent className="pt-4 pb-4">
                      <p className={`text-2xl font-bold ${complianceTrend >= 0 ? "text-[var(--color-success-600)]" : "text-[var(--color-danger-500)]"}`}>
                        {complianceTrend >= 0 ? "+" : ""}{complianceTrend.toFixed(1)}%
                      </p>
                      <p className="text-xs text-[var(--color-muted)] mt-1">Compliance Trend</p>
                    </CardContent>
                  </Card>
                  <Card className="text-center col-span-2 sm:col-span-1">
                    <CardContent className="pt-4 pb-4 flex items-center justify-center gap-4">
                      <ProgressRing
                        value={Math.round(latest.compliance_score)}
                        size={72}
                        strokeWidth={6}
                      />
                      <div>
                        <p className="text-sm font-semibold text-[var(--color-foreground)]">Day {latest.day}</p>
                        <p className="text-xs text-[var(--color-muted)]">Overall Compliance</p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </TabPanel>

            {/* ── Digital Twin ── */}
            <TabPanel id="twin">
              <div className="mt-4 space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Ideal vs Real Twin — Health Score Divergence</CardTitle>
                    <CardDescription>
                      Gap on Day {latest.day}: Ideal {latest.ideal_health_score.toFixed(1)} vs Real {latest.real_health_score.toFixed(1)} (Δ {latest.deviation_score.toFixed(1)})
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={240}>
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="idealGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.15} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                          </linearGradient>
                          <linearGradient id="realGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%"  stopColor="#f43f5e" stopOpacity={0.15} />
                            <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", border: "1px solid var(--color-border)", fontSize: 12 }} />
                        <Legend />
                        <Area type="monotone" dataKey="ideal" name="Ideal Twin" stroke="#3b82f6" fill="url(#idealGrad)" strokeWidth={2} dot={false} />
                        <Area type="monotone" dataKey="real"  name="Real Twin"  stroke="#f43f5e" fill="url(#realGrad)"  strokeWidth={2} dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                {/* Summary stat row */}
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  {[
                    { label: "Ideal Health (Day 1)",  value: trends[0]?.ideal_health_score.toFixed(1) ?? "—",  color: "text-[var(--color-primary-600)]" },
                    { label: "Real Health (Day 1)",   value: trends[0]?.real_health_score.toFixed(1) ?? "—",   color: "text-[var(--color-danger-500)]" },
                    { label: "Ideal Health (Latest)", value: latest.ideal_health_score.toFixed(1),              color: "text-[var(--color-primary-600)]" },
                    { label: "Real Health (Latest)",  value: latest.real_health_score.toFixed(1),               color: "text-[var(--color-danger-500)]" },
                  ].map(s => (
                    <Card key={s.label} className="text-center">
                      <CardContent className="pt-4 pb-4">
                        <p className={`text-2xl font-bold tabular-nums ${s.color}`}>{s.value}</p>
                        <p className="text-xs text-[var(--color-muted)] mt-1">{s.label}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </TabPanel>

            {/* ── Care Plan ── */}
            <TabPanel id="careplan">
              <div className="mt-4 space-y-4">
                {carePlan ? (
                  <>
                    <Card>
                      <CardHeader>
                        <CardTitle>Active Care Plan</CardTitle>
                        <CardDescription>Ideal Digital Twin targets set by the treating doctor</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-3 gap-4 mb-5">
                          <div className="text-center p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20">
                            <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">
                              {carePlan.daily_steps_goal?.toLocaleString()}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">Steps / day</p>
                          </div>
                          <div className="text-center p-3 rounded-xl bg-purple-50 dark:bg-purple-900/20">
                            <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">
                              {carePlan.sleep_hours_goal}h
                            </p>
                            <p className="text-xs text-gray-500 mt-1">Sleep goal</p>
                          </div>
                          <div className="text-center p-3 rounded-xl bg-cyan-50 dark:bg-cyan-900/20">
                            <p className="text-2xl font-bold text-cyan-700 dark:text-cyan-300">
                              {carePlan.water_intake_goal_ml}ml
                            </p>
                            <p className="text-xs text-gray-500 mt-1">Water intake</p>
                          </div>
                        </div>
                        <div className="space-y-3">
                          {carePlan.medication_schedule && (
                            <InfoRow label="💊 Medication Schedule" value={carePlan.medication_schedule} />
                          )}
                          {carePlan.exercise_plan && (
                            <InfoRow label="🏃 Exercise Plan" value={carePlan.exercise_plan} />
                          )}
                          {carePlan.diet_plan && (
                            <InfoRow label="🥗 Diet Plan" value={carePlan.diet_plan} />
                          )}
                          {carePlan.notes && (
                            <InfoRow label="📋 Doctor Notes" value={carePlan.notes} />
                          )}
                        </div>
                        <div className="flex gap-4 mt-4 pt-4 border-t border-gray-100 dark:border-gray-800 text-xs text-gray-500">
                          <span>Follow-up every {carePlan.followup_frequency_days} days</span>
                          <span>·</span>
                          <span>Monitoring {carePlan.monitoring_duration_days} days</span>
                          <span>·</span>
                          <span>Alert at &gt;{Math.round((carePlan.risk_threshold ?? 0.5) * 100)}% risk</span>
                        </div>
                      </CardContent>
                    </Card>
                    <Button
                      variant="secondary"
                      size="sm"
                      leftIcon={<ClipboardList size={14} />}
                      onClick={() => setCarePlanOpen(true)}
                    >
                      Update Care Plan
                    </Button>
                  </>
                ) : (
                  <EmptyState
                    title="No Care Plan Yet"
                    description="Create a care plan to set this patient's Ideal Digital Twin targets."
                    size="sm"
                    className="py-8"
                    action={{ label: "Create Care Plan", onClick: () => setCarePlanOpen(true) }}
                  />
                )}
              </div>
            </TabPanel>

            {/* ── Medical History ── */}
            <TabPanel id="history">
              <div className="mt-4 space-y-4">
                {medicalHistory ? (
                  <Card>
                    <CardHeader>
                      <CardTitle>Medical History</CardTitle>
                      <CardDescription>Clinical record maintained by the treating doctor</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {medicalHistory.past_diseases && (
                        <Section label="Past Diseases" value={medicalHistory.past_diseases} />
                      )}
                      {medicalHistory.previous_admissions && (
                        <Section label="Previous Admissions" value={medicalHistory.previous_admissions} />
                      )}
                      {medicalHistory.previous_surgeries && (
                        <Section label="Previous Surgeries" value={medicalHistory.previous_surgeries} />
                      )}
                      {medicalHistory.family_history && (
                        <Section label="Family History" value={medicalHistory.family_history} />
                      )}
                      {medicalHistory.current_medications && (
                        <Section label="Current Medications" value={medicalHistory.current_medications} />
                      )}
                      {medicalHistory.allergies && (
                        <Section label="Allergies" value={medicalHistory.allergies} />
                      )}
                      {(medicalHistory.lifestyle_smoking || medicalHistory.lifestyle_alcohol || medicalHistory.lifestyle_exercise) && (
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-2">Lifestyle</p>
                          <div className="flex flex-wrap gap-2">
                            {medicalHistory.lifestyle_smoking && (
                              <span className="px-2.5 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                                Smoking: {medicalHistory.lifestyle_smoking}
                              </span>
                            )}
                            {medicalHistory.lifestyle_alcohol && (
                              <span className="px-2.5 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                                Alcohol: {medicalHistory.lifestyle_alcohol}
                              </span>
                            )}
                            {medicalHistory.lifestyle_exercise && (
                              <span className="px-2.5 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                                Exercise: {medicalHistory.lifestyle_exercise}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                      {medicalHistory.doctor_notes && (
                        <div className="p-3 rounded-xl bg-primary-50 dark:bg-primary-900/20 border border-primary-100 dark:border-primary-800">
                          <p className="text-xs font-semibold text-primary-700 dark:text-primary-400 mb-1">
                            🩺 Doctor's Clinical Notes
                          </p>
                          <p className="text-sm text-gray-700 dark:text-gray-300">{medicalHistory.doctor_notes}</p>
                        </div>
                      )}
                      {medicalHistory.discharge_summary && (
                        <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800">
                          <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 mb-1">
                            📄 Discharge Summary
                          </p>
                          <p className="text-sm text-gray-700 dark:text-gray-300">{medicalHistory.discharge_summary}</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ) : (
                  <EmptyState
                    title="No Medical History"
                    description="No clinical history has been recorded for this patient yet."
                    size="sm"
                    className="py-8"
                  />
                )}
              </div>
            </TabPanel>

          </TabPanels>
        </Tabs>
      </motion.div>

      {/* Care Plan Editor modal */}
      <CarePlanEditor
        open={carePlanOpen}
        onClose={() => setCarePlanOpen(false)}
        patientUserId={patientId}
        patientName={summaryData.patient_name || patientId}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: hospitalQueryKeys.carePlan(patientId) });
        }}
      />
    </motion.div>
  );
}

function StatCard({ icon, label, value, color }: {
  icon: React.ReactNode; label: string; value: string; color: string;
}) {
  const colors: Record<string, string> = {
    danger:  "text-[var(--color-danger-500)]  bg-[var(--color-danger-50)]",
    primary: "text-[var(--color-primary-600)] bg-[var(--color-primary-50)]",
    success: "text-[var(--color-success-600)] bg-[var(--color-success-50)]",
    warning: "text-[var(--color-warning-600)] bg-[var(--color-warning-50)]",
  };
  return (
    <Card className="text-center">
      <CardContent className="pt-5 pb-4">
        <div className={`inline-flex items-center justify-center w-8 h-8 rounded-xl mb-2 ${colors[color]}`}>
          {icon}
        </div>
        <p className="text-xl font-bold text-[var(--color-foreground)] tabular-nums">{value}</p>
        <p className="text-xs text-[var(--color-muted)] mt-0.5">{label}</p>
      </CardContent>
    </Card>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-700">
      <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-0.5">{label}</p>
      <p className="text-sm text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

function Section({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">{value}</p>
    </div>
  );
}
