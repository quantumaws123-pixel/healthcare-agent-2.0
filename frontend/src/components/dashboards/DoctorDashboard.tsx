import React, { useState } from "react";
import { Users, Heart, TrendingUp, AlertTriangle, FileText, Activity, Loader2, ClipboardList, Bot, Stethoscope } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { FloatingPanel } from "@/components/ui/FloatingPanel";
import { StatCard } from "@/components/ui/StatCard";
import { Button } from "@/components/ui/Button";
import { useDashboardStats, usePatients } from "@/hooks/usePatients";
import { getMyDoctorPatients, hospitalQueryKeys } from "@/lib/api";
import { CarePlanEditor } from "@/components/doctor/CarePlanEditor";

export function DoctorDashboard() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: patientsData, isLoading: patientsLoading } = usePatients({ page_size: 100 });
  const [carePlanOpen, setCarePlanOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState<{ id: string; name?: string } | null>(null);

  const { data: myPatients = [], isLoading: myPatientsLoading } = useQuery({
    queryKey: hospitalQueryKeys.myDoctorPatients(),
    queryFn: getMyDoctorPatients,
  });

  const isLoading = statsLoading || patientsLoading || myPatientsLoading;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-primary-500" size={32} />
      </div>
    );
  }

  const totalPatients = patientsData?.total ?? 0;
  const highRiskCount = stats?.risk_distribution ? (stats.risk_distribution.high + stats.risk_distribution.critical) : 0;
  const avgCompliance = stats?.avg_compliance ? `${Math.round(stats.avg_compliance)}%` : "N/A";
  const assignedCount = myPatients.length;

  const highRiskPatients = (patientsData?.data ?? []).filter(
    p => p.Risk_Level === "High" || p.Risk_Level === "Critical"
  );

  const openCarePlan = (patId: string, patName?: string) => {
    setSelectedPatient({ id: patId, name: patName });
    setCarePlanOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Doctor Dashboard</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Monitor and manage your patients</p>
        </div>
        <Link to="/workbench">
          <Button variant="primary" leftIcon={<Stethoscope size={15} />}>
            Open Workbench
          </Button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="My Assigned Patients" value={String(assignedCount)} icon={Users} color="blue" />
        <StatCard label="Total in System" value={String(totalPatients)} icon={Heart} color="green" />
        <StatCard label="High Risk Alerts" value={String(highRiskCount)} icon={AlertTriangle} color="red" />
        <StatCard label="Avg Compliance" value={avgCompliance} icon={TrendingUp} color="purple" />
      </div>

      {/* AI Assistant CTA */}
      <Link to="/assistant">
        <div className="flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-r from-primary-500 to-blue-600 hover:from-primary-600 hover:to-blue-700 transition-all cursor-pointer shadow-md group">
          <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
            <Bot size={20} className="text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-white">AI Clinical Assistant</p>
            <p className="text-xs text-white/80 mt-0.5">
              "Why is this patient high risk?" · "Explain the prediction." · "Show compliance summary."
            </p>
          </div>
          <div className="text-white/60 group-hover:text-white transition-colors text-xs font-medium">
            Ask →
          </div>
        </div>
      </Link>

      {/* My Assigned Patients */}
      {myPatients.length > 0 && (
        <FloatingPanel>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Users className="text-primary-500" size={20} />
            My Patients ({myPatients.length})
          </h2>
          <div className="space-y-2">
            {myPatients.map(p => (
              <div key={p.user_id}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center text-sm font-semibold text-primary-600">
                    {(p.name ?? p.email)[0]?.toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">{p.name ?? p.email}</p>
                    <p className="text-xs text-gray-500">{p.disease_type ?? "—"} · {p.gender ?? "—"} · Age {p.age ?? "—"}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {!p.onboarding_completed && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/20 dark:text-amber-400">
                      Onboarding pending
                    </span>
                  )}
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    p.patient_status === "Monitoring" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"
                  }`}>
                    {p.patient_status ?? "Active"}
                  </span>
                  <Button size="xs" variant="secondary"
                    leftIcon={<ClipboardList size={11} />}
                    onClick={() => openCarePlan(p.user_id, p.name ?? undefined)}
                  >
                    Care Plan
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </FloatingPanel>
      )}

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

      {/* Care Plan Editor modal */}
      {selectedPatient && (
        <CarePlanEditor
          open={carePlanOpen}
          onClose={() => { setCarePlanOpen(false); setSelectedPatient(null); }}
          patientUserId={selectedPatient.id}
          patientName={selectedPatient.name}
        />
      )}
    </div>
  );
}
