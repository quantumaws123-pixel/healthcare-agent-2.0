import React, { useState } from "react";
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { getStoredUser } from "@/lib/auth";
import { motion } from "framer-motion";
import { AlertTriangle, ChevronRight, Bell, BellOff, RefreshCw, Stethoscope, ShieldAlert } from "lucide-react";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { RiskBadge, RecoveryBadge } from "@/components/ui/StatusBadge";
import { Avatar } from "@/components/ui/Avatar";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonTableRow } from "@/components/ui/Skeleton";
import { usePatients } from "@/hooks/usePatients";
import type { RiskLevel, RecoveryStatus, PatientSummary } from "@/types";

export const Route = createFileRoute("/_app/alerts")({
  beforeLoad: () => {
    const user = getStoredUser();
    if (!user || (user.role !== "admin" && user.role !== "doctor")) {
      throw redirect({ to: "/" });
    }
  },
  component: AlertsPage,
});

// Derive an alert message from the patient's data
function getAlertMessage(p: PatientSummary): string {
  const prob = Math.round(p.Readmission_Probability * 100);
  if (prob >= 98) return `Readmission probability ${prob}% — Immediate hospital readmission protocol required.`;
  if (prob >= 90) return `Critical readmission risk (${prob}%). Immediate doctor review and medication assessment needed.`;
  if (prob >= 80) return `High readmission risk (${prob}%). Compliance score ${p.Compliance_Score.toFixed(0)}% — escalation required.`;
  if (prob >= 70) return `Elevated readmission risk (${prob}%). Increase monitoring frequency and review care plan.`;
  return `Readmission risk ${prob}% with compliance ${p.Compliance_Score.toFixed(0)}% — continue monitoring.`;
}

function getUrgency(prob: number): "critical" | "high" | "medium" {
  if (prob >= 0.85) return "critical";
  if (prob >= 0.70) return "high";
  return "medium";
}

function AlertsPage() {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const { data: highRisk,     isLoading: loadingHigh,    refetch: refetchHigh }     = usePatients({ risk_level: "High",     page_size: 20 });
  const { data: criticalRisk, isLoading: loadingCritical, refetch: refetchCritical } = usePatients({ risk_level: "Critical", page_size: 20 });

  const isLoading = loadingHigh || loadingCritical;

  const allAlerts: PatientSummary[] = [
    ...(criticalRisk?.data ?? []),
    ...(highRisk?.data ?? []),
  ].filter(p => !dismissed.has(p.Patient_ID))
   .sort((a, b) => b.Readmission_Probability - a.Readmission_Probability);

  const criticalCount = allAlerts.filter(p => p.Risk_Level === "Critical").length;
  const highCount     = allAlerts.filter(p => p.Risk_Level === "High").length;
  const lowCompCount  = allAlerts.filter(p => p.Compliance_Score < 50).length;

  const dismissAll = () => setDismissed(new Set(allAlerts.map(p => p.Patient_ID)));

  const refetchAll = () => { setDismissed(new Set()); refetchHigh(); refetchCritical(); };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight flex items-center gap-2">
            <ShieldAlert size={22} className="text-red-500" />
            Risk Alerts
          </h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {isLoading ? "Loading…" : `${allAlerts.length} active alert${allAlerts.length !== 1 ? "s" : ""} requiring attention`}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to="/workbench">
            <Button variant="primary" size="sm" leftIcon={<Stethoscope size={14} />}>
              Open Workbench
            </Button>
          </Link>
          <Button variant="secondary" size="sm" leftIcon={<RefreshCw size={14} />} loading={isLoading} onClick={refetchAll}>
            Refresh
          </Button>
          <Button variant="secondary" size="sm" leftIcon={<BellOff size={14} />} disabled={allAlerts.length === 0} onClick={dismissAll}>
            Dismiss All
          </Button>
        </div>
      </motion.div>

      {/* Summary cards — real counts */}
      <motion.div variants={staggerItem} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="border-l-4 border-red-500">
          <CardContent className="pt-5">
            <p className="text-3xl font-bold text-red-500">{isLoading ? "—" : criticalCount}</p>
            <p className="text-sm text-[var(--color-muted)] mt-1">Critical Risk Patients</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-amber-500">
          <CardContent className="pt-5">
            <p className="text-3xl font-bold text-amber-600 dark:text-amber-400">{isLoading ? "—" : highCount}</p>
            <p className="text-sm text-[var(--color-muted)] mt-1">High Risk Patients</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-primary-500">
          <CardContent className="pt-5">
            <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">{isLoading ? "—" : lowCompCount}</p>
            <p className="text-sm text-[var(--color-muted)] mt-1">Low Compliance (under 50%)</p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Alert list */}
      <motion.div variants={staggerItem}>
        <Card padding="none">
          <div className="px-5 py-4 border-b border-[var(--color-border-subtle)]">
            <CardTitle>Active Alerts</CardTitle>
            <CardDescription className="mt-0.5">
              High-risk patients sorted by readmission probability
            </CardDescription>
          </div>

          {isLoading ? (
            Array.from({ length: 6 }).map((_, i) => <SkeletonTableRow key={i} columns={5} />)
          ) : allAlerts.length === 0 ? (
            <EmptyState
              title="No active alerts"
              description="All high-risk patients have been reviewed or dismissed."
              size="sm"
              className="py-12"
            />
          ) : (
            <div className="divide-y divide-[var(--color-border-subtle)]">
              {allAlerts.map((patient) => (
                <AlertRow
                  key={patient.Patient_ID}
                  patient={patient}
                  onDismiss={() => setDismissed(prev => new Set([...prev, patient.Patient_ID]))}
                />
              ))}
            </div>
          )}
        </Card>
      </motion.div>
    </motion.div>
  );
}

