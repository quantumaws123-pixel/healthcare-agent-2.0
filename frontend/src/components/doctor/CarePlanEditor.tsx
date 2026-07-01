/**
 * CarePlanEditor — Doctor creates or updates a patient's care plan.
 * The care plan becomes the patient's Ideal Digital Twin targets.
 */
import React, { useState, useEffect } from "react";
import { Loader2, AlertCircle, CheckCircle, ClipboardList } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { createCarePlan, getCarePlan, type CarePlan } from "@/lib/api";

interface Props {
  open: boolean;
  onClose: () => void;
  patientUserId: string;
  patientName?: string;
  onSuccess?: () => void;
}

export function CarePlanEditor({ open, onClose, patientUserId, patientName, onSuccess }: Props) {
  const [loading, setLoading]     = useState(false);
  const [fetchLoading, setFetch]  = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [success, setSuccess]     = useState(false);

  const [stepsGoal, setSteps]   = useState("8000");
  const [sleepGoal, setSleep]   = useState("8.0");
  const [waterGoal, setWater]   = useState("2000");
  const [medSchedule, setMed]   = useState("");
  const [exercisePlan, setEx]   = useState("");
  const [dietPlan, setDiet]     = useState("");
  const [followup, setFollowup] = useState("7");
  const [duration, setDuration] = useState("30");
  const [riskThr, setRisk]      = useState("0.50");
  const [emergThr, setEmerg]    = useState("0.75");
  const [notes, setNotes]       = useState("");

  // Load existing care plan
  useEffect(() => {
    if (!open || !patientUserId) return;
    setFetch(true);
    getCarePlan(patientUserId)
      .then(plan => {
        if (plan) {
          setSteps(String(plan.daily_steps_goal ?? 8000));
          setSleep(String(plan.sleep_hours_goal ?? 8.0));
          setWater(String(plan.water_intake_goal_ml ?? 2000));
          setMed(plan.medication_schedule ?? "");
          setEx(plan.exercise_plan ?? "");
          setDiet(plan.diet_plan ?? "");
          setFollowup(String(plan.followup_frequency_days ?? 7));
          setDuration(String(plan.monitoring_duration_days ?? 30));
          setRisk(String(plan.risk_threshold ?? 0.5));
          setEmerg(String(plan.emergency_threshold ?? 0.75));
          setNotes(plan.notes ?? "");
        }
      })
      .catch(() => {})
      .finally(() => setFetch(false));
  }, [open, patientUserId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await createCarePlan({
        patient_user_id:         patientUserId,
        daily_steps_goal:        parseInt(stepsGoal),
        sleep_hours_goal:        parseFloat(sleepGoal),
        water_intake_goal_ml:    parseInt(waterGoal),
        medication_schedule:     medSchedule || undefined,
        exercise_plan:           exercisePlan || undefined,
        diet_plan:               dietPlan || undefined,
        followup_frequency_days: parseInt(followup),
        monitoring_duration_days:parseInt(duration),
        risk_threshold:          parseFloat(riskThr),
        emergency_threshold:     parseFloat(emergThr),
        notes:                   notes || undefined,
      });
      setSuccess(true);
      setTimeout(() => { setSuccess(false); onSuccess?.(); onClose(); }, 1500);
    } catch (err: any) {
      setError(err?.message ?? "Failed to save care plan.");
    } finally {
      setLoading(false);
    }
  };

  const inp = "w-full h-9 px-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400";
  const ta  = "w-full px-3 py-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400 resize-none";

  return (
    <Modal open={open} onClose={onClose} size="xl"
      title={`Care Plan — ${patientName ?? patientUserId}`}
      description="Sets the Ideal Digital Twin targets for this patient.">
      {success ? (
        <div className="flex flex-col items-center justify-center py-8 gap-3">
          <CheckCircle size={48} className="text-green-500" />
          <p className="text-lg font-semibold text-gray-900 dark:text-white">Care Plan Saved!</p>
          <p className="text-sm text-gray-500">The patient's Ideal Twin has been updated.</p>
        </div>
      ) : fetchLoading ? (
        <div className="flex justify-center py-8"><Loader2 className="animate-spin text-primary-500" size={28} /></div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Daily Targets */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3 flex items-center gap-1.5">
              <ClipboardList size={13} /> Daily Targets (Ideal Twin)
            </p>
            <div className="grid grid-cols-3 gap-3">
              <F label="Steps Goal / day">
                <input type="number" value={stepsGoal} onChange={e => setSteps(e.target.value)} className={inp} placeholder="8000" />
              </F>
              <F label="Sleep (hours)">
                <input type="number" value={sleepGoal} onChange={e => setSleep(e.target.value)} className={inp} step="0.5" placeholder="8.0" />
              </F>
              <F label="Water Goal (ml)">
                <input type="number" value={waterGoal} onChange={e => setWater(e.target.value)} className={inp} placeholder="2000" />
              </F>
            </div>
          </div>

          {/* Plans */}
          <div className="grid grid-cols-1 gap-3">
            <F label="Medication Schedule">
              <textarea value={medSchedule} onChange={e => setMed(e.target.value)} rows={2}
                placeholder="e.g. Metformin 500mg morning, Atorvastatin 10mg night" className={ta} />
            </F>
            <F label="Exercise Plan">
              <textarea value={exercisePlan} onChange={e => setEx(e.target.value)} rows={2}
                placeholder="e.g. 30 min brisk walk daily, light yoga 3x per week" className={ta} />
            </F>
            <F label="Diet Plan">
              <textarea value={dietPlan} onChange={e => setDiet(e.target.value)} rows={2}
                placeholder="e.g. Low sodium diet, avoid processed foods, 5 servings of vegetables" className={ta} />
            </F>
          </div>

          {/* Monitoring Settings */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3">Monitoring Settings</p>
            <div className="grid grid-cols-2 gap-3">
              <F label="Follow-up every (days)">
                <input type="number" value={followup} onChange={e => setFollowup(e.target.value)} className={inp} />
              </F>
              <F label="Monitoring duration (days)">
                <input type="number" value={duration} onChange={e => setDuration(e.target.value)} className={inp} />
              </F>
              <F label="Risk Alert Threshold (0–1)">
                <input type="number" value={riskThr} onChange={e => setRisk(e.target.value)} className={inp} step="0.05" min="0" max="1" />
              </F>
              <F label="Emergency Threshold (0–1)">
                <input type="number" value={emergThr} onChange={e => setEmerg(e.target.value)} className={inp} step="0.05" min="0" max="1" />
              </F>
            </div>
          </div>

          <F label="Doctor's Notes">
            <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2}
              placeholder="Additional instructions or observations for this patient" className={ta} />
          </F>

          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
              <AlertCircle size={15} className="shrink-0" /> {error}
            </div>
          )}

          <div className="flex gap-3 justify-end pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" variant="primary" loading={loading}>Save Care Plan</Button>
          </div>
        </form>
      )}
    </Modal>
  );
}

function F({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      {children}
    </div>
  );
}
