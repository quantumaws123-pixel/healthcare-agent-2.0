import React from "react";
import { Users, Heart, TrendingUp, AlertTriangle, FileText, Activity, Loader2 } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { FloatingPanel } from "@/components/ui/FloatingPanel";
import { StatCard } from "@/components/ui/StatCard";
import { useDashboardStats, usePatients } from "@/hooks/usePatients";

export function DoctorDashboard() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: patientsData, isLoading: patientsLoading } = usePatients({ page_size: 100 });

  if (statsLoading || patientsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-primary-500" size={32} />
      </div>
    );
  }

  const totalPatients = patientsData?.total ?? 0;
  const highRiskCount = stats?.risk_distribution ? (stats.risk_distribution.high + stats.risk_distribution.critical) : 0;
  const avgCompliance = stats?.avg_compliance ? `${Math.round(stats.avg_compliance)}%` : "N/A";

  // Filter high/critical risk patients
  const highRiskPatients = (patientsData?.data ?? []).filter(
    p => p.Risk_Level === "High" || p.Risk_Level === "Critical"
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Doctor Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Monitor and manage your patients</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Patients"
          value={String(totalPatients)}
          icon={Users}
          color="blue"
        />
        <StatCard
          label="Monitoring Active"
          value={String(totalPatients)}
          icon={Heart}
          color="green"
        />
        <StatCard
          label="High Risk Alerts"
          value={String(highRiskCount)}
          icon={AlertTriangle}
          color="red"
        />
        <StatCard
          label="Avg Compliance"
          value={avgCompliance}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* High Risk Patients */}
      <FloatingPanel>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <AlertTriangle className="text-red-500" size={20} />
          High Risk Alerts ({highRiskPatients.length})
        </h2>
        {highRiskPatients.length === 0 ? (
          <p className="text-sm text-gray-500 py-4 text-center">No high risk patients currently monitored.</p>
        ) : (
          <div className="space-y-3">
            {highRiskPatients.map((patient) => (
              <Link
                key={patient.Patient_ID}
                to="/patients/$patientId"
                params={{ patientId: patient.Patient_ID }}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 transition-all cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                    <span className="text-sm font-semibold text-red-600 dark:text-red-400">
                      {patient.Gender === "Male" ? "Mr" : "Ms"}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">Patient {patient.Patient_ID}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{patient.Disease_Type} · Age {patient.Age}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-red-600 dark:text-red-400">
                    {Math.round(patient.Readmission_Probability * 100)}%
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Risk Prob.</p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </FloatingPanel>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/patients"
          className="flex items-start gap-3 p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all group cursor-pointer"
        >
          <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center group-hover:bg-primary-200 dark:group-hover:bg-primary-900/50 transition-colors">
            <Users size={20} className="text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">View Patients</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{totalPatients} total</p>
          </div>
        </Link>
        <Link
          to="/twins"
          className="flex items-start gap-3 p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all group cursor-pointer"
        >
          <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center group-hover:bg-primary-200 dark:group-hover:bg-primary-900/50 transition-colors">
            <Activity size={20} className="text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">Digital Twins</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Real-time simulation</p>
          </div>
        </Link>
        <Link
          to="/alerts"
          className="flex items-start gap-3 p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all group cursor-pointer"
        >
          <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center group-hover:bg-primary-200 dark:group-hover:bg-primary-900/50 transition-colors">
            <AlertTriangle size={20} className="text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900 dark:text-white">Risk Alerts</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{highRiskPatients.length} active</p>
          </div>
        </Link>
      </div>
    </div>
  );
}
