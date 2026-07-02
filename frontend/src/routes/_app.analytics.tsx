import { createFileRoute, redirect } from "@tanstack/react-router";
import { getStoredUser } from "@/lib/auth";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, Users, ShieldCheck } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { KPICard } from "@/components/ui/KPICard";
import { SkeletonKPICard, SkeletonCard } from "@/components/ui/Skeleton";
import { Tabs, TabList, TabTrigger, TabPanels, TabPanel } from "@/components/ui/Tabs";
import { useDashboardStats } from "@/hooks/usePatients";

export const Route = createFileRoute("/_app/analytics")({
  beforeLoad: () => {
    const user = getStoredUser();
    if (!user || (user.role !== "admin" && user.role !== "doctor")) {
      throw redirect({ to: "/" });
    }
  },
  component: AnalyticsPage,
});

// Maps API lowercase keys → display labels
const RISK_LABEL: Record<string, string> = {
  low: "Low", medium: "Medium", high: "High", critical: "Critical",
};
const RISK_COLORS: Record<string, string> = {
  low: "#22c55e", medium: "#f59e0b", high: "#f43f5e", critical: "#9333ea",
};
const RECOVERY_LABEL: Record<string, string> = {
  recovered:        "Recovered",
  improving:        "Improving",
  stable:           "Stable",
  delayed_recovery: "Delayed Recovery",
  worsening:        "Worsening",
  critical:         "Critical",
};
const RECOVERY_COLORS: Record<string, string> = {
  recovered:        "#22c55e",
  improving:        "#3b82f6",
  stable:           "#6366f1",
  delayed_recovery: "#f59e0b",
  worsening:        "#f97316",
  critical:         "#f43f5e",
};

