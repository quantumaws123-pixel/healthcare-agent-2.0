import React, { useState, useEffect } from "react";
import { Users, UserCheck, Clock, AlertTriangle, Activity, Loader2, ClipboardList, Shield } from "lucide-react";
import { Link } from "@tanstack/react-router";
import { FloatingPanel } from "@/components/ui/FloatingPanel";
import { StatCard } from "@/components/ui/StatCard";
import { useDashboardStats, usePatients } from "@/hooks/usePatients";

interface DoctorUser {
  id: string;
  email: string;
  name: string | null;
  status: "pending" | "approved" | "rejected" | "inactive";
  is_active: boolean;
  created_at: string;
}

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function AdminDashboard() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: patientsData, isLoading: patientsLoading } = usePatients({ page_size: 100 });
  const [doctors, setDoctors] = useState<DoctorUser[]>([]);
  const [doctorsLoading, setDoctorsLoading] = useState(true);

  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        const token = localStorage.getItem("ha_access");
        const res = await fetch(`${BASE_URL}/api/admin/doctors`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          setDoctors(data);
        }
      } catch (err) {
        console.error("Failed to fetch doctors:", err);
      } finally {
        setDoctorsLoading(false);
      }
    };
    fetchDoctors();
  }, []);

  if (statsLoading || patientsLoading || doctorsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-primary-500" size={32} />
      </div>
    );
  }

  const totalPatients = patientsData?.total ?? 0;
  const totalDoctors = doctors.length;
  const pendingRequests = doctors.filter((d) => d.status === "pending").length;
  const highRiskCount = stats?.risk_distribution
    ? stats.risk_distribution.high + stats.risk_distribution.critical
    : 0;

  // Build a dynamic recent activity list based on actual doctor registrations
  const recentActivity = doctors
    .slice(0, 5)
    .map((doc) => {
      if (doc.status === "pending") {
        return {
          title: `Dr. ${doc.name || doc.email} registered - Pending approval`,
          time: new Date(doc.created_at).toLocaleDateString(),
          color: "bg-amber-500",
        };
      } else if (doc.status === "approved") {
        return {
          title: `Doctor approved: Dr. ${doc.name || doc.email}`,
          time: new Date(doc.created_at).toLocaleDateString(),
          color: "bg-success-500",
        };
      } else {
        return {
          title: `Doctor account deactivated: Dr. ${doc.name || doc.email}`,
          time: new Date(doc.created_at).toLocaleDateString(),
          color: "bg-danger-500",
        };
      }
    });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Admin Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">System overview and management</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link to="/patients" className="block">
          <StatCard
            label="Total Patients"
            value={String(totalPatients)}
            icon={Users}
            color="blue"
          />
        </Link>
        <Link to="/admin/doctors" className="block">
          <StatCard
            label="Total Doctors"
            value={String(totalDoctors)}
            icon={UserCheck}
            color="green"
          />
        </Link>
        <Link to="/admin/doctors" className="block">
          <StatCard
            label="Pending Requests"
            value={String(pendingRequests)}
            icon={Clock}
            color="amber"
          />
        </Link>
        <Link to="/patients" className="block">
          <StatCard
            label="High Risk Patients"
            value={String(highRiskCount)}
            icon={AlertTriangle}
            color="red"
          />
        </Link>
      </div>

      {/* Quick Actions */}
      <FloatingPanel>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Link to="/admin/doctors" className="flex items-start gap-3 p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all group cursor-pointer">
            <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center group-hover:bg-primary-200 transition-colors">
              <UserCheck size={20} className="text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">Approve Doctors</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{pendingRequests} pending</p>
            </div>
          </Link>
          <Link to="/admin/assign" className="flex items-start gap-3 p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all group cursor-pointer">
            <div className="w-10 h-10 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center group-hover:bg-green-200 transition-colors">
              <ClipboardList size={20} className="text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">Assign Doctors</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Match patients to doctors</p>
            </div>
          </Link>
          <Link to="/admin/admins" className="flex items-start gap-3 p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all group cursor-pointer">
            <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center group-hover:bg-purple-200 transition-colors">
              <Shield size={20} className="text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">Manage Admins</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">Create or suspend admins</p>
            </div>
          </Link>
          <Link to="/models" className="flex items-start gap-3 p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all group cursor-pointer">
            <div className="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center group-hover:bg-primary-200 transition-colors">
              <Activity size={20} className="text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900 dark:text-white">ML Models</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">View model performance</p>
            </div>
          </Link>
        </div>
      </FloatingPanel>

      {/* Recent Activity */}
      <FloatingPanel>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h2>
        {recentActivity.length === 0 ? (
          <p className="text-sm text-gray-500 py-4 text-center">No recent administrative activity.</p>
        ) : (
          <div className="space-y-3">
            {recentActivity.map((item, i) => (
              <div
                key={i}
                className="flex items-start gap-3 py-2 border-b border-gray-100 dark:border-gray-800 last:border-0"
              >
                <div className={`mt-1 w-2 h-2 rounded-full shrink-0 ${item.color}`} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{item.title}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{item.time}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </FloatingPanel>
    </div>
  );
}
