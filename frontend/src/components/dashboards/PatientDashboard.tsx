import React, { useState } from "react";
import { Heart, Activity, TrendingUp, Pill, FileText, Loader2, Plus, UserCheck, Sliders, Zap, CheckCircle, Info, Award, HelpCircle, Bot } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { FloatingPanel } from "@/components/ui/FloatingPanel";
import { StatCard } from "@/components/ui/StatCard";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { useAuthContext } from "@/context/AuthContext";
import { usePatientLatest } from "@/hooks/usePatients";
import { DailyVitalsModal } from "@/components/patient/DailyVitalsModal";
import {
  getMyPatientProfile, getTodayVitals, getCarePlan, getAssignedDoctor,
  hospitalQueryKeys, simulateRecovery, type SimulationResponse
} from "@/lib/api";

export function PatientDashboard() {
  const { user } = useAuthContext();
  const queryClient = useQueryClient();
  const [vitalsOpen, setVitalsOpen] = useState(false);

  const { data: record, isLoading } = usePatientLatest(user?.id ?? "");

  // Simulator state
  const [simulating, setSimulating] = useState(false);
  const [simInputs, setSimInputs] = useState({
    actual_steps: 8000,
    actual_sleep_hours: 8,
    water_intake: 2000,
    medication_taken: "Yes" as "Yes" | "No",
    weight_kg: 70,
  });
  const [simResult, setSimResult] = useState<SimulationResponse | null>(null);

  const { data: profile } = useQuery({
    queryKey: hospitalQueryKeys.myProfile(),
    queryFn: getMyPatientProfile,
    enabled: Boolean(user?.id),
  });

  const { data: todayVitals } = useQuery({
    queryKey: hospitalQueryKeys.todayVitals(),
    queryFn: getTodayVitals,
    enabled: Boolean(user?.id),
  });

  const { data: carePlan } = useQuery({
    queryKey: hospitalQueryKeys.carePlan(user?.id ?? ""),
    queryFn: () => getCarePlan(user?.id ?? ""),
    enabled: Boolean(user?.id),
  });

  const { data: assignedDoctorData } = useQuery({
    queryKey: hospitalQueryKeys.assignedDoctor(user?.id ?? ""),
    queryFn: () => getAssignedDoctor(user?.id ?? ""),
    enabled: Boolean(user?.id),
  });

  const assignedDoctor = assignedDoctorData?.assigned_doctor;

  React.useEffect(() => {
    if (record) {
      setSimInputs({
        actual_steps: record.actual_steps ?? 8000,
        actual_sleep_hours: record.actual_sleep_hours ?? 8,
        water_intake: record.water_intake ?? 2000,
        medication_taken: (record.medication_taken as "Yes" | "No") ?? "Yes",
        weight_kg: record.weight_kg ?? 70,
      });
      setSimResult(null);
    }
  }, [record]);

  const handleSimulate = async () => {
    if (!user?.id) return;
    setSimulating(true);
    try {
      const res = await simulateRecovery(user.id, simInputs);
      setSimResult(res);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setSimulating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-primary-500" size={32} />
      </div>
    );
  }

  if (!record) {
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
  const recoveryVal = Math.round(record.recovery_score ?? 50);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">My Health Dashboard</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Monitor your recovery progress in real-time</p>
        </div>
        <Button
          leftIcon={<Plus size={15} />}
          variant="primary"
          onClick={() => setVitalsOpen(true)}
        >
          {todayVitals ? "Update Today's Vitals" : "Log Today's Vitals"}
        </Button>
      </div>

      {/* Daily vitals logged indicator */}
      {todayVitals && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-sm">
          <Activity size={15} className="shrink-0" />
          Today's vitals recorded · Heart rate: {todayVitals.heart_rate ?? "—"} bpm ·
          Steps: {todayVitals.actual_steps?.toLocaleString() ?? "—"} ·
          Medication: {todayVitals.medication_taken ?? "—"}
        </div>
      )}

      {/* Assigned Doctor */}
      {assignedDoctor && (
        <FloatingPanel>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
              <UserCheck size={18} className="text-primary-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">
                Your Doctor: {assignedDoctor.name ?? "Assigned Physician"}
              </p>
              <p className="text-xs text-gray-500">
                {assignedDoctor.specialization ?? ""}{assignedDoctor.department ? ` · ${assignedDoctor.department}` : ""}
                {assignedDoctor.phone ? ` · ${assignedDoctor.phone}` : ""}
              </p>
            </div>
          </div>
        </FloatingPanel>
      )}

      {/* AI Assistant CTA */}
      <Link to="/assistant">
        <div className="flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-r from-primary-500 to-blue-600 hover:from-primary-600 hover:to-blue-700 transition-all cursor-pointer shadow-md group">
          <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
            <Bot size={20} className="text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-white">Ask Your Health Assistant</p>
            <p className="text-xs text-white/80 mt-0.5">
              "Why is my risk high?" · "Did I sleep enough?" · "What should I improve today?"
            </p>
          </div>
          <div className="text-white/60 group-hover:text-white transition-colors text-xs font-medium">
            Ask →
          </div>
        </div>
      </Link>

      {/* Health Overview Section: Twin Indexes */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recovery Score Index */}
        <FloatingPanel className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/10 dark:to-emerald-900/10 border-green-200 dark:border-green-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-green-600 dark:text-green-400 uppercase tracking-wider">Recovery Index</p>
              <p className="text-5xl font-extrabold text-green-900 dark:text-green-100 mt-2">{recoveryVal}</p>
              <p className="text-xs text-green-700 dark:text-green-300 mt-2 font-medium">
                Trend: {record.health_trend ?? "Stable"} · Status: {record.recovery_status ?? "Stable"}
              </p>
            </div>
            <div className="w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/40 flex items-center justify-center">
              <Award size={36} className="text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div className="mt-4 border-t border-green-200/50 pt-2">
            <ProgressBar value={recoveryVal} showValue color="var(--color-success-500)" />
          </div>
        </FloatingPanel>

        {/* Readmission Risk Index */}
        <FloatingPanel className="bg-gradient-to-br from-primary-50 to-blue-50 dark:from-primary-900/10 dark:to-blue-900/10 border-primary-200 dark:border-primary-800">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-primary-600 dark:text-primary-400 uppercase tracking-wider">Readmission Risk Index</p>
              <p className="text-5xl font-extrabold text-primary-900 dark:text-primary-100 mt-2">{riskPercent}%</p>
              <p className="text-xs text-primary-700 dark:text-primary-300 mt-2 font-medium">
                Classification: {record.risk_level ?? "Low"} Risk
              </p>
            </div>
            <div className="w-20 h-20 rounded-full bg-primary-100 dark:bg-primary-900/40 flex items-center justify-center">
              <Heart size={36} className="text-primary-600 dark:text-primary-400" />
            </div>
          </div>
          <div className="mt-4 border-t border-primary-200/50 pt-2">
            <ProgressBar value={riskPercent} showValue color="var(--color-primary-500)" />
          </div>
        </FloatingPanel>
      </div>

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
          label="Compliance Score"
          value={`${complianceVal}%`}
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Explainable AI Risk Drivers (Why is risk X%) */}
      <FloatingPanel>
        <h2 className="text-base font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
          <Info size={18} className="text-[var(--color-primary-500)]" />
          Explainable AI Risk Drivers
        </h2>
        <div className="flex flex-wrap gap-2">
          {record.shap_reasons && record.shap_reasons.length > 0 ? (
            record.shap_reasons.map((reason, idx) => (
              <Badge key={idx} variant="danger" className="px-2.5 py-1 text-xs">
                {reason}
              </Badge>
            ))
          ) : (
            <span className="text-xs text-gray-500">All risk categories are within optimal ranges.</span>
          )}
        </div>
      </FloatingPanel>

      {/* Personalized AI Recommendations & Improvement Tips */}
      <FloatingPanel>
        <h2 className="text-base font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
          <Zap size={18} className="text-amber-500" />
          Today's Personalized AI Recommendations & Tips
        </h2>
        <div className="space-y-2">
          {record.ai_recommendations && record.ai_recommendations.length > 0 ? (
            record.ai_recommendations.map((rec, i) => (
              <div key={i} className="flex gap-2.5 items-start p-3 rounded-xl bg-amber-500/5 border border-amber-500/10 text-amber-900 dark:text-amber-300">
                <CheckCircle size={16} className="shrink-0 mt-0.5 text-amber-500" />
                <span className="text-xs leading-relaxed font-medium">{rec}</span>
              </div>
            ))
          ) : (
            <div className="p-3 rounded-xl bg-green-500/5 border border-green-500/10 text-green-900 dark:text-green-300 text-xs font-medium">
              ✓ Excellent adherence! Keep up the good work on your daily targets.
            </div>
          )}
        </div>
      </FloatingPanel>

      {/* Mini Recovery Simulator */}
      <FloatingPanel className="border-2 border-primary-500/20 bg-gradient-to-br from-white to-primary-50/5 dark:from-gray-900 dark:to-primary-950/10">
        <h2 className="text-base font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
          <Sliders size={18} className="text-primary-500" />
          Mini Recovery Simulator ("What-If")
        </h2>
        <p className="text-xs text-gray-500 mb-4">
          Test how completing your daily goals changes your recovery index and lowers your readmission risk:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-gray-700 dark:text-gray-300">Take Medication?</label>
              <select
                value={simInputs.medication_taken}
                onChange={e => setSimInputs(prev => ({ ...prev, medication_taken: e.target.value as "Yes" | "No" }))}
                className="text-xs p-1 rounded bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
              </select>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <label className="font-semibold text-gray-700 dark:text-gray-300">Steps</label>
                <span className="text-gray-500">{simInputs.actual_steps.toLocaleString()}</span>
              </div>
              <input
                type="range"
                min={0}
                max={20000}
                step={500}
                value={simInputs.actual_steps}
                onChange={e => setSimInputs(prev => ({ ...prev, actual_steps: parseInt(e.target.value) }))}
                className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <label className="font-semibold text-gray-700 dark:text-gray-300">Sleep Duration</label>
                <span className="text-gray-500">{simInputs.actual_sleep_hours.toFixed(1)} h</span>
              </div>
              <input
                type="range"
                min={0}
                max={24}
                step={0.5}
                value={simInputs.actual_sleep_hours}
                onChange={e => setSimInputs(prev => ({ ...prev, actual_sleep_hours: parseFloat(e.target.value) }))}
                className="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
              />
            </div>
            <Button onClick={handleSimulate} disabled={simulating} size="sm" variant="primary" className="w-full mt-2">
              {simulating ? "Calculating Forecast..." : "Simulate Recovery Outlines"}
            </Button>
          </div>

          <div className="p-3.5 bg-gray-50 dark:bg-gray-800/40 rounded-xl border border-gray-100 dark:border-gray-800 flex flex-col justify-center text-xs">
            {simResult ? (
              <div className="space-y-3">
                <div className="flex justify-between border-b border-gray-200/50 pb-1.5">
                  <span className="text-gray-500">Recovery score forecast:</span>
                  <span className="font-bold text-green-500">
                    {Math.round(simResult.original_recovery_score)} → {Math.round(simResult.simulated_recovery_score)}
                  </span>
                </div>
                <div className="flex justify-between border-b border-gray-200/50 pb-1.5">
                  <span className="text-gray-500">Risk classification forecast:</span>
                  <span className="font-bold text-primary-500">
                    {simResult.original_risk_level} → {simResult.simulated_risk_level}
                  </span>
                </div>
                <div className="flex justify-between pb-1.5">
                  <span className="text-gray-500">Probability of readmission:</span>
                  <span className="font-bold text-primary-600">
                    {Math.round(simResult.original_readmission_probability * 100)}% → {Math.round(simResult.simulated_readmission_probability * 100)}%
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-gray-400 dark:text-gray-600">
                <HelpCircle size={28} className="mx-auto opacity-30 mb-1.5" />
                Adjust values and simulate to view recovery forecast.
              </div>
            )}
          </div>
        </div>
      </FloatingPanel>

      {/* Digital Twin Behavior Comparison */}
      <FloatingPanel>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <TrendingUp size={20} className="text-primary-600" />
          Today's Goal Tracker {carePlan && <span className="text-xs font-normal text-gray-400">(from Care Plan)</span>}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-center">
            <p className="text-xs font-medium text-gray-500">Steps Progress</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {(todayVitals?.actual_steps ?? record.actual_steps)?.toLocaleString()} / {(carePlan?.daily_steps_goal ?? record.expected_steps)?.toLocaleString()}
            </p>
            <p className="text-xs text-gray-400 mt-1">steps achieved</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-center">
            <p className="text-xs font-medium text-gray-500">Sleep Sleep</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {todayVitals?.actual_sleep_hours ?? record.actual_sleep_hours}h / {carePlan?.sleep_hours_goal ?? record.expected_sleep_hours}h
            </p>
            <p className="text-xs text-gray-400 mt-1">hours rest</p>
          </div>
          <div className="p-4 rounded-xl bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-center">
            <p className="text-xs font-medium text-gray-500">Water Hydration</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {(todayVitals?.water_intake_ml ?? record.water_intake)}ml / {(carePlan?.water_intake_goal_ml ?? record.water_intake_goal)}ml
            </p>
            <p className="text-xs text-gray-400 mt-1">fluid targets</p>
          </div>
        </div>
      </FloatingPanel>

      {/* Medication Adherence */}
      <FloatingPanel>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Pill size={20} className="text-primary-600" />
          My Daily Treatment Compliance
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

      {/* Care Plan from Doctor */}
      {carePlan && (
        <FloatingPanel>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <FileText size={20} className="text-primary-600" />
            My Care Plan
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {carePlan.medication_schedule && (
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800">
                <p className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-1">💊 Medication Schedule</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">{carePlan.medication_schedule}</p>
              </div>
            )}
            {carePlan.exercise_plan && (
              <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800">
                <p className="text-xs font-semibold text-green-700 dark:text-green-400 mb-1">🏃 Exercise Plan</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">{carePlan.exercise_plan}</p>
              </div>
            )}
            {carePlan.diet_plan && (
              <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800">
                <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 mb-1">🥗 Diet Plan</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">{carePlan.diet_plan}</p>
              </div>
            )}
            {carePlan.notes && (
              <div className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700">
                <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1">📋 Doctor's Notes</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">{carePlan.notes}</p>
              </div>
            )}
          </div>
          <p className="text-xs text-gray-400 mt-3">
            Follow-up every {carePlan.followup_frequency_days} days · Monitoring: {carePlan.monitoring_duration_days} days
          </p>
        </FloatingPanel>
      )}

      {/* Vitals modal */}
      <DailyVitalsModal
        open={vitalsOpen}
        onClose={() => setVitalsOpen(false)}
        todayAlreadyLogged={!!todayVitals}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: hospitalQueryKeys.todayVitals() });
          queryClient.invalidateQueries({ queryKey: ["patient-latest", user?.id ?? ""] });
        }}
      />
    </div>
  );
}
