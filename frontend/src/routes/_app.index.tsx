import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Activity, AlertTriangle, Users, TrendingUp, ShieldCheck, Stethoscope } from "lucide-react";
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
import { useAuthContext } from "@/context/AuthContext";
import type { RiskLevel, RecoveryStatus } from "@/types";

import { AdminDashboard } from "@/components/dashboards/AdminDashboard";
import { DoctorDashboard } from "@/components/dashboards/DoctorDashboard";
import { PatientDashboard } from "@/components/dashboards/PatientDashboard";

export const Route = createFileRoute("/_app/")({ component: DashboardOverview });

const RISK_MAP = [
  { key: "low",      label: "Low Risk",      color: "var(--color-success-500)" },
  { key: "medium",   label: "Medium Risk",   color: "var(--color-warning-500)" },
  { key: "high",     label: "High Risk",     color: "var(--color-danger-500)"  },
  { key: "critical", label: "Critical Risk", color: "#9333ea" },
];

const RECOVERY_KEY_MAP: Record<string, RecoveryStatus> = {
  recovered: "Recovered", improving: "Improving", stable: "Stable",
  delayed_recovery: "Delayed Recovery", worsening: "Worsening", critical: "Critical",
};

function DashboardOverview() {
  const { user } = useAuthContext();
  const role = user?.role;

  if (role === "admin") {
    return <AdminDashboard />;
  }
  if (role === "doctor") {
    return <DoctorDashboard />;
  }
  if (role === "patient") {
    return <PatientDashboard />;
  }

  // Fallback (should not be reached under normal authenticated circumstances)
  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-bold">Welcome</h2>
      <p className="text-gray-500 mt-2">Please contact your administrator if you cannot see your dashboard.</p>
    </div>
  );
}
