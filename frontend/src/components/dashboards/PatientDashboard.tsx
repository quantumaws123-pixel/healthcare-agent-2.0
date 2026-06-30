import React from "react";
import { Heart, Activity, TrendingUp, Pill, FileText, Loader2 } from "lucide-react";
import { FloatingPanel } from "@/components/ui/FloatingPanel";
import { StatCard } from "@/components/ui/StatCard";
import { useAuthContext } from "@/context/AuthContext";
import { usePatientLatest } from "@/hooks/usePatients";

export function PatientDashboard() {
  const { user } = useAuthContext();
  const { data: record, isLoading, error } = usePatientLatest(user?.id ?? "");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-primary-500" size={32} />
      </div>
    );
  }

  if (error || !record) {
    return (
      <div className="p-8 text-center bg-white dark:bg-gray-900 rounded-3xl border border-gray-100 dark:border-gray-800">
        <Heart className="mx-auto text-gray-400 mb-3" size={48} />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">No Health Records Yet</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-2">
          Your digital twin profile is being prepared. Please check back shortly or contact medical staff.
        </p>
      </div>
    );
  }

  const riskPercent = Math.round((record.readmission_probability ?? 0) * 100);
  const complianceVal = Math.round(record.compliance_score ?? 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">My Health Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Monitor your recovery progress in real-time</p>
      </div>

      {/* Health Summary Card */}
      <FloatingPanel className="bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 border-primary-200 dark:border-primary-800">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-primary-600 dark:text-primary-400">Your Readmission Risk</p>
            <p className="text-4xl font-bold text-primary-900 dark:text-primary-100 mt-2">{riskPercent}%</p>
            <p className="text-sm text-primary-700 dark:text-primary-300 mt-1">
              {record.risk_level} Risk · {record.health_trend ?? "Stable"}
            </p>
          </div>
          <div className="w-24 h-24 rounded-full bg-primary-100 dark:bg-primary-900/40 flex items-center justify-center">
            <Heart size={40} className="text-primary-600 dark:text-primary-400" />
          </div>
        </div>
      </FloatingPanel>

      {/* Vitals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Heart Rate"
          value={`${record.heart_rate} bpm`}
          icon={Activity}
          color="red"
        />
        <StatCard
          label="Blood Pressure"
          value={`${record.systolic_bp}/${record.diastolic_bp}`}
          icon={Heart}
          color="blue"
        />
        <StatCard
          label="SpO2"
          value={`${record.spo2}%`}
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          label="Compliance"
          value={`${complianceVal}%`}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* My Medication */}
      <FloatingPanel>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Pill size={20} className="text-primary-600" />
          My Medication Adherence
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">Prescribed Treatment Regimen</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Medication intake compliance for today</p>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              record.medication_taken === "Yes" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" 
              : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
            }`}>
              {record.medication_taken === "Yes" ? "Taken" : "Pending / Missed"}
            </div>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">Daily Exercise Routine</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Doctor-prescribed daily physical activity</p>
            </div>
            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
              record.exercise_completed === "Yes" ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" 
              : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
            }`}>
              {record.exercise_completed === "Yes" ? "Completed" : "Pending"}
            </div>
          </div>
        </div>
      </FloatingPanel>

      {/* Doctor Recommendation */}
      <FloatingPanel>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <FileText size={20} className="text-primary-600" />
          Doctor's Recommendation & Care Plan
        </h2>
        <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-gray-700 dark:text-gray-300">
            "{record.doctor_recommendation || "Continue current medication regimen. Maintain daily hydration goals and log any vital changes."}"
          </p>
        </div>
      </FloatingPanel>

      {/* Digital Twin Behavior Comparison */}
      <FloatingPanel>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-primary-600" />
          Activity vs. Plan
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-center">
            <p className="text-xs font-medium text-gray-500">Steps Taken</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {record.actual_steps} / {record.expected_steps}
            </p>
            <p className="text-xs text-gray-400 mt-1">steps goal</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-center">
            <p className="text-xs font-medium text-gray-500">Sleep Logged</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {record.actual_sleep_hours}h / {record.expected_sleep_hours}h
            </p>
            <p className="text-xs text-gray-400 mt-1">sleep goal</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-center">
            <p className="text-xs font-medium text-gray-500">Water Intake</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {record.water_intake}ml / {record.water_intake_goal}ml
            </p>
            <p className="text-xs text-gray-400 mt-1">hydration goal</p>
          </div>
        </div>
      </FloatingPanel>
    </div>
  );
}
