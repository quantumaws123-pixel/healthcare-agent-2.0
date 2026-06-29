import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  Users,
  TrendingUp,
  Heart,
  Brain,
  ShieldCheck,
  Stethoscope,
} from "lucide-react";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { KPICard } from "@/components/ui/KPICard";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { RiskBadge, RecoveryBadge, TrendBadge } from "@/components/ui/StatusBadge";
import { Avatar } from "@/components/ui/Avatar";

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useDashboardStats, usePatients } from "@/hooks/usePatients";

export const Route = createFileRoute("/_app/")({
  component: DashboardOverview,
});

function DashboardOverview() {
  const navigate = useNavigate();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: patientsData, isLoading: patientsLoading } = usePatients({
    risk_level: "High",
    page_size: 5,
  });

  if (statsLoading || patientsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary-500)]" />
      </div>
    );
  }

  const kpis = {
    totalPatients: stats?.total_patients ?? 0,
    highRiskCount: stats?.high_risk_count ?? 0,
    avgCompliance: stats?.avg_compliance ?? 0,
    avgReadmissionProbability: stats?.avg_readmission_probability ?? 0,
  };

  const riskDistribution = stats?.risk_distribution ?? { Low: 0, Medium: 0, High: 0, Critical: 0 };
  const recoveryDistribution = stats?.recovery_distribution ?? {};

  // Map recovery status counts to percentages for display
  const totalRecovery = (Object.values(recoveryDistribution) as number[]).reduce((a, b) => a + b, 0) || 1;
  const recoveryDataMapped = Object.entries(recoveryDistribution).map(([status, count]) => ({
    status,
    pct: Math.round(((count as number) / totalRecovery) * 1000) / 10,
    count: count as number,
  })).sort((a, b) => b.count - a.count);

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
      <motion.div
        variants={staggerContainer}
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <KPICard
          title="Total Patients"
          value={kpis.totalPatients.toLocaleString()}
          trend={2.4}
          trendLabel="vs last week"
          icon={<Users size={18} className="text-[var(--color-primary-500)]" />}
          iconColor="bg-[var(--color-primary-50)]"
        />
        <KPICard
          title="High Risk"
          value={kpis.highRiskCount.toLocaleString()}
          unit="patients"
          trend={-5.2}
          trendLabel="vs last week"
          invertTrend
          icon={<AlertTriangle size={18} className="text-[var(--color-danger-500)]" />}
          iconColor="bg-[var(--color-danger-50)]"
        />
        <KPICard
          title="Avg Compliance"
          value={(Math.round(kpis.avgCompliance * 10) / 10).toString()}
          unit="%"
          trend={3.1}
          trendLabel="vs last week"
          icon={<ShieldCheck size={18} className="text-[var(--color-success-600)]" />}
          iconColor="bg-[var(--color-success-50)]"
        />
        <KPICard
          title="Readmission Risk"
          value={(Math.round(kpis.avgReadmissionProbability * 1000) / 10).toString()}
          unit="%"
          trend={-1.8}
          trendLabel="vs last week"
          invertTrend
          icon={<Activity size={18} className="text-[var(--color-warning-600)]" />}
          iconColor="bg-[var(--color-warning-50)]"
        />
      </motion.div>

      {/* Main content row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Risk distribution */}
        <motion.div variants={staggerItem} className="lg:col-span-1">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Risk Distribution</CardTitle>
                <CardDescription>Across all active patients</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <ProgressBar
                label="Low Risk"
                value={Math.round((riskDistribution.Low / kpis.totalPatients) * 100) || 0}
                showValue
                color="var(--color-success-500)"
              />
              <ProgressBar
                label="Medium Risk"
                value={Math.round((riskDistribution.Medium / kpis.totalPatients) * 100) || 0}
                showValue
                color="var(--color-warning-500)"
              />
              <ProgressBar
                label="High Risk"
                value={Math.round(((riskDistribution.High + (riskDistribution.Critical ?? 0)) / kpis.totalPatients) * 100) || 0}
                showValue
                color="var(--color-danger-500)"
              />
            </CardContent>
          </Card>
        </motion.div>

        {/* Recovery status */}
        <motion.div variants={staggerItem} className="lg:col-span-1">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Recovery Status</CardTitle>
                <CardDescription>Current cohort breakdown</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {recoveryDataMapped.map((item) => (
                <div key={item.status} className="flex items-center justify-between">
                  <RecoveryBadge status={item.status as any} size="sm" />
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-[var(--color-foreground)] tabular-nums">
                      {item.pct}%
                    </span>
                  </div>
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
                value={Math.round(kpis.avgCompliance)}
                size={120}
                strokeWidth={10}
                color="var(--color-primary-500)"
              />
              <div className="flex gap-3">
                <Badge variant="success" dot>Improving</Badge>
                <Badge variant="warning" dot>Monitored</Badge>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Recent high-risk patients */}
      <motion.div variants={staggerItem}>
        <Card padding="none">
          <div className="px-5 py-4 border-b border-[var(--color-border-subtle)] flex items-center justify-between">
            <div>
              <CardTitle>High Risk Patients</CardTitle>
              <CardDescription className="mt-0.5">Requiring immediate attention</CardDescription>
            </div>
            <Button variant="secondary" size="sm" rightIcon={<TrendingUp size={14} />} onClick={() => navigate({ to: "/patients" })}>
              View all
            </Button>
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {highRiskPatients.map((p) => (
              <div
                key={p.Patient_ID}
                className="flex items-center gap-4 px-5 py-3.5 hover:bg-[var(--color-border-subtle)] transition-colors cursor-pointer"
                onClick={() => navigate({ to: `/patients/${p.Patient_ID}` })}
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
                <RiskBadge level={p.Risk_Level as any} size="sm" />
                <RecoveryBadge status={p.Recovery_Status as any} size="sm" />
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-bold text-[var(--color-danger-500)] tabular-nums">
                    {Math.round(p.Readmission_Probability * 100)}%
                  </p>
                  <p className="text-[10px] text-[var(--color-muted)]">readmission</p>
                </div>
                <Button variant="ghost" size="icon-sm" onClick={(e) => { e.stopPropagation(); navigate({ to: `/patients/${p.Patient_ID}` }); }}>
                  <Stethoscope size={14} />
                </Button>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}