function AnalyticsPage() {
  const { data: stats, isLoading } = useDashboardStats();

  // Build chart data from real API response
  const riskDist     = (stats?.risk_distribution     ?? {}) as Record<string, number>;
  const recoveryDist = (stats?.recovery_distribution ?? {}) as Record<string, number>;

  const riskPieData = Object.entries(riskDist)
    .filter(([, v]) => v > 0)
    .map(([key, value]) => ({
      name:  RISK_LABEL[key] ?? key,
      value,
      key,
    }));

  const recoveryBarData = Object.entries(recoveryDist)
    .map(([key, count]) => ({
      status: RECOVERY_LABEL[key] ?? key,
      count,
      key,
    }))
    .sort((a, b) => b.count - a.count);

  const totalPatients      = stats?.total_patients ?? 0;
  const highRiskCount      = stats?.high_risk_count ?? 0;
  const avgCompliance      = stats?.avg_compliance ?? 0;
  const avgReadmission     = stats?.avg_readmission_probability ?? 0;
  const highComplianceEst  = Math.round(((100 - avgReadmission * 100) / 100) * totalPatients);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <motion.div variants={staggerItem}>
        <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">Analytics</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">
          {isLoading ? "Loading…" : `Population-level insights across ${totalPatients} active patients`}
        </p>
      </motion.div>

      {/* KPIs — all from real API */}
      <motion.div variants={staggerContainer} className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonKPICard key={i} />)
        ) : (
          <>
            <KPICard
              title="Total Patients"
              value={totalPatients.toLocaleString()}
              icon={<Users size={18} className="text-[var(--color-primary-500)]" />}
              iconColor="bg-[var(--color-primary-50)] dark:bg-primary-900/30"
            />
            <KPICard
              title="High / Critical Risk"
              value={highRiskCount.toLocaleString()}
              unit={totalPatients > 0 ? `(${Math.round(highRiskCount / totalPatients * 100)}%)` : ""}
              icon={<BarChart3 size={18} className="text-[var(--color-danger-500)]" />}
              iconColor="bg-[var(--color-danger-50)] dark:bg-red-900/30"
            />
            <KPICard
              title="Avg Compliance"
              value={(Math.round(avgCompliance * 10) / 10).toFixed(1)}
              unit="%"
              icon={<ShieldCheck size={18} className="text-[var(--color-success-600)]" />}
              iconColor="bg-[var(--color-success-50)] dark:bg-green-900/30"
              description={avgCompliance >= 75 ? "✓ Above target (75%)" : "⚠ Below 75% target"}
            />
            <KPICard
              title="Avg Readmission Risk"
              value={(Math.round(avgReadmission * 1000) / 10).toFixed(1)}
              unit="%"
              icon={<TrendingUp size={18} className="text-[var(--color-warning-600)]" />}
              iconColor="bg-[var(--color-warning-50)] dark:bg-amber-900/30"
              invertTrend
            />
          </>
        )}
      </motion.div>

      {/* Insight callouts */}
      {!isLoading && stats && (
        <motion.div variants={staggerItem} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="rounded-xl p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/50 text-sm">
            <p className="font-semibold text-blue-800 dark:text-blue-300">📊 Risk Insight</p>
            <p className="text-blue-700 dark:text-blue-400 mt-0.5 text-xs">
              {highRiskCount} of {totalPatients} patients ({totalPatients > 0 ? Math.round(highRiskCount / totalPatients * 100) : 0}%) are High or Critical risk and need intervention.
            </p>
          </div>
          <div className="rounded-xl p-3 bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800/50 text-sm">
            <p className="font-semibold text-green-800 dark:text-green-300">✅ Compliance Status</p>
            <p className="text-green-700 dark:text-green-400 mt-0.5 text-xs">
              System-wide average compliance is {avgCompliance.toFixed(1)}%. {avgCompliance >= 75 ? "Platform is performing above target." : "Below the 75% clinical target — review care plans."}
            </p>
          </div>
          <div className="rounded-xl p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800/50 text-sm">
            <p className="font-semibold text-amber-800 dark:text-amber-300">⚠ Readmission Risk</p>
            <p className="text-amber-700 dark:text-amber-400 mt-0.5 text-xs">
              Average readmission probability is {(avgReadmission * 100).toFixed(1)}%. {avgReadmission < 0.3 ? "Risk is well-managed." : "Focused compliance improvements are needed."}
            </p>
          </div>
        </motion.div>
      )}

      <motion.div variants={staggerItem}>
        <Tabs defaultTab="overview" variant="line">
          <TabList>
            <TabTrigger id="overview">Overview</TabTrigger>
            <TabTrigger id="recovery">Recovery</TabTrigger>
          </TabList>
          <TabPanels>

            {/* Overview — risk pie + compliance */}
            <TabPanel id="overview">
              {isLoading ? (
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mt-4">
                  <SkeletonCard /><SkeletonCard />
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Risk Level Distribution</CardTitle>
                      <CardDescription>{totalPatients} patients (latest record per patient)</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={240}>
                        <PieChart>
                          <Pie
                            data={riskPieData}
                            dataKey="value"
                            nameKey="name"
                            cx="50%"
                            cy="50%"
                            outerRadius={90}
                            label={({ name, value, percent }) =>
                              `${name}: ${value} (${(percent * 100).toFixed(0)}%)`
                            }
                            labelLine={false}
                          >
                            {riskPieData.map((entry) => (
                              <Cell key={entry.key} fill={RISK_COLORS[entry.key] ?? "#94a3b8"} />
                            ))}
                          </Pie>
                          <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Risk Count by Level</CardTitle>
                      <CardDescription>Absolute patient counts</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={240}>
                        <BarChart
                          data={riskPieData}
                          margin={{ top: 8, right: 16, left: 0, bottom: 8 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                          <Bar dataKey="value" name="Patients" radius={[6, 6, 0, 0]}>
                            {riskPieData.map((entry) => (
                              <Cell key={entry.key} fill={RISK_COLORS[entry.key] ?? "#94a3b8"} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>
              )}
            </TabPanel>

            {/* Recovery distribution */}
            <TabPanel id="recovery">
              {isLoading ? (
                <div className="mt-4"><SkeletonCard /></div>
              ) : (
                <div className="mt-4 space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Recovery Status Distribution</CardTitle>
                      <CardDescription>All {totalPatients} patients, latest monitoring day</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={260}>
                        <BarChart
                          data={recoveryBarData}
                          layout="vertical"
                          margin={{ right: 24, left: 8 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                          <XAxis type="number" tick={{ fontSize: 11 }} />
                          <YAxis
                            dataKey="status"
                            type="category"
                            tick={{ fontSize: 10 }}
                            width={110}
                          />
                          <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                          <Bar dataKey="count" name="Patients" radius={[0, 6, 6, 0]}>
                            {recoveryBarData.map((entry) => (
                              <Cell
                                key={entry.key}
                                fill={RECOVERY_COLORS[entry.key] ?? "#94a3b8"}
                              />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  {/* Summary table */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Recovery Breakdown</CardTitle>
                      <CardDescription>Counts and percentages</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="divide-y divide-[var(--color-border-subtle)]">
                        {recoveryBarData.map((entry) => (
                          <div key={entry.key} className="flex items-center justify-between py-2">
                            <span className="text-sm text-[var(--color-foreground)]">
                              {entry.status}
                            </span>
                            <div className="flex items-center gap-3">
                              <div
                                className="w-2 h-2 rounded-full shrink-0"
                                style={{ background: RECOVERY_COLORS[entry.key] ?? "#94a3b8" }}
                              />
                              <span className="text-sm font-semibold tabular-nums text-[var(--color-foreground)]">
                                {entry.count}
                              </span>
                              <span className="text-xs text-[var(--color-muted)] w-10 text-right">
                                {totalPatients > 0 ? Math.round((entry.count / totalPatients) * 100) : 0}%
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}
            </TabPanel>

          </TabPanels>
        </Tabs>
      </motion.div>
    </motion.div>
  );
}
