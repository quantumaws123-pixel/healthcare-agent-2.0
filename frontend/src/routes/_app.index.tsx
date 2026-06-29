import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  Activity, AlertTriangle, Users, TrendingUp,
  ShieldCheck, Stethoscope,
} from "lucide-react";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { KPICard } from "@/components/ui/KPICard";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { RiskBadge, RecoveryBadge } from "@/components/ui/StatusBadge";
import { Avatar } from "@/components/ui/Avatar";
import { SkeletonKPICard } from "@/components/ui/Skeleton";
import { useDashboardStats, usePatients } from "@/hooks/usePatients";
import type { RiskLevel, RecoveryStatus } from "@/types";

export const Route = createFileRoute("/_app/")({
  component: DashboardOverview,
});

// Maps API lowercase keys → display labels and component props
const RISK_MAP: { key: string; label: string; color: string }[] = [
  { key: "low",      label: "Low Risk",      color: "var(--color-success-500)" },
  { key: "medium",   label: "Medium Risk",   color: "var(--color-warning-500)" },
  { key: "high",     label: "High Risk",     color: "var(--color-danger-500)" },
  { key: "critical", label: "Critical Risk", color: "#9333ea" },
];

// Maps API snake_case keys → RecoveryStatus display values
const RECOVERY_KEY_MAP: Record<string, RecoveryStatus> = {
  recovered:        "Recovered",
  improving:        "Improving",
  stable:           "Stable",
  delayed_recovery: "Delayed Recovery",
  worsening:        "Worsening",
  critical:         "Critical",
};

