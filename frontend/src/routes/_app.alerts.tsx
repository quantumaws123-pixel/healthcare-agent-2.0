import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { AlertTriangle, ChevronRight, Clock, Bell, BellOff } from "lucide-react";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge, RecoveryBadge } from "@/components/ui/StatusBadge";
import { Avatar } from "@/components/ui/Avatar";
import { EmptyState } from "@/components/ui/EmptyState";

export const Route = createFileRoute("/_app/alerts")({
  component: AlertsPage,
});

function AlertsPage() {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <motion.div variants={staggerItem} className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">
            Risk Alerts
          </h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {ALERTS.filter(a => !a.dismissed).length} active alerts requiring attention
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" leftIcon={<BellOff size={14} />}>
            Dismiss All
          </Button>
          <Button size="sm" leftIcon={<Bell size={14} />}>
            Configure Alerts
          </Button>
        </div>
      </motion.div>

      {/* Summary cards */}
      <motion.div variants={staggerItem} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="border-l-4 border-[var(--color-danger-500)]">
          <CardContent className="pt-5">
            <p className="text-3xl font-bold text-[var(--color-danger-500)]">3</p>
            <p className="text-sm text-[var(--color-muted)] mt-1">Critical — Immediate Review</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-[var(--color-warning-500)]">
          <CardContent className="pt-5">
            <p className="text-3xl font-bold text-[var(--color-warning-600)]">8</p>
            <p className="text-sm text-[var(--color-muted)] mt-1">High Risk — Increase Monitoring</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-[var(--color-primary-500)]">
          <CardContent className="pt-5">
            <p className="text-3xl font-bold text-[var(--color-primary-600)]">12</p>
            <p className="text-sm text-[var(--color-muted)] mt-1">Medication Non-Compliance</p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Alert list */}
      <motion.div variants={staggerItem}>
        <Card padding="none">
          <div className="px-5 py-4 border-b border-[var(--color-border-subtle)]">
            <CardTitle>Active Alerts</CardTitle>
            <CardDescription className="mt-0.5">Sorted by readmission probability descending</CardDescription>
          </div>
          {ALERTS.filter(a => !a.dismissed).length === 0 ? (
            <EmptyState title="No active alerts" description="All patients are within safe parameters." size="sm" className="py-12" />
          ) : (
            <div className="divide-y divide-[var(--color-border-subtle)]">
              {ALERTS.filter(a => !a.dismissed).map((alert) => (
                <AlertRow key={alert.id} alert={alert} />
              ))}
            </div>
          )}
        </Card>
      </motion.div>
    </motion.div>
  );
}

function AlertRow({ alert }: { alert: typeof ALERTS[0] }) {
  const urgencyColor = alert.urgency === "critical"
    ? "border-l-[var(--color-danger-500)] bg-[var(--color-danger-50)]/20"
    : alert.urgency === "high"
    ? "border-l-[var(--color-warning-500)] bg-[var(--color-warning-50)]/20"
    : "border-l-[var(--color-primary-400)]";

  return (
    <div className={`flex items-center gap-4 px-5 py-4 border-l-4 ${urgencyColor} hover:bg-[var(--color-border-subtle)]/30 transition-colors`}>
      <Avatar name={alert.patientId} size="sm" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-semibold text-[var(--color-foreground)] truncate">{alert.patientId}</p>
          <RiskBadge level={alert.risk as any} size="sm" />
        </div>
        <p className="text-xs text-[var(--color-muted)] mt-0.5">{alert.message}</p>
        <div className="flex items-center gap-1 mt-1 text-[var(--color-muted)]">
          <Clock size={10} />
          <span className="text-[10px]">{alert.time}</span>
        </div>
      </div>
      <div className="text-right shrink-0 hidden sm:block">
        <p className="text-sm font-bold text-[var(--color-danger-500)] tabular-nums">{alert.readmission}%</p>
        <p className="text-[10px] text-[var(--color-muted)]">readmission risk</p>
      </div>
      <Link to="/patients/$patientId" params={{ patientId: alert.patientId }}>
        <Button variant="ghost" size="icon-sm"><ChevronRight size={14} /></Button>
      </Link>
    </div>
  );
}

const ALERTS = [
  { id: 1, patientId: "HDT-NHP-2026-693424", risk: "High", urgency: "critical", readmission: 82.9, message: "Readmission probability >80%. Immediate doctor review required.", time: "2 min ago", dismissed: false },
  { id: 2, patientId: "HDT-SGH-2026-749915", risk: "High", urgency: "critical", readmission: 71.2, message: "3 consecutive missed medications. Compliance score dropped to 38%.", time: "15 min ago", dismissed: false },
  { id: 3, patientId: "HDT-SGH-2026-996501", risk: "High", urgency: "critical", readmission: 78.5, message: "SpO₂ dropped below 94%. Worsening recovery trend.", time: "32 min ago", dismissed: false },
  { id: 4, patientId: "HDT-AHD-2026-501118", risk: "High", urgency: "high", readmission: 75.1, message: "6-day declining health trend. Respiratory infection recorded.", time: "1 hour ago", dismissed: false },
  { id: 5, patientId: "HDT-KMC-2026-356698", risk: "High", urgency: "high", readmission: 68.7, message: "Cardiac stress event logged. Medication adjustment recommended.", time: "2 hours ago", dismissed: false },
  { id: 6, patientId: "HDT-LCC-2026-450186", risk: "Medium", urgency: "medium", readmission: 59.7, message: "Deviation score increased to 29.7. Exercise non-compliance for 7 days.", time: "3 hours ago", dismissed: false },
];
