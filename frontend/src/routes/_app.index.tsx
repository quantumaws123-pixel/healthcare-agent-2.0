import { createFileRoute } from "@tanstack/react-router";
import { useAuthContext } from "@/context/AuthContext";
import { AdminDashboard } from "@/components/dashboards/AdminDashboard";
import { DoctorDashboard } from "@/components/dashboards/DoctorDashboard";
import { PatientDashboard } from "@/components/dashboards/PatientDashboard";

export const Route = createFileRoute("/_app/")({ component: DashboardOverview });

function DashboardOverview() {
  const { user } = useAuthContext();
  const role = user?.role;

  if (role === "admin") {
    return <AdminDashboard />;
  }
  if (role === "doctor") {
    return <DoctorDashboard />;
  }
  if (role === "patient") {
    return <PatientDashboard />;
  }

  // Fallback (should not be reached under normal authenticated circumstances)
  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-bold">Welcome</h2>
      <p className="text-gray-500 mt-2">Please contact your administrator if you cannot see your dashboard.</p>
    </div>
  );
}