function DashboardOverview() {
  const navigate = useNavigate();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: patientsData, isLoading: patientsLoading } = usePatients({
    risk_level: "High",
    page_size: 5,
  });

  const totalPatients   = stats?.total_patients ?? 0;
  const highRiskCount   = stats?.high_risk_count ?? 0;
  const avgCompliance   = stats?.avg_compliance ?? 0;
  const avgReadmission  = stats?.avg_readmission_probability ?? 0;

  // API returns lowercase keys: { low, medium, high, critical }
  const riskDist = (stats?.risk_distribution ?? {}) as Record<string, number>;

  // API returns snake_case keys: { recovered, improving, stable, delayed_recovery, worsening, critical }
  const recoveryDist = (stats?.recovery_distribution ?? {}) as Record<string, number>;
  const totalRecovery = Object.values(recoveryDist).reduce((a, b) => a + b, 0) || 1;
  const recoveryRows = Object.entries(recoveryDist)
    .map(([key, count]) => ({
      displayStatus: RECOVERY_KEY_MAP[key] ?? key,
      pct: Math.round((count / totalRecovery) * 1000) / 10,
    }))
    .sort((a, b) => b.pct - a.pct);

  const highRiskPatients = patientsData?.data ?? [];

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Page header */}
      <motion.div variants={staggerItem}>
        <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">
          Dashboard
        </h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          Post-discharge patient monitoring — Digital Twin overview
        </p>
      </motion.div>

      {/* KPI row */}
      <motion.div variants={staggerContainer} className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statsLoading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonKPICard key={i} />)
        ) : (
          <>
            <KPICard
              title="Total Patients"
              value={totalPatients.toLocaleString()}
              icon={<Users size={18} className="text-[var(--color-primary-500)]" />}
              iconColor="bg-[var(--color-primary-50)]"
            />
            <KPICard
              title="High Risk"
              value={highRiskCount.toLocaleString()}
              unit="patients"
              icon={<AlertTriangle size={18} className="text-[var(--color-danger-500)]" />}
              iconColor="bg-[var(--color-danger-50)]"
            />
            <KPICard
              title="Avg Compliance"
              value={(Math.round(avgCompliance * 10) / 10).toFixed(1)}
              unit="%"
              icon={<ShieldCheck size={18} className="text-[var(--color-success-600)]" />}
              iconColor="bg-[var(--color-success-50)]"
            />
            <KPICard
              title="Readmission Risk"
              value={(Math.round(avgReadmission * 1000) / 10).toFixed(1)}
              unit="%"
              icon={<Activity size={18} className="text-[var(--color-warning-600)]" />}
              iconColor="bg-[var(--color-warning-50)]"
            />
          </>
        )}
      </motion.div>

      {/* Main content row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">

        {/* Risk distribution — reads lowercase API keys correctly */}
        <motion.div variants={staggerItem} className="lg:col-span-1">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Risk Distribution</CardTitle>
                <CardDescription>
                  {totalPatients} active patients
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {RISK_MAP.filter(r => r.key !== "critical" || (riskDist["critical"] ?? 0) > 0).map(r => (
                <ProgressBar
                  key={r.key}
                  label={`${r.label} (${riskDist[r.key] ?? 0})`}
                  value={totalPatients > 0 ? Math.round(((riskDist[r.key] ?? 0) / totalPatients) * 100) : 0}
                  showValue
                  color={r.color}
                />
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* Recovery status — reads snake_case API keys correctly */}
        <motion.div variants={staggerItem} className="lg:col-span-1">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Recovery Status</CardTitle>
                <CardDescription>Current cohort breakdown</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {recoveryRows.map((item) => (
                <div key={item.displayStatus} className="flex items-center justify-between">
                  <RecoveryBadge status={item.displayStatus as RecoveryStatus} size="sm" />
                  <span className="text-xs font-semibold text-[var(--color-foreground)] tabular-nums">
                    {item.pct}%
                  </span>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* Avg compliance ring */}
        <motion.div variants={staggerItem} className="lg:col-span-1">
          <Card className="flex flex-col items-center justify-center min-h-[220px]">
            <CardHeader className="mb-0 w-full">
              <div>
                <CardTitle>Avg Compliance Score</CardTitle>
                <CardDescription>All patients, latest day</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-4 pt-2">
              <ProgressRing
                value={Math.round(avgCompliance)}
                size={120}
                strokeWidth={10}
                color="var(--color-primary-500)"
              />
              <p className="text-xs text-[var(--color-muted)] text-center">
                {highRiskCount} of {totalPatients} patients classified High/Critical risk
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Recent high-risk patients from API */}
      <motion.div variants={staggerItem}>
        <Card padding="none">
          <div className="px-5 py-4 border-b border-[var(--color-border-subtle)] flex items-center justify-between">
            <div>
              <CardTitle>High Risk Patients</CardTitle>
              <CardDescription className="mt-0.5">Top 5 by readmission probability</CardDescription>
            </div>
            <Button
              variant="secondary"
              size="sm"
              rightIcon={<TrendingUp size={14} />}
              onClick={() => navigate({ to: "/patients" })}
            >
              View all
            </Button>
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {patientsLoading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 px-5 py-3.5 animate-pulse">
                    <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700" />
                    <div className="flex-1 space-y-1.5">
                      <div className="h-3 w-40 rounded bg-gray-200 dark:bg-gray-700" />
                      <div className="h-2.5 w-24 rounded bg-gray-200 dark:bg-gray-700" />
                    </div>
                    <div className="h-5 w-14 rounded-full bg-gray-200 dark:bg-gray-700" />
                  </div>
                ))
              : highRiskPatients.map((p) => (
                  <div
                    key={p.Patient_ID}
                    className="flex items-center gap-4 px-5 py-3.5 hover:bg-[var(--color-border-subtle)] transition-colors cursor-pointer"
                    onClick={() => navigate({ to: "/patients/$patientId", params: { patientId: p.Patient_ID } })}
                  >
                    <Avatar name={p.Patient_ID} size="sm" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--color-foreground)] truncate">
                        {p.Patient_ID}
                      </p>
                      <p className="text-xs text-[var(--color-muted)] truncate">
                        {p.Disease_Type} · Day {p.Latest_Day}
                      </p>
                    </div>
                    <RiskBadge level={p.Risk_Level as RiskLevel} size="sm" />
                    <RecoveryBadge status={p.Recovery_Status as RecoveryStatus} size="sm" />
                    <div className="text-right hidden sm:block">
                      <p className="text-sm font-bold text-[var(--color-danger-500)] tabular-nums">
                        {Math.round(p.Readmission_Probability * 100)}%
                      </p>
                      <p className="text-[10px] text-[var(--color-muted)]">readmission</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate({ to: "/patients/$patientId", params: { patientId: p.Patient_ID } });
                      }}
                    >
                      <Stethoscope size={14} />
                    </Button>
                  </div>
                ))
            }
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
