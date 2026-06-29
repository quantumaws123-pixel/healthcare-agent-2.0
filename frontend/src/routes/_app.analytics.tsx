import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  BarChart3, TrendingUp, Users, Calendar,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area,
} from "recharts";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { KPICard } from "@/components/ui/KPICard";
import { Tabs, TabList, TabTrigger, TabPanels, TabPanel } from "@/components/ui/Tabs";

export const Route = createFileRoute("/_app/analytics")({
  component: AnalyticsPage,
});

const RISK_COLORS = { Low: "#22c55e", Medium: "#f59e0b", High: "#f43f5e" };
const RECOVERY_COLORS = {
  Recovered: "#22c55e", Improving: "#3b82f6", Stable: "#6366f1",
  "Delayed Recovery": "#f59e0b", Worsening: "#f97316", Critical: "#f43f5e",
};

function AnalyticsPage() {
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
          Population-level insights across all 3,334 patients
        </p>
      </motion.div>

      {/* KPIs */}
      <motion.div variants={staggerContainer} className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPICard title="Total Observations" value="100K" unit="rows" trend={0} icon={<BarChart3 size={18} className="text-[var(--color-primary-500)]" />} iconColor="bg-[var(--color-primary-50)]" />
        <KPICard title="Avg Monitoring Days" value="30" unit="days/patient" trend={0} icon={<Calendar size={18} className="text-[var(--color-success-600)]" />} iconColor="bg-[var(--color-success-50)]" />
        <KPICard title="Readmission Events" value="24%" unit="of patients" trend={-2.1} trendLabel="improvement" invertTrend icon={<TrendingUp size={18} className="text-[var(--color-warning-600)]" />} iconColor="bg-[var(--color-warning-50)]" />
        <KPICard title="High Compliance" value="38%" unit="patients >80%" trend={3.2} icon={<Users size={18} className="text-[var(--color-primary-600)]" />} iconColor="bg-[var(--color-primary-50)]" />
      </motion.div>

      <motion.div variants={staggerItem}>
        <Tabs defaultTab="overview" variant="line">
          <TabList>
            <TabTrigger id="overview">Overview</TabTrigger>
            <TabTrigger id="disease">By Disease</TabTrigger>
            <TabTrigger id="compliance">Compliance</TabTrigger>
            <TabTrigger id="trends">Trends</TabTrigger>
          </TabList>
          <TabPanels>
            {/* Overview */}
            <TabPanel id="overview">
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 mt-4">
                <Card>
                  <CardHeader><CardTitle>Risk Level Distribution</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={220}>
                      <PieChart>
                        <Pie data={RISK_PIE} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                          {RISK_PIE.map((entry) => (
                            <Cell key={entry.name} fill={RISK_COLORS[entry.name as keyof typeof RISK_COLORS]} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader><CardTitle>Recovery Status Distribution</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={RECOVERY_BAR} layout="vertical" margin={{ right: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis type="number" tick={{ fontSize: 11 }} />
                        <YAxis dataKey="status" type="category" tick={{ fontSize: 10 }} width={100} />
                        <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                        <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                          {RECOVERY_BAR.map((entry) => (
                            <Cell key={entry.status} fill={RECOVERY_COLORS[entry.status as keyof typeof RECOVERY_COLORS]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabPanel>

            {/* Disease */}
            <TabPanel id="disease">
              <div className="mt-4 space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Patients by Disease Type</CardTitle>
                    <CardDescription>Rows in dataset per disease category</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={DISEASE_BAR}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="disease" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" height={50} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                        <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Average Readmission Risk by Disease</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={DISEASE_RISK}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="disease" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" height={50} />
                        <YAxis domain={[0, 70]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                        <Bar dataKey="avgRisk" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabPanel>

            {/* Compliance */}
            <TabPanel id="compliance">
              <div className="mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Compliance Score Distribution</CardTitle>
                    <CardDescription>All patients, day 30</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={COMPLIANCE_HIST}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="range" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                        <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </TabPanel>

            {/* Trends */}
            <TabPanel id="trends">
              <div className="mt-4 space-y-6">
                <Card>
                  <CardHeader><CardTitle>Avg Compliance — Population Trend over 30 Days</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={220}>
                      <AreaChart data={POP_TREND}>
                        <defs>
                          <linearGradient id="popGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[50, 90]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                        <Area type="monotone" dataKey="compliance" name="Avg Compliance" stroke="#3b82f6" fill="url(#popGrad)" strokeWidth={2} dot={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle>Avg Readmission Risk — Population Trend</CardTitle></CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={POP_TREND}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                        <YAxis domain={[20, 60]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={{ borderRadius: "12px", fontSize: 12 }} />
                        <Line type="monotone" dataKey="readmission" name="Avg Readmission Risk" stroke="#f43f5e" strokeWidth={2} dot={false} />
                      </LineChart>
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

/* ── Static data ────────────────────────────────────────────────────────── */
const RISK_PIE = [
  { name: "Low", value: 12107 },
  { name: "Medium", value: 46278 },
  { name: "High", value: 41615 },
];

const RECOVERY_BAR = [
  { status: "Delayed Recovery", count: 43108 },
  { status: "Critical", count: 18833 },
  { status: "Worsening", count: 13660 },
  { status: "Stable", count: 12544 },
  { status: "Improving", count: 10429 },
  { status: "Recovered", count: 1426 },
];

const DISEASE_BAR = [
  { disease: "Diabetes", count: 18240 },
  { disease: "Hypertension", count: 15630 },
  { disease: "Cardiac", count: 15570 },
  { disease: "Post Surgery", count: 12360 },
  { disease: "Kidney Disease", count: 10920 },
  { disease: "COPD", count: 10380 },
  { disease: "Asthma", count: 9670 },
  { disease: "Stroke Recovery", count: 7230 },
];

const DISEASE_RISK = [
  { disease: "Stroke Recovery", avgRisk: 62 },
  { disease: "COPD", avgRisk: 55 },
  { disease: "Cardiac", avgRisk: 52 },
  { disease: "Kidney Disease", avgRisk: 48 },
  { disease: "Post Surgery", avgRisk: 44 },
  { disease: "Diabetes", avgRisk: 39 },
  { disease: "Hypertension", avgRisk: 35 },
  { disease: "Asthma", avgRisk: 38 },
];

const COMPLIANCE_HIST = [
  { range: "0–20", count: 892 },
  { range: "20–40", count: 4215 },
  { range: "40–60", count: 18930 },
  { range: "60–80", count: 52440 },
  { range: "80–100", count: 23523 },
];

const POP_TREND = Array.from({ length: 30 }, (_, i) => ({
  day: i + 1,
  compliance: 72 - i * 0.3 + Math.sin(i * 0.4) * 3,
  readmission: 31 + i * 0.4 + Math.cos(i * 0.5) * 2,
}));
