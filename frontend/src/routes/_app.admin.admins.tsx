import React, { useState, useEffect } from "react";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, ShieldAlert, RefreshCw, UserPlus, Trash2, Key, Check, X, ShieldAlert as AlertIcon } from "lucide-react";
import { getStoredUser } from "@/lib/auth";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Avatar } from "@/components/ui/Avatar";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { staggerContainer, staggerItem } from "@/lib/motion";

export const Route = createFileRoute("/_app/admin/admins")({
  beforeLoad: () => {
    const user = getStoredUser();
    if (!user || user.role !== "admin") {
      throw redirect({ to: "/" });
    }
  },
  component: AdminManagementPage,
});

interface AdminUser {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  role: string;
  is_active: boolean;
  created_at: string;
}

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function AdminManagementPage() {
  const currentUser = getStoredUser();
  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Create Admin Form State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newName, setNewName] = useState("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchAdmins = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem("ha_access");
      const res = await fetch(`${BASE_URL}/api/admin/admins`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) throw new Error("Failed to fetch admin list");
      const data = await res.json();
      setAdmins(data);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdmins();
  }, []);

  const handleToggleStatus = async (id: string, currentlyActive: boolean) => {
    if (id === currentUser?.id) {
      alert("You cannot deactivate your own admin account.");
      return;
    }
    setActionLoading(id);
    const action = currentlyActive ? "deactivate" : "activate";
    try {
      const token = localStorage.getItem("ha_access");
      const res = await fetch(`${BASE_URL}/api/admin/admins/${id}/${action}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Failed to ${action} admin`);
      }
      await fetchAdmins();
    } catch (err: any) {
      alert(err.message || "Action failed");
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreateAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError(null);
    try {
      const token = localStorage.getItem("ha_access");
      const res = await fetch(`${BASE_URL}/api/admin/admins`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          email: newEmail,
          password: newPassword,
          name: newName,
          role: "admin",
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to create admin");
      }
      // Reset form & close modal
      setNewEmail("");
      setNewPassword("");
      setNewName("");
      setShowCreateModal(false);
      await fetchAdmins();
    } catch (err: any) {
      setCreateError(err.message || "Failed to create admin account");
    } finally {
      setCreateLoading(false);
    }
  };

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">Admin Management</h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">Create and manage administrator accounts with system access</p>
        </div>
        <div className="flex gap-2">
          <Button
            leftIcon={<RefreshCw size={14} />}
            variant="secondary"
            size="sm"
            loading={loading}
            onClick={fetchAdmins}
          >
            Refresh
          </Button>
          <Button
            leftIcon={<UserPlus size={14} />}
            variant="primary"
            size="sm"
            onClick={() => setShowCreateModal(true)}
          >
            Create Admin
          </Button>
        </div>
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
        ) : admins.length === 0 ? (
          <EmptyState
            title="No administrators found"
            description="You should have at least one admin account."
            size="md"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[var(--color-border-subtle)] text-xs font-semibold text-[var(--color-muted)] uppercase bg-gray-50/50 dark:bg-gray-900/20">
                  <th className="px-6 py-4">Admin Name</th>
                  <th className="px-6 py-4">Email</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Created On</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border-subtle)]">
                {admins.map((admin) => (
                  <tr key={admin.id} className="hover:bg-[var(--color-border-subtle)]/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <Avatar name={admin.name || admin.email} src={admin.avatar_url || undefined} size="sm" />
                        <span className="text-sm font-semibold text-[var(--color-foreground)]">
                          {admin.name || "Unnamed Admin"}
                          {admin.id === currentUser?.id && (
                            <span className="ml-2 px-1.5 py-0.5 text-[10px] bg-primary-100 text-primary-700 rounded dark:bg-primary-900/30 dark:text-primary-300 font-bold">You</span>
                          )}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-[var(--color-muted)]">{admin.email}</td>
                    <td className="px-6 py-4">
                      {admin.is_active ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-success-50 text-success-700 dark:bg-green-900/20 dark:text-green-300">Active</span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400">Suspended</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-[var(--color-muted)]">
                      {new Date(admin.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {admin.id !== currentUser?.id ? (
                        <Button
                          size="xs"
                          variant={admin.is_active ? "danger" : "success"}
                          leftIcon={admin.is_active ? <X size={12} /> : <Check size={12} />}
                          loading={actionLoading === admin.id}
                          onClick={() => handleToggleStatus(admin.id, admin.is_active)}
                        >
                          {admin.is_active ? "Suspend" : "Activate"}
                        </Button>
                      ) : (
                        <span className="text-xs text-[var(--color-muted)] font-medium italic">Active System User</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Create Admin Modal */}
      <Modal open={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Administrator Account">
        <form onSubmit={handleCreateAdmin} className="space-y-4 pt-2">
          {createError && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-danger-50 dark:bg-red-900/20 text-danger-600 dark:text-red-400 text-sm">
              <AlertIcon size={16} className="shrink-0" />
              <span>{createError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Full Name</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="e.g., Jane Doe"
              required
              className="w-full h-11 px-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Email Address</label>
            <input
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="e.g., admin2@hospital.com"
              required
              className="w-full h-11 px-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1.5 uppercase tracking-wide">Account Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Min. 8 characters"
              required
              minLength={8}
              className="w-full h-11 px-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary-400"
            />
          </div>

          <div className="flex gap-3 justify-end pt-4 border-t border-gray-100 dark:border-gray-800">
            <Button type="button" variant="secondary" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={createLoading}>
              Create Account
            </Button>
          </div>
        </form>
      </Modal>
    </motion.div>
  );
}
