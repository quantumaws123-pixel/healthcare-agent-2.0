/**
 * /admin/assign — Admin assigns doctors to patients.
 */
import React, { useState, useEffect } from "react";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { UserCheck, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import { getStoredUser, getAccessToken } from "@/lib/auth";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Avatar } from "@/components/ui/Avatar";
import { EmptyState } from "@/components/ui/EmptyState";
import { staggerContainer, staggerItem } from "@/lib/motion";

export const Route = createFileRoute("/_app/admin/assign")({
  beforeLoad: () => {
    const user = getStoredUser();
    if (!user || user.role !== "admin") throw redirect({ to: "/" });
  },
  component: AssignDoctorPage,
});

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface PatientRow { user_id: string; name?: string; email: string; disease_type?: string; age?: number; gender?: string; assigned_doctor_id?: string; }
interface DoctorRow  { id: string; user_id: string; doctor_profile_id: string | null; name?: string; email: string; specialization?: string; }

function AssignDoctorPage() {
  const [patients, setPatients]   = useState<PatientRow[]>([]);
  const [doctors, setDoctors]     = useState<DoctorRow[]>([]);
  const [loading, setLoading]     = useState(true);
  const [actionId, setActionId]   = useState<string | null>(null);
  const [selected, setSelected]   = useState<Record<string, string>>({});
  const [success, setSuccess]     = useState<string | null>(null);
  const [error, setError]         = useState<string | null>(null);

  const token = () => localStorage.getItem("ha_access");

  const load = async () => {
    setLoading(true);
    try {
      const [pRes, dRes] = await Promise.all([
        fetch(`${BASE_URL}/api/hospital/doctor/my-patients`, { headers: { Authorization: `Bearer ${token()}` } }),
        fetch(`${BASE_URL}/api/admin/doctors`, { headers: { Authorization: `Bearer ${token()}` } }),
      ]);

      // For admin, get ALL patients via the auth/me approach — use users list
      const usersRes = await fetch(`${BASE_URL}/api/admin/patients`, { headers: { Authorization: `Bearer ${token()}` } });

      if (usersRes.ok) {
        const pData = await usersRes.json();
        setPatients(pData);
      } else {
        // Fallback: load from my-patients which may be empty for admin
        setPatients([]);
      }

      if (dRes.ok) {
        const dData = await dRes.json();
        // Use doctor_profile_id for assignment — that's what the backend expects
        const mapped: DoctorRow[] = dData
          .filter((d: any) => d.doctor_profile_id) // only approved doctors with profiles
          .map((d: any) => ({
            id:               d.id,                  // user id (for display lookup)
            user_id:          d.id,
            doctor_profile_id: d.doctor_profile_id,  // profile id (sent to /assign-doctor)
            name:             d.name,
            email:            d.email,
            specialization:   d.specialization,
          }));
        setDoctors(mapped);
      }
    } catch (e) {
      setError("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleAssign = async (patientUserId: string) => {
    const doctorProfileId = selected[patientUserId];
    if (!doctorProfileId) return;
    setActionId(patientUserId);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`${BASE_URL}/api/hospital/assign-doctor`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token()}` },
        body: JSON.stringify({ patient_user_id: patientUserId, doctor_profile_id: doctorProfileId }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Assignment failed");
      }
      setSuccess(`Doctor assigned successfully`);
      setTimeout(() => setSuccess(null), 3000);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setActionId(null);
    }
  };

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
      <motion.div variants={staggerItem} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-foreground)]">Assign Doctors to Patients</h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">Match patients to their treating physicians</p>
        </div>
        <Button leftIcon={<RefreshCw size={14} />} variant="secondary" size="sm" loading={loading} onClick={load}>
          Refresh
        </Button>
      </motion.div>

      {success && (
        <motion.div variants={staggerItem}
          className="flex items-center gap-2 p-3 rounded-xl bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 text-sm">
          <CheckCircle size={15} /> {success}
        </motion.div>
      )}
      {error && (
        <motion.div variants={staggerItem}
          className="flex items-center gap-2 p-3 rounded-xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
          <AlertCircle size={15} /> {error}
        </motion.div>
      )}

      <motion.div variants={staggerItem}>
        <Card padding="none">
          {loading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary-500)]" />
            </div>
          ) : patients.length === 0 ? (
            <EmptyState
              title="No patients found"
              description="Patients will appear here once they register and complete onboarding."
              size="md"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[var(--color-border-subtle)] text-xs font-semibold text-[var(--color-muted)] uppercase bg-gray-50/50 dark:bg-gray-900/20">
                    <th className="px-6 py-4">Patient</th>
                    <th className="px-6 py-4">Condition</th>
                    <th className="px-6 py-4">Current Doctor</th>
                    <th className="px-6 py-4">Assign To</th>
                    <th className="px-6 py-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--color-border-subtle)]">
                  {patients.map(p => {
                    // assigned_doctor_id is a DoctorProfileDB.id — match against doctor_profile_id
                    const currentDoc = doctors.find(d => d.doctor_profile_id === p.assigned_doctor_id);
                    return (
                      <tr key={p.user_id} className="hover:bg-[var(--color-border-subtle)]/30 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <Avatar name={p.name ?? p.email} size="sm" />
                            <div>
                              <p className="text-sm font-semibold text-[var(--color-foreground)]">{p.name ?? "—"}</p>
                              <p className="text-xs text-[var(--color-muted)]">{p.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-[var(--color-muted)]">
                          {p.disease_type ?? "—"}{p.age ? ` · ${p.age}y` : ""}{p.gender ? ` · ${p.gender}` : ""}
                        </td>
                        <td className="px-6 py-4 text-sm text-[var(--color-muted)]">
                          {currentDoc ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400">
                              <UserCheck size={11} /> {currentDoc.name ?? currentDoc.email}
                            </span>
                          ) : (
                            <span className="text-xs text-amber-600 dark:text-amber-400">Unassigned</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <select
                            value={selected[p.user_id] ?? ""}
                            onChange={e => setSelected(s => ({ ...s, [p.user_id]: e.target.value }))}
                            className="h-8 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-sm text-[var(--color-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-400)]"
                          >
                            <option value="">Select doctor…</option>
                            {doctors.map(d => (
                              // value = doctor_profile_id — what the backend expects
                              <option key={d.doctor_profile_id ?? d.id} value={d.doctor_profile_id ?? ""}>
                                {d.name ?? d.email}{d.specialization ? ` (${d.specialization})` : ""}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <Button
                            size="xs"
                            variant="primary"
                            leftIcon={<UserCheck size={12} />}
                            loading={actionId === p.user_id}
                            disabled={!selected[p.user_id]}
                            onClick={() => handleAssign(p.user_id)}
                          >
                            Assign
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </motion.div>
    </motion.div>
  );
}
