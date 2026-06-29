import { createFileRoute } from "@tanstack/react-router";
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

export const Route = createFileRoute("/_app/")({
  component: DashboardOverview,
});

function DashboardOverview() {
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
          value="3,334"
          trend={2.4}
          trendLabel="vs last week"
          icon={<Users size={18} className="text-[var(--color-primary-500)]" />}
          iconColor="bg-[var(--color-primary-50)]"
        />
        <KPICard
          title="High Risk"
          value="1,385"
          unit="patients"
          trend={-5.2}
          trendLabel="vs last week"
          invertTrend
          icon={<AlertTriangle size={18} className="text-[var(--color-danger-500)]" />}
          iconColor="bg-[var(--color-danger-50)]"
        />
        <KPICard
          title="Avg Compliance"
          value="71.4"
          unit="%"
          trend={3.1}
          trendLabel="vs last week"
          icon={<ShieldCheck size={18} className="text-[var(--color-success-600)]" />}
          iconColor="bg-[var(--color-success-50)]"
        />
        <KPICard
          title="Readmission Risk"
          value="38.6"
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
                value={12}
                showValue
                color="var(--color-success-500)"
              />
              <ProgressBar
                label="Medium Risk"
                value={46}
                showValue
                color="var(--color-warning-500)"
              />
              <ProgressBar
                label="High Risk"
                value={42}
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
              {RECOVERY_DATA.map((item) => (
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
                <CardTitle>Avg Recovery Score</CardTitle>
                <CardDescription>All patients, latest day</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="flex flex-col items-center gap-4 pt-2">
              <ProgressRing
                value={68}
                size={120}
                strokeWidth={10}
                color="var(--color-primary-500)"
              />
              <div className="flex gap-3">
                <Badge variant="success" dot>Improving: 10%</Badge>
                <Badge variant="warning" dot>Delayed: 43%</Badge>
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
            <Button variant="secondary" size="sm" rightIcon={<TrendingUp size={14} />}>
              View all
            </Button>
          </div>
          <div className="divide-y divide-[var(--color-border-subtle)]">
            {SAMPLE_PATIENTS.map((p) => (
              <div
                key={p.id}
                className="flex items-center gap-4 px-5 py-3.5 hover:bg-[var(--color-border-subtle)] transition-colors"
              >
                <Avatar name={p.id} size="sm" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[var(--color-foreground)] truncate">
                    {p.id}
                  </p>
                  <p className="text-xs text-[var(--color-muted)] truncate">
                    {p.disease} · Day {p.day}
                  </p>
                </div>
                <RiskBadge level={p.risk as any} size="sm" />
                <TrendBadge trend={p.trend as any} size="sm" />
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-bold text-[var(--color-danger-500)] tabular-nums">
                    {p.readmission}%
                  </p>
                  <p className="text-[10px] text-[var(--color-muted)]">readmission</p>
                </div>
                <Button variant="ghost" size="icon-sm">
                  <Stethoscope size={14} />
                </Button>
              </div>
            ))}
          </div>
        </Card>
      </motion.div>

      {/* Disease breakdown */}
      <motion.div variants={staggerItem}>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Disease Distribution</CardTitle>
              <CardDescription>Patient count by primary condition</CardDescription>
            </div>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {DISEASE_DATA.map((d) => (
              <div
                key={d.name}
                className="rounded-xl bg-[var(--color-border-subtle)] p-3 text-center"
              >
                <p className="text-lg font-bold text-[var(--color-foreground)] tabular-nums">
                  {d.count.toLocaleString()}
                </p>
                <p className="text-xs text-[var(--color-muted)] mt-0.5">{d.name}</p>
                <div className="mt-2">
                  <ProgressBar value={(d.count / 18240) * 100} size="xs" animated />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}

/* ── Static data ──────────────────────────────────────────────────────── */

const RECOVERY_DATA = [
  { status: "Delayed Recovery", pct: 43.1 },
  { status: "Critical", pct: 18.8 },
  { status: "Worsening", pct: 13.7 },
  { status: "Stable", pct: 12.5 },
  { status: "Improving", pct: 10.4 },
  { status: "Recovered", pct: 1.4 },
];

const SAMPLE_PATIENTS = [
  { id: "HDT-AHD-2026-501118", disease: "Asthma", day: 26, risk: "High", trend: "Declining", readmission: 75.1 },
  { id: "HDT-LCC-2026-450186", disease: "Cardiac", day: 30, risk: "Medium", trend: "Declining", readmission: 59.7 },
  { id: "HDT-KMC-2026-356698", disease: "Kidney Disease", day: 14, risk: "High", trend: "Stable", readmission: 68.7 },
  { id: "HDT-SGH-2026-749915", disease: "Diabetes", day: 22, risk: "High", trend: "Declining", readmission: 71.2 },
  { id: "HDT-NHP-2026-782008", disease: "COPD", day: 18, risk: "Medium", trend: "Stable", readmission: 55.4 },
];

const DISEASE_DATA = [
  { name: "Diabetes", count: 18240 },
  { name: "Hypertension", count: 15630 },
  { name: "Cardiac", count: 15570 },
  { name: "Post Surgery", count: 12360 },
  { name: "Kidney Disease", count: 10920 },
  { name: "COPD", count: 10380 },
  { name: "Asthma", count: 9670 },
  { name: "Stroke Recovery", count: 7230 },
];
