/**
 * OnboardingWizard — shown to patients on first login.
 * Collects real demographics so personalised monitoring data can be generated.
 */
import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, ChevronRight, ChevronLeft, CheckCircle, Loader2, AlertCircle } from "lucide-react";
import { completeOnboarding, type PatientOnboardingRequest } from "@/lib/api";
import { cn } from "@/lib/utils";

interface Props {
  onComplete: () => void;
}

const DISEASE_TYPES = [
  "Cardiac", "Diabetes", "Hypertension", "COPD",
  "Kidney Disease", "Asthma", "Stroke Recovery", "Post Surgery",
];

const STEPS = ["Personal Info", "Clinical Details", "Lifestyle & Emergency"];

export function OnboardingWizard({ onComplete }: Props) {
  const [step, setStep]       = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  // Form state
  const [age, setAge]           = useState("");
  const [gender, setGender]     = useState("Male");
  const [heightCm, setHeightCm] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [bloodGroup, setBloodGroup] = useState("");
  const [diseaseType, setDisease] = useState(DISEASE_TYPES[0]);
  const [dischargeDate, setDischarge] = useState("");
  const [existingConditions, setConditions] = useState("");
  const [allergies, setAllergies] = useState("");
  const [currentMedication, setMedication] = useState("");
  const [smokingStatus, setSmoking]       = useState("Never");
  const [alcoholConsumption, setAlcohol]  = useState("None");
  const [emergencyName, setEmergencyName] = useState("");
  const [emergencyPhone, setEmergencyPhone] = useState("");

  const next = () => setStep(s => s + 1);
  const back = () => setStep(s => s - 1);

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: PatientOnboardingRequest = {
        age: parseInt(age),
        gender,
        height_cm: heightCm ? parseInt(heightCm) : undefined,
        weight_kg: weightKg ? parseFloat(weightKg) : undefined,
        blood_group: bloodGroup || undefined,
        disease_type: diseaseType,
        smoking_status: smokingStatus,
        alcohol_consumption: alcoholConsumption,
        allergies: allergies || undefined,
        existing_conditions: existingConditions || undefined,
        current_medication: currentMedication || undefined,
        emergency_contact_name: emergencyName || undefined,
        emergency_contact_phone: emergencyPhone || undefined,
        discharge_date: dischargeDate || undefined,
      };
      await completeOnboarding(payload);
      onComplete();
    } catch (err: any) {
      setError(err?.message ?? "Failed to save your profile. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-blue-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg"
      >
        {/* Header */}
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className="w-11 h-11 rounded-2xl bg-primary-500 flex items-center justify-center shadow-lg">
            <Heart size={22} className="text-white" strokeWidth={2.5} />
          </div>
          <div>
            <p className="text-lg font-bold text-gray-900 dark:text-white">Healthcare Agent 2.0</p>
            <p className="text-xs text-gray-500">Patient Setup</p>
          </div>
        </div>

        {/* Progress */}
        <div className="flex items-center justify-between mb-6">
          {STEPS.map((s, i) => (
            <React.Fragment key={s}>
              <div className="flex flex-col items-center gap-1">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all",
                  i < step  ? "bg-primary-500 text-white" :
                  i === step ? "bg-primary-500 text-white ring-4 ring-primary-100" :
                               "bg-gray-200 dark:bg-gray-700 text-gray-500"
                )}>
                  {i < step ? <CheckCircle size={16} /> : i + 1}
                </div>
                <span className="text-[10px] text-gray-500 hidden sm:block">{s}</span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={cn("flex-1 h-0.5 mx-2 transition-all",
                  i < step ? "bg-primary-500" : "bg-gray-200 dark:bg-gray-700"
                )} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-gray-900 rounded-3xl shadow-xl border border-gray-100 dark:border-gray-800 overflow-hidden">
          <div className="p-7">
            <AnimatePresence mode="wait">
              {step === 0 && (
                <Step0 key="s0" age={age} setAge={setAge} gender={gender} setGender={setGender}
                  heightCm={heightCm} setHeightCm={setHeightCm} weightKg={weightKg} setWeightKg={setWeightKg}
                  bloodGroup={bloodGroup} setBloodGroup={setBloodGroup} />
              )}
              {step === 1 && (
                <Step1 key="s1" diseaseType={diseaseType} setDisease={setDisease}
                  dischargeDate={dischargeDate} setDischarge={setDischarge}
                  existingConditions={existingConditions} setConditions={setConditions}
                  allergies={allergies} setAllergies={setAllergies}
                  currentMedication={currentMedication} setMedication={setMedication} />
              )}
              {step === 2 && (
                <Step2 key="s2" smokingStatus={smokingStatus} setSmoking={setSmoking}
                  alcoholConsumption={alcoholConsumption} setAlcohol={setAlcohol}
                  emergencyName={emergencyName} setEmergencyName={setEmergencyName}
                  emergencyPhone={emergencyPhone} setEmergencyPhone={setEmergencyPhone} />
              )}
            </AnimatePresence>

            {error && (
              <div className="flex items-center gap-2 p-3 mt-4 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
                <AlertCircle size={15} className="shrink-0" />
                {error}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-100 dark:border-gray-800">
              <button
                onClick={back} disabled={step === 0}
                className="flex items-center gap-1 text-sm font-medium text-gray-500 hover:text-gray-900 disabled:opacity-30 disabled:pointer-events-none transition-colors"
              >
                <ChevronLeft size={16} /> Back
              </button>
              {step < STEPS.length - 1 ? (
                <button
                  onClick={next}
                  disabled={step === 0 && (!age || !gender)}
                  className="flex items-center gap-1.5 h-10 px-5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white text-sm font-semibold transition-colors disabled:opacity-40 disabled:pointer-events-none"
                >
                  Next <ChevronRight size={16} />
                </button>
              ) : (
                <button
                  onClick={handleSubmit} disabled={loading}
                  className="flex items-center gap-1.5 h-10 px-5 rounded-xl bg-primary-500 hover:bg-primary-600 text-white text-sm font-semibold transition-colors disabled:opacity-40"
                >
                  {loading ? <Loader2 size={15} className="animate-spin" /> : <CheckCircle size={15} />}
                  {loading ? "Saving…" : "Complete Setup"}
                </button>
              )}
            </div>
          </div>
        </div>
        <p className="text-center text-xs text-gray-400 mt-4">
          Your data is securely stored and used only for your health monitoring.
        </p>
      </motion.div>
    </div>
  );
}

// ── Step sub-components ───────────────────────────────────────────────────

function StepWrap({ title, desc, children }: { title: string; desc: string; children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2 }}
    >
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">{title}</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-5">{desc}</p>
      <div className="space-y-4">{children}</div>
    </motion.div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">{label}</label>
      {children}
    </div>
  );
}

const inputCls = "w-full h-10 px-3.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400";
const selectCls = inputCls;

function Step0({ age, setAge, gender, setGender, heightCm, setHeightCm, weightKg, setWeightKg, bloodGroup, setBloodGroup }: any) {
  return (
    <StepWrap title="Tell us about yourself" desc="We'll use this to personalise your monitoring data.">
      <div className="grid grid-cols-2 gap-4">
        <Field label="Age *">
          <input type="number" value={age} onChange={e => setAge(e.target.value)}
            placeholder="e.g. 45" min={1} max={120} className={inputCls} required />
        </Field>
        <Field label="Gender *">
          <select value={gender} onChange={e => setGender(e.target.value)} className={selectCls}>
            <option>Male</option><option>Female</option><option>Other</option>
          </select>
        </Field>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Height (cm)">
          <input type="number" value={heightCm} onChange={e => setHeightCm(e.target.value)}
            placeholder="e.g. 170" className={inputCls} />
        </Field>
        <Field label="Weight (kg)">
          <input type="number" value={weightKg} onChange={e => setWeightKg(e.target.value)}
            placeholder="e.g. 72.5" step="0.1" className={inputCls} />
        </Field>
      </div>
      <Field label="Blood Group">
        <select value={bloodGroup} onChange={e => setBloodGroup(e.target.value)} className={selectCls}>
          <option value="">Select…</option>
          {["A+","A-","B+","B-","AB+","AB-","O+","O-"].map(g => <option key={g}>{g}</option>)}
        </select>
      </Field>
    </StepWrap>
  );
}

function Step1({ diseaseType, setDisease, dischargeDate, setDischarge, existingConditions, setConditions, allergies, setAllergies, currentMedication, setMedication }: any) {
  return (
    <StepWrap title="Clinical Information" desc="Tell us about your condition and treatment.">
      <Field label="Primary Condition *">
        <select value={diseaseType} onChange={e => setDisease(e.target.value)} className={selectCls}>
          {["Cardiac","Diabetes","Hypertension","COPD","Kidney Disease","Asthma","Stroke Recovery","Post Surgery"].map(d => (
            <option key={d}>{d}</option>
          ))}
        </select>
      </Field>
      <Field label="Discharge Date">
        <input type="date" value={dischargeDate} onChange={e => setDischarge(e.target.value)} className={inputCls} />
      </Field>
      <Field label="Existing Medical Conditions">
        <input type="text" value={existingConditions} onChange={e => setConditions(e.target.value)}
          placeholder="e.g. Type 2 Diabetes, Hypertension" className={inputCls} />
      </Field>
      <Field label="Known Allergies">
        <input type="text" value={allergies} onChange={e => setAllergies(e.target.value)}
          placeholder="e.g. Penicillin, Aspirin" className={inputCls} />
      </Field>
      <Field label="Current Medications">
        <input type="text" value={currentMedication} onChange={e => setMedication(e.target.value)}
          placeholder="e.g. Metformin 500mg, Atorvastatin 10mg" className={inputCls} />
      </Field>
    </StepWrap>
  );
}

function Step2({ smokingStatus, setSmoking, alcoholConsumption, setAlcohol, emergencyName, setEmergencyName, emergencyPhone, setEmergencyPhone }: any) {
  return (
    <StepWrap title="Lifestyle & Emergency Contact" desc="Almost done — just a few more details.">
      <div className="grid grid-cols-2 gap-4">
        <Field label="Smoking Status">
          <select value={smokingStatus} onChange={e => setSmoking(e.target.value)} className={selectCls}>
            <option>Never</option><option>Former</option><option>Current</option>
          </select>
        </Field>
        <Field label="Alcohol Consumption">
          <select value={alcoholConsumption} onChange={e => setAlcohol(e.target.value)} className={selectCls}>
            <option>None</option><option>Occasional</option><option>Moderate</option><option>Heavy</option>
          </select>
        </Field>
      </div>
      <div className="border-t border-gray-100 dark:border-gray-800 pt-4 mt-2">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Emergency Contact</p>
        <div className="space-y-3">
          <Field label="Full Name">
            <input type="text" value={emergencyName} onChange={e => setEmergencyName(e.target.value)}
              placeholder="e.g. Jane Doe" className={inputCls} />
          </Field>
          <Field label="Phone Number">
            <input type="tel" value={emergencyPhone} onChange={e => setEmergencyPhone(e.target.value)}
              placeholder="e.g. +91 98765 43210" className={inputCls} />
          </Field>
        </div>
      </div>
    </StepWrap>
  );
}
