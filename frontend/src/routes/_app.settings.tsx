import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "framer-motion";
import { Settings, Bell, Shield, Database, Palette, User } from "lucide-react";
import { useAuthContext } from "@/context/AuthContext";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Tabs, TabList, TabTrigger, TabPanels, TabPanel } from "@/components/ui/Tabs";
import { Avatar } from "@/components/ui/Avatar";

export const Route = createFileRoute("/_app/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const { user } = useAuthContext();
  const [notifications, setNotifications] = useState({
    highRisk: true,
    medication: true,
    weeklyReport: false,
    criticalAlert: true,
  });

  const [thresholds, setThresholds] = useState({
    readmissionAlert: 70,
    complianceWarn: 60,
    deviationAlert: 25,
  });

  const [apiUrl, setApiUrl] = useState(() => {
    return localStorage.getItem("ha_api_url") || (import.meta.env.VITE_API_URL ?? "http://localhost:8000");
  });
  const [testing, setTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<"success" | "error" | "idle">("idle");
  const [statusMessage, setStatusMessage] = useState("");

  const handleTestConnection = async () => {
    setTesting(true);
    setConnectionStatus("idle");
    setStatusMessage("Testing connection...");
    try {
      const res = await fetch(`${apiUrl}/health/detailed`);
      if (res.ok) {
        setConnectionStatus("success");
        setStatusMessage("Backend reachable and saved successfully!");
        localStorage.setItem("ha_api_url", apiUrl);
      } else {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch (err) {
      setConnectionStatus("error");
      setStatusMessage("Failed to connect to backend. Please check the URL.");
    } finally {
      setTesting(false);
    }
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6 max-w-3xl"
    >
      <motion.div variants={staggerItem}>
        <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-[var(--color-muted)]">Configure alerts, API, and dashboard preferences</p>
      </motion.div>

      <motion.div variants={staggerItem}>
        <Tabs defaultTab="profile" variant="line">
          <TabList>
            <TabTrigger id="profile" icon={<User size={14} />}>Profile</TabTrigger>
            <TabTrigger id="notifications" icon={<Bell size={14} />}>Notifications</TabTrigger>
            {user?.role !== "patient" && (
              <TabTrigger id="thresholds" icon={<Shield size={14} />}>Thresholds</TabTrigger>
            )}
            {user?.role === "admin" && (
              <TabTrigger id="api" icon={<Database size={14} />}>API</TabTrigger>
            )}
          </TabList>
          <TabPanels>
            {/* Profile */}
            <TabPanel id="profile">
              <div className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="capitalize">{user?.role ?? "User"} Profile</CardTitle>
                    <CardDescription>Your account information</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center gap-4">
                      <Avatar name={user?.name ?? "User"} size="xl" />
                      <div>
                        <p className="font-semibold text-[var(--color-foreground)]">{user?.name ?? "No Name"}</p>
                        <p className="text-sm text-[var(--color-muted)] capitalize">{user?.role ?? "User"} · General Hospital</p>
                        <Badge variant="primary" size="sm" className="mt-1 capitalize">{user?.role ?? "User"}</Badge>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 pt-2">
                      {[
                        { label: "Full Name", value: user?.name ?? "Not Provided" },
                        { label: "Role / Permission", value: user?.role ? (user.role.charAt(0).toUpperCase() + user.role.slice(1)) : "User" },
                        { label: "Email Address", value: user?.email ?? "Not Provided" },
                        { label: "Hospital", value: "General Hospital" },
                      ].map((f) => (
                        <div key={f.label}>
                          <label className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">{f.label}</label>
                          <p className="mt-1 text-sm text-[var(--color-foreground)]">{f.value}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabPanel>

            {/* Notifications */}
            <TabPanel id="notifications">
              <div className="space-y-4 mt-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Alert Preferences</CardTitle>
                    <CardDescription>Choose which events trigger notifications</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {Object.entries(notifications).map(([key, val]) => (
                      <div key={key} className="flex items-center justify-between py-2 border-b border-[var(--color-border-subtle)] last:border-0">
                        <div>
                          <p className="text-sm font-medium text-[var(--color-foreground)] capitalize">
                            {key.replace(/([A-Z])/g, " $1")}
                          </p>
                          <p className="text-xs text-[var(--color-muted)]">{NOTIF_DESCRIPTIONS[key]}</p>
                        </div>
                        <button
                          onClick={() => setNotifications(n => ({ ...n, [key]: !val }))}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${val ? "bg-[var(--color-primary-500)]" : "bg-[var(--color-border)]"}`}
                          role="switch"
                          aria-checked={val}
                        >
                          <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${val ? "translate-x-6" : "translate-x-1"}`} />
                        </button>
                      </div>
                    ))}
                    <Button size="sm" className="mt-2">Save Preferences</Button>
                  </CardContent>
                </Card>
              </div>
            </TabPanel>

            {/* Thresholds */}
            {user?.role !== "patient" && (
              <TabPanel id="thresholds">
                <div className="space-y-4 mt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>Alert Thresholds</CardTitle>
                      <CardDescription>Numeric thresholds that trigger risk alerts</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-5">
                      {Object.entries(thresholds).map(([key, val]) => (
                        <div key={key}>
                          <div className="flex items-center justify-between mb-1">
                            <label className="text-sm font-medium text-[var(--color-foreground)] capitalize">
                              {key.replace(/([A-Z])/g, " $1")}
                            </label>
                            <Badge variant="primary" size="sm">{val}%</Badge>
                          </div>
                          <input
                            type="range"
                            min={0}
                            max={100}
                            value={val}
                            onChange={(e) => setThresholds(t => ({ ...t, [key]: +e.target.value }))}
                            className="w-full accent-[var(--color-primary-500)]"
                          />
                          <div className="flex justify-between mt-0.5">
                            <span className="text-[10px] text-[var(--color-muted)]">0%</span>
                            <span className="text-[10px] text-[var(--color-muted)]">100%</span>
                          </div>
                        </div>
                      ))}
                      <Button size="sm">Save Thresholds</Button>
                    </CardContent>
                  </Card>
                </div>
              </TabPanel>
            )}

            {/* API */}
            {user?.role === "admin" && (
              <TabPanel id="api">
                <div className="space-y-4 mt-4">
                  <Card>
                    <CardHeader>
                      <CardTitle>API Configuration</CardTitle>
                      <CardDescription>Backend connection settings</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <label className="text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">API Base URL</label>
                        <input
                          type="text"
                          value={apiUrl}
                          onChange={(e) => setApiUrl(e.target.value)}
                          className="mt-1 w-full h-9 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-400)]"
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${connectionStatus === "success" ? "bg-[var(--color-success-500)]" : connectionStatus === "error" ? "bg-[var(--color-danger-500)]" : "bg-gray-400"}`} />
                        <span className="text-sm text-[var(--color-muted)]">
                          {statusMessage || (localStorage.getItem("ha_api_url") ? "Backend configured and saved" : "Default environment API active")}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-3 pt-2">
                        {API_ENDPOINTS.map((ep) => (
                          <div key={ep.path} className="rounded-xl bg-[var(--color-border-subtle)] p-3">
                            <p className="text-xs font-mono font-semibold text-[var(--color-foreground)]">{ep.method} {ep.path}</p>
                            <p className="text-[10px] text-[var(--color-muted)] mt-0.5">{ep.desc}</p>
                          </div>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={handleTestConnection} disabled={testing}>
                          {testing ? "Testing..." : "Test & Save Connection"}
                        </Button>
                        {localStorage.getItem("ha_api_url") && (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => {
                              localStorage.removeItem("ha_api_url");
                              window.location.reload();
                            }}
                          >
                            Reset to Default
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabPanel>
            )}
          </TabPanels>
        </Tabs>
      </motion.div>
    </motion.div>
  );
}

const NOTIF_DESCRIPTIONS: Record<string, string> = {
  highRisk: "Alert when a patient's Risk Level changes to High",
  medication: "Alert when 3+ consecutive medications are missed",
  weeklyReport: "Receive a weekly compliance summary report",
  criticalAlert: "Immediate notification for Critical recovery status",
};

const API_ENDPOINTS = [
  { method: "GET", path: "/patients", desc: "Paginated patient list" },
  { method: "GET", path: "/patients/{id}/summary", desc: "30-day trend data" },
  { method: "POST", path: "/predict", desc: "ML prediction endpoint" },
  { method: "GET", path: "/dashboard/stats", desc: "Aggregated stats" },
];