function AlertRow({
  patient: p,
  onDismiss,
}: {
  patient: PatientSummary;
  onDismiss: () => void;
}) {
  const urgency = getUrgency(p.Readmission_Probability);
  const urgencyBorder =
    urgency === "critical"
      ? "border-l-[var(--color-danger-500)] bg-[var(--color-danger-50)]/20"
      : urgency === "high"
      ? "border-l-[var(--color-warning-500)] bg-[var(--color-warning-50)]/20"
      : "border-l-[var(--color-primary-400)]";

  return (
    <div
      className={`flex items-center gap-4 px-5 py-4 border-l-4 ${urgencyBorder} hover:bg-[var(--color-border-subtle)]/30 transition-colors`}
    >
      <Avatar name={p.Patient_ID} size="sm" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="text-sm font-semibold text-[var(--color-foreground)] truncate">
            {p.Patient_ID}
          </p>
          <RiskBadge level={p.Risk_Level as RiskLevel} size="sm" />
          <RecoveryBadge status={p.Recovery_Status as RecoveryStatus} size="sm" />
        </div>
        <p className="text-xs text-[var(--color-muted)] mt-0.5 line-clamp-1">
          {getAlertMessage(p)}
        </p>
        <p className="text-[10px] text-[var(--color-muted)] mt-0.5">
          {p.Disease_Type} · Day {p.Latest_Day} · Compliance {p.Compliance_Score.toFixed(0)}%
        </p>
      </div>
      <div className="text-right shrink-0 hidden sm:block">
        <p className="text-sm font-bold text-[var(--color-danger-500)] tabular-nums">
          {Math.round(p.Readmission_Probability * 100)}%
        </p>
        <p className="text-[10px] text-[var(--color-muted)]">readmission risk</p>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Dismiss alert"
          onClick={onDismiss}
        >
          <BellOff size={13} />
        </Button>
        <Link to="/patients/$patientId" params={{ patientId: p.Patient_ID }}>
          <Button variant="ghost" size="icon-sm" aria-label="View patient">
            <ChevronRight size={14} />
          </Button>
        </Link>
      </div>
    </div>
  );
}


