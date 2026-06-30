import React, { useState, useEffect } from "react";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { UserCheck, XCircle, AlertTriangle, Check, X, RefreshCw, UserMinus, ShieldAlert } from "lucide-react";
import { getStoredUser } from "@/lib/auth";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Avatar } from "@/components/ui/Avatar";
import { EmptyState } from "@/components/ui/EmptyState";
import { staggerContainer, staggerItem } from "@/lib/motion";

export const Route = createFileRoute("/_app/admin/doctors")({
  beforeLoad: () => {
    const user = getStoredUser();
    if (!user || user.role !== "admin") {
      throw redirect({ to: "/" });
    }
  },
  component: AdminDoctorsPage,
});

interface DoctorUser {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  role: string;
  status: "pending" | "approved" | "rejected" | "inactive";
  is_active: boolean;
  created_at: string;
}

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function AdminDoctorsPage() {
  const [doctors, setDoctors] = useState<DoctorUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchDoctors = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("ha_access");
      const res = await fetch(`${BASE_URL}/api/admin/doctors`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) throw new Error("Failed to fetch doctors list");
      const data = await res.json();
      setDoctors(data);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDoctors();
  }, []);

  const handleAction = async (id: string, action: "approve" | "reject" | "deactivate" | "activate") => {
    setActionLoading(id);
    try {
      const token = localStorage.getItem("ha_access");
      const res = await fetch(`${BASE_URL}/api/admin/doctors/${id}/${action}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed to ${action} doctor`);
      }
      // Refresh list
      await fetchDoctors();
    } catch (err: any) {
      alert(err.message || "Action failed");
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusBadge = (status: DoctorUser["status"]) => {
    switch (status) {
      case "approved":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-success-50 text-success-700 dark:bg-green-900/20 dark:text-green-300">Active</span>;
      case "pending":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-warning-50 text-warning-700 dark:bg-amber-900/20 dark:text-amber-300">Pending Approval</span>;
      case "rejected":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-danger-50 text-danger-700 dark:bg-red-900/20 dark:text-red-300">Rejected</span>;
      case "inactive":
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400">Deactivated</span>;
      default:
        return null;
    }
  };

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">Doctor Approval</h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">Manage registrations and account status for medical staff</p>
        </div>
        <Button
          leftIcon={<RefreshCw size={14} />}
          variant="secondary"
          size="sm"
          loading={loading}
          onClick={fetchDoctors}
        >
          Refresh
        </Button>
      </div>

      <Card padding="none">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary-500)]" />
          </div>
        ) : error ? (
          <div className="p-6 text-center text-danger-500">
            <ShieldAlert className="mx-auto mb-2" size={32} />
            <p>{error}</p>
          </div>
        ) : doctors.length === 0 ? (
          <EmptyState
            title="No doctor accounts"
            description="Registered doctors will appear here for approval."
            size="md"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[var(--color-border-subtle)] text-xs font-semibold text-[var(--color-muted)] uppercase bg-gray-50/50 dark:bg-gray-900/20">
                  <th className="px-6 py-4">Doctor</th>
                  <th className="px-6 py-4">Email</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Registered On</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border-subtle)]">
                {doctors.map((doc) => (
                  <tr key={doc.id} className="hover:bg-[var(--color-border-subtle)]/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <Avatar name={doc.name || doc.email} src={doc.avatar_url || undefined} size="sm" />
                        <span className="text-sm font-semibold text-[var(--color-foreground)]">
                          {doc.name || "Dr. Unnamed"}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-[var(--color-muted)]">{doc.email}</td>
                    <td className="px-6 py-4">{getStatusBadge(doc.status)}</td>
                    <td className="px-6 py-4 text-sm text-[var(--color-muted)]">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {doc.status === "pending" && (
                          <>
                            <Button
                              size="xs"
                              variant="success"
                              leftIcon={<Check size={12} />}
                              loading={actionLoading === doc.id}
                              onClick={() => handleAction(doc.id, "approve")}
                            >
                              Approve
                            </Button>
                            <Button
                              size="xs"
                              variant="danger"
                              leftIcon={<X size={12} />}
                              loading={actionLoading === doc.id}
                              onClick={() => handleAction(doc.id, "reject")}
                            >
                              Reject
                            </Button>
                          </>
                        )}
                        {doc.status === "approved" && (
                          <Button
                            size="xs"
                            variant="secondary"
                            className="text-amber-600 hover:text-amber-700 hover:bg-amber-50 dark:hover:bg-amber-950/20"
                            leftIcon={<UserMinus size={12} />}
                            loading={actionLoading === doc.id}
                            onClick={() => handleAction(doc.id, "deactivate")}
                          >
                            Deactivate
                          </Button>
                        )}
                        {(doc.status === "inactive" || doc.status === "rejected") && (
                          <Button
                            size="xs"
                            variant="primary"
                            leftIcon={<UserCheck size={12} />}
                            loading={actionLoading === doc.id}
                            onClick={() => handleAction(doc.id, "activate")}
                          >
                            Activate
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </motion.div>
  );
}
