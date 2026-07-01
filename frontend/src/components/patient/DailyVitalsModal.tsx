/**
 * DailyVitalsModal — Patient submits today's real-world vitals.
 * Updates the Real Digital Twin in the backend.
 */
import React, { useState } from "react";
import { Loader2, AlertCircle, CheckCircle, Heart, Activity, Droplets } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { submitDailyVitals, type DailyVitalsRequest } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  todayAlreadyLogged?: boolean;
}

export function DailyVitalsModal({ open, onClose, onSuccess, todayAlreadyLogged }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form fields
  const [heartRate, setHeartRate]   = useState("");
  const [sysB, setSysB]             = useState("");
  const [diaB, setDiaB]             = useState("");
  const [spo2, setSpo2]             = useState("");
  const [temp, setTemp]             = useState("");
  const [steps, setSteps]           = useState("");
  const [sleep, setSleep]           = useState("");
  const [water, setWater]           = useState("");
  const [medTaken, setMedTaken]     = useState<"Yes"|"No"|"">("");
  const [exercise, setExercise]     = useState<"Yes"|"No"|"">("");
  const [diet, setDiet]             = useState("");
  const [pain, setPain]             = useState("");
  const [mood, setMood]             = useState("");
  const [symptoms, setSymptoms]     = useState("");

  const reset = () => {
    setHeartRate(""); setSysB(""); setDiaB(""); setSpo2(""); setTemp("");
    setSteps(""); setSleep(""); setWater(""); setMedTaken(""); setExercise("");
    setDiet(""); setPain(""); setMood(""); setSymptoms("");
    setError(null); setSuccess(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload: DailyVitalsRequest = {
        heart_rate:          heartRate ? parseInt(heartRate) : undefined,
        systolic_bp:         sysB      ? parseInt(sysB)      : undefined,
        diastolic_bp:        diaB      ? parseInt(diaB)      : undefined,
        spo2:                spo2      ? parseFloat(spo2)    : undefined,
        body_temperature:    temp      ? parseFloat(temp)    : undefined,
        actual_steps:        steps     ? parseInt(steps)     : undefined,
        actual_sleep_hours:  sleep     ? parseFloat(sleep)   : undefined,
        water_intake_ml:     water     ? parseInt(water)     : undefined,
        medication_taken:    medTaken  || undefined,
        exercise_completed:  exercise  || undefined,
        diet_compliance:     diet      ? parseFloat(diet)    : undefined,
        pain_level:          pain      ? parseInt(pain)      : undefined,
        mood:                mood      || undefined,
        symptoms:            symptoms  || undefined,
      };
      await submitDailyVitals(payload);
      setSuccess(true);
      setTimeout(() => { reset(); onSuccess(); onClose(); }, 1500);
    } catch (err: any) {
      setError(err?.message ?? "Failed to save vitals. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const inp = "w-full h-9 px-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400";
  const sel = inp;

  return (
    <Modal open={open} onClose={onClose} title="Log Today's Health Update"
      description="Update your Real Digital Twin with today's measurements." size="lg">
      {success ? (
        <div className="flex flex-col items-center justify-center py-8 gap-3">
          <CheckCircle size={48} className="text-green-500" />
          <p className="text-lg font-semibold text-gray-900 dark:text-white">Vitals Recorded!</p>
          <p className="text-sm text-gray-500">Your Digital Twin has been updated.</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">
          {todayAlreadyLogged && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 text-sm">
              <AlertCircle size={15} className="shrink-0" />
              You already submitted vitals today. Submitting again will update them.
            </div>
          )}

          {/* Vitals */}
          <Section icon={<Heart size={14} />} title="Vital Signs">
            <div className="grid grid-cols-2 gap-3">
              <F label="Heart Rate (bpm)">
                <input type="number" value={heartRate} onChange={e => setHeartRate(e.target.value)}
                  placeholder="e.g. 78" min={30} max={200} className={inp} />
              </F>
              <F label="SpO₂ (%)">
                <input type="number" value={spo2} onChange={e => setSpo2(e.target.value)}
                  placeholder="e.g. 98.5" step="0.1" min={50} max={100} className={inp} />
              </F>
              <F label="Systolic BP">
                <input type="number" value={sysB} onChange={e => setSysB(e.target.value)}
                  placeholder="e.g. 120" className={inp} />
              </F>
              <F label="Diastolic BP">
                <input type="number" value={diaB} onChange={e => setDiaB(e.target.value)}
                  placeholder="e.g. 80" className={inp} />
              </F>
              <F label="Temperature (°C)">
                <input type="number" value={temp} onChange={e => setTemp(e.target.value)}
                  placeholder="e.g. 36.6" step="0.1" className={inp} />
              </F>
            </div>
          </Section>

          {/* Activity */}
          <Section icon={<Activity size={14} />} title="Activity & Adherence">
            <div className="grid grid-cols-2 gap-3">
              <F label="Steps Taken">
                <input type="number" value={steps} onChange={e => setSteps(e.target.value)}
                  placeholder="e.g. 7500" className={inp} />
              </F>
              <F label="Sleep (hours)">
                <input type="number" value={sleep} onChange={e => setSleep(e.target.value)}
                  placeholder="e.g. 7.5" step="0.5" className={inp} />
              </F>
              <F label="Medication Taken">
                <select value={medTaken} onChange={e => setMedTaken(e.target.value as any)} className={sel}>
                  <option value="">Select…</option>
                  <option value="Yes">Yes ✓</option>
                  <option value="No">No ✗</option>
                </select>
              </F>
              <F label="Exercise Completed">
                <select value={exercise} onChange={e => setExercise(e.target.value as any)} className={sel}>
                  <option value="">Select…</option>
                  <option value="Yes">Yes ✓</option>
                  <option value="No">No ✗</option>
                </select>
              </F>
            </div>
          </Section>

          {/* Wellbeing */}
          <Section icon={<Droplets size={14} />} title="Wellbeing">
            <div className="grid grid-cols-2 gap-3">
              <F label="Water Intake (ml)">
                <input type="number" value={water} onChange={e => setWater(e.target.value)}
                  placeholder="e.g. 1800" className={inp} />
              </F>
              <F label="Diet Compliance (%)">
                <input type="number" value={diet} onChange={e => setDiet(e.target.value)}
                  placeholder="e.g. 85" min={0} max={100} className={inp} />
              </F>
              <F label="Pain Level (0-10)">
                <input type="number" value={pain} onChange={e => setPain(e.target.value)}
                  placeholder="0 = none" min={0} max={10} className={inp} />
              </F>
              <F label="Mood">
                <select value={mood} onChange={e => setMood(e.target.value)} className={sel}>
                  <option value="">Select…</option>
                  {["Great","Good","Neutral","Tired","Anxious","Unwell"].map(m=><option key={m}>{m}</option>)}
                </select>
              </F>
            </div>
            <F label="Symptoms or Notes (optional)">
              <input type="text" value={symptoms} onChange={e => setSymptoms(e.target.value)}
                placeholder="e.g. Mild shortness of breath, slight fatigue" className={inp} />
            </F>
          </Section>

          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
              <AlertCircle size={15} className="shrink-0" /> {error}
            </div>
          )}

          <div className="flex gap-3 justify-end pt-2">
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" variant="primary" loading={loading}>Save Today's Vitals</Button>
          </div>
        </form>
      )}
    </Modal>
  );
}

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-primary-500">{icon}</span>
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</p>
      </div>
      {children}
    </div>
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
