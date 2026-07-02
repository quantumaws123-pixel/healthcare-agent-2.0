/**
 * /workbench — Doctor Workbench
 * Main clinical workspace for doctors: patient queue, risk prioritisation,
 * AI explanations, alerts, quick actions, and trend previews.
 * Reuses all existing APIs — no new backend required.
 */
import React, { useState, useMemo, useEffect } from "react";
import { createFileRoute, Link, redirect } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import {
  AlertTriangle, Activity, Users, TrendingUp, Heart, Search,
  Filter, RefreshCw, ChevronRight, Phone, Calendar, Pill,
  ClipboardList, Bot, FileText, Stethoscope, Bell, CheckCircle,
  X, ArrowUpRight, Zap, BarChart3, Eye,
} from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getStoredUser } from "@/lib/auth";
import { getPatients, getDashboardStats, getMyDoctorPatients, queryKeys, hospitalQueryKeys, type GetPatientsParams } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge, RecoveryBadge } from "@/components/ui/StatusBadge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Avatar } from "@/components/ui/Avatar";
import { FloatingPanel } from "@/components/ui/FloatingPanel";
import { staggerContainer, staggerItem } from "@/lib/motion";
import type { PatientSummary, RiskLevel, RecoveryStatus } from "@/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/workbench")({
  beforeLoad: () => {
    const user = getStoredUser();
    if (!user || (user.role !== "doctor" && user.role !== "admin")) {
      throw redirect({ to: "/" });
    }
  },
  component: DoctorWorkbench,
});

// ── Suggested actions per risk level ─────────────────────────────────────
const RISK_ACTIONS: Record<string, { label: string; icon: React.ElementType; color: string }[]> = {
  Critical: [
    { label: "Recommend Hospitalization", icon: AlertTriangle, color: "text-red-600" },
    { label: "Call Patient Now",          icon: Phone,         color: "text-red-500" },
    { label: "Review Medication",         icon: Pill,          color: "text-orange-500" },
  ],
  High: [
    { label: "Schedule Follow-up",        icon: Calendar,      color: "text-orange-500" },
    { label: "Call Patient",              icon: Phone,         color: "text-amber-500" },
    { label: "Review Medication",         icon: Pill,          color: "text-amber-500" },
  ],
  Medium: [
    { label: "Increase Monitoring",       icon: Activity,      color: "text-yellow-600" },
    { label: "Schedule Follow-up",        icon: Calendar,      color: "text-yellow-500" },
    { label: "Continue Monitoring",       icon: CheckCircle,   color: "text-blue-500" },
  ],
  Low: [
    { label: "Continue Monitoring",       icon: CheckCircle,   color: "text-green-500" },
    { label: "Routine Check-up",          icon: Stethoscope,   color: "text-green-500" },
  ],
};

// ── Alert generation from patient data ──────────────────────────────────
function getAlerts(p: PatientSummary): string[] {
  const alerts: string[] = [];
  if (p.Readmission_Probability > 0.7) alerts.push("⚠️ Critical readmission risk");
  if (p.Compliance_Score < 50)          alerts.push("💊 Very low compliance");
  else if (p.Compliance_Score < 65)     alerts.push("📉 Low compliance");
  if (p.Risk_Level === "Critical")      alerts.push("🚨 Critical risk level");
  return alerts;
}

// ── Risk priority sort value ─────────────────────────────────────────────
const RISK_ORDER: Record<string, number> = { Critical: 0, High: 1, Medium: 2, Low: 3 };

// ── Compliance color ─────────────────────────────────────────────────────
function complianceColor(score: number): string {
  if (score >= 80) return "text-green-600 dark:text-green-400";
  if (score >= 60) return "text-amber-600 dark:text-amber-400";
  return "text-red-600 dark:text-red-400";
}

// ── Main component ────────────────────────────────────────────────────────
function DoctorWorkbench() {
  const qc = useQueryClient();
  const [search, setSearch]             = useState("");
  const [riskFilter, setRiskFilter]     = useState("All");
  const [diseaseFilter, setDiseaseFilter] = useState("All");
  const [sortBy, setSortBy]             = useState<"risk" | "compliance" | "recovery">("risk");
  const [expandedId, setExpandedId]     = useState<string | null>(null);
  const [dismissedAlerts, setDismissed] = useState<Set<string>>(new Set());

  const { data: patientsData, isLoading, refetch } = useQuery({
    queryKey: queryKeys.patients({ page_size: 100 }),
    queryFn:  () => getPatients({ page_size: 100 }),
  });

  const { data: stats } = useQuery({
    queryKey: queryKeys.dashboardStats(),
    queryFn:  getDashboardStats,
  });

  const { data: myPatients = [] } = useQuery({
    queryKey: hospitalQueryKeys.myDoctorPatients(),
    queryFn:  getMyDoctorPatients,
  });

  const allPatients: PatientSummary[] = patientsData?.data ?? [];

  // Filter to only assigned patients if we have assignment data; else show all
  const myPatientIds = useMemo(() =>
    new Set(myPatients.map(p => p.user_id)), [myPatients]);

  const basePatients = useMemo(() =>
    myPatients.length > 0
      ? allPatients.filter(p => myPatientIds.has(p.Patient_ID))
      : allPatients,
    [allPatients, myPatientIds, myPatients.length]);

  // Apply search + filters
  const filtered = useMemo(() => {
    let list = [...basePatients];
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(p =>
        p.Patient_ID.toLowerCase().includes(q) ||
        p.Disease_Type.toLowerCase().includes(q)
      );
    }
    if (riskFilter !== "All")    list = list.filter(p => p.Risk_Level === riskFilter);
    if (diseaseFilter !== "All") list = list.filter(p => p.Disease_Type === diseaseFilter);

    // Sort
    list.sort((a, b) => {
      if (sortBy === "risk")
        return (RISK_ORDER[a.Risk_Level] ?? 4) - (RISK_ORDER[b.Risk_Level] ?? 4)
          || b.Readmission_Probability - a.Readmission_Probability;
      if (sortBy === "compliance") return a.Compliance_Score - b.Compliance_Score;
      return a.Recovery_Status.localeCompare(b.Recovery_Status);
    });
    return list;
  }, [basePatients, search, riskFilter, diseaseFilter, sortBy]);

  // KPI computations
  const criticalCount    = basePatients.filter(p => p.Risk_Level === "Critical" || p.Risk_Level === "High").length;
  const avgRecovery      = basePatients.length
    ? Math.round(basePatients.reduce((s, p) => s + p.Readmission_Probability * 100, 0) / basePatients.length)
    : 0;
  const avgCompliance    = basePatients.length
    ? Math.round(basePatients.reduce((s, p) => s + p.Compliance_Score, 0) / basePatients.length)
    : 0;
  const needAttention    = basePatients.filter(p => p.Readmission_Probability > 0.5 || p.Compliance_Score < 60).length;

  // Disease types for filter
  const diseaseTypes = useMemo(() =>
    Array.from(new Set(allPatients.map(p => p.Disease_Type))).sort(),
    [allPatients]);

  // Global alerts (non-dismissed critical patients)
  const globalAlerts = useMemo(() =>
    basePatients
      .filter(p => p.Risk_Level === "Critical" || p.Readmission_Probability > 0.75)
      .filter(p => !dismissedAlerts.has(p.Patient_ID))
      .slice(0, 5),
    [basePatients, dismissedAlerts]);

  return (
    <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="space-y-5">

      {/* ── Header ─────────────────────────────────────────────────────── */}
      <motion.div variants={staggerItem} className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Stethoscope size={22} className="text-primary-500" />
            Doctor Workbench
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {basePatients.length} assigned patients · {criticalCount} need urgent attention
          </p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" leftIcon={<RefreshCw size={14} />}
            loading={isLoading} onClick={() => { refetch(); qc.invalidateQueries(); }}>
            Refresh
          </Button>
          <Link to="/assistant">
            <Button size="sm" variant="primary" leftIcon={<Bot size={14} />}>
              AI Assistant
            </Button>
          </Link>
        </div>
      </motion.div>

      {/* ── KPI Cards ──────────────────────────────────────────────────── */}
      <motion.div variants={staggerItem} className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: "Assigned Patients",    value: basePatients.length, icon: Users,         color: "bg-blue-50 dark:bg-blue-900/20",   text: "text-blue-600 dark:text-blue-400" },
          { label: "Need Urgent Attention",value: criticalCount,        icon: AlertTriangle,  color: "bg-red-50 dark:bg-red-900/20",    text: "text-red-600 dark:text-red-400" },
          { label: "Avg Compliance",       value: `${avgCompliance}%`,  icon: TrendingUp,     color: "bg-green-50 dark:bg-green-900/20",text: "text-green-600 dark:text-green-400" },
          { label: "Patients at Risk",     value: needAttention,        icon: Heart,          color: "bg-amber-50 dark:bg-amber-900/20",text: "text-amber-600 dark:text-amber-400" },
        ].map(k => (
          <Card key={k.label} padding="sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{k.label}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{k.value}</p>
              </div>
              <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", k.color)}>
                <k.icon size={18} className={k.text} />
              </div>
            </div>
          </Card>
        ))}
      </motion.div>

      {/* ── Global Alerts ──────────────────────────────────────────────── */}
      <AnimatePresence>
        {globalAlerts.length > 0 && (
          <motion.div variants={staggerItem}
            initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}>
            <div className="rounded-2xl border border-red-200 dark:border-red-800/50 bg-red-50 dark:bg-red-900/10 px-4 py-3">
              <p className="text-xs font-bold text-red-700 dark:text-red-400 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                <Bell size={12} /> Critical Alerts ({globalAlerts.length})
              </p>
              <div className="space-y-1.5">
                {globalAlerts.map(p => (
                  <div key={p.Patient_ID} className="flex items-center justify-between">
                    <span className="text-xs text-red-700 dark:text-red-300">
                      🚨 Patient {p.Patient_ID} — {p.Risk_Level} risk · {Math.round(p.Readmission_Probability * 100)}% readmission probability
                    </span>
                    <button onClick={() => setDismissed(s => new Set([...s, p.Patient_ID]))}
                      className="text-red-400 hover:text-red-600 transition-colors ml-2">
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Filters + Search ───────────────────────────────────────────── */}
      <motion.div variants={staggerItem} className="flex flex-wrap gap-2 items-center">
        {/* Search */}
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search patient ID or disease…"
            className="w-full h-9 pl-8 pr-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-400"
          />
          {search && (
            <button onClick={() => setSearch("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              <X size={12} />
            </button>
          )}
        </div>

        {/* Risk filter */}
        <select value={riskFilter} onChange={e => setRiskFilter(e.target.value)}
          className="h-9 px-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-400">
          <option value="All">All Risk Levels</option>
          {["Critical","High","Medium","Low"].map(r => <option key={r}>{r}</option>)}
        </select>

        {/* Disease filter */}
        <select value={diseaseFilter} onChange={e => setDiseaseFilter(e.target.value)}
          className="h-9 px-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-400">
          <option value="All">All Diseases</option>
          {diseaseTypes.map(d => <option key={d}>{d}</option>)}
        </select>

        {/* Sort */}
        <select value={sortBy} onChange={e => setSortBy(e.target.value as any)}
          className="h-9 px-3 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-400">
          <option value="risk">Sort: Risk Priority</option>
          <option value="compliance">Sort: Lowest Compliance</option>
          <option value="recovery">Sort: Recovery Status</option>
        </select>

        <span className="text-xs text-gray-400 ml-auto">{filtered.length} patient{filtered.length !== 1 ? "s" : ""}</span>
      </motion.div>

      {/* ── Patient Queue ───────────────────────────────────────────────── */}
      <motion.div variants={staggerItem} className="space-y-2">
        {isLoading && (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
            ))}
          </div>
        )}

        {!isLoading && basePatients.length === 0 && (
          <Card padding="lg" className="text-center py-12">
            <Users size={36} className="mx-auto text-gray-300 mb-3" />
            <p className="text-base font-semibold text-gray-700 dark:text-gray-300">No patients assigned yet</p>
            <p className="text-sm text-gray-500 mt-1 max-w-xs mx-auto">
              Ask your administrator to assign patients to your account. Once assigned, they will appear here.
            </p>
          </Card>
        )}

        {!isLoading && basePatients.length > 0 && filtered.length === 0 && (
          <Card padding="lg" className="text-center py-10">
            <p className="text-sm font-medium text-gray-500">No patients match your current filters.</p>
            <button
              onClick={() => { setSearch(""); setRiskFilter("All"); setDiseaseFilter("All"); }}
              className="mt-2 text-xs text-primary-500 hover:text-primary-700 underline"
            >
              Clear all filters
            </button>
          </Card>
        )}

        {filtered.map((patient, idx) => (
          <PatientQueueRow
            key={patient.Patient_ID}
            patient={patient}
            rank={idx + 1}
            expanded={expandedId === patient.Patient_ID}
            onToggle={() => setExpandedId(id => id === patient.Patient_ID ? null : patient.Patient_ID)}
          />
        ))}
      </motion.div>
    </motion.div>
  );
}

// ── Patient Queue Row ─────────────────────────────────────────────────────

interface RowProps {
  patient: PatientSummary;
  rank: number;
  expanded: boolean;
  onToggle: () => void;
}

function PatientQueueRow({ patient: p, rank, expanded, onToggle }: RowProps) {
  const riskPct    = Math.round(p.Readmission_Probability * 100);
  const alerts     = getAlerts(p);
  const actions    = RISK_ACTIONS[p.Risk_Level] ?? RISK_ACTIONS.Low;
  const isCritical = p.Risk_Level === "Critical" || p.Risk_Level === "High";

  // Simulated SHAP-style explanation from available data
  const shapReasons: string[] = [];
  if (p.Compliance_Score < 60)          shapReasons.push(`Low compliance (${Math.round(p.Compliance_Score)}%) — major risk driver`);
  if (p.Readmission_Probability > 0.5)  shapReasons.push(`High readmission probability (${riskPct}%)`);
  if (p.Recovery_Status === "Worsening" || p.Recovery_Status === "Critical") shapReasons.push(`Recovery status: ${p.Recovery_Status}`);
  if (p.Latest_Day > 20)                shapReasons.push(`Extended monitoring (Day ${p.Latest_Day}) — prolonged recovery`);
  if (shapReasons.length === 0)         shapReasons.push("Stable indicators — continue monitoring");

  return (
    <motion.div
      layout
      className={cn(
        "rounded-2xl border transition-all duration-200",
        isCritical
          ? "border-red-200 dark:border-red-800/50 bg-red-50/30 dark:bg-red-900/5"
          : "border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900",
        expanded && "shadow-lg"
      )}
    >
      {/* ── Collapsed row ── */}
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer select-none"
        onClick={onToggle}
      >
        {/* Rank + urgency indicator */}
        <div className={cn(
          "w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold",
          p.Risk_Level === "Critical" ? "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300" :
          p.Risk_Level === "High"     ? "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300" :
          p.Risk_Level === "Medium"   ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300" :
                                        "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300"
        )}>
          {rank}
        </div>

        {/* Avatar + name */}
        <Avatar name={p.Patient_ID} size="sm" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-gray-900 dark:text-white truncate">
              Patient {p.Patient_ID}
            </span>
            <RiskBadge level={p.Risk_Level as RiskLevel} size="sm" />
            <RecoveryBadge status={p.Recovery_Status as RecoveryStatus} size="sm" />
          </div>
          <p className="text-xs text-gray-500 mt-0.5">
            {p.Disease_Type} · {p.Age}y · {p.Gender} · Day {p.Latest_Day}
          </p>
        </div>

        {/* Compact metrics */}
        <div className="hidden sm:flex items-center gap-4 shrink-0">
          <MetricPill label="Risk" value={`${riskPct}%`} highlight={riskPct > 60} />
          <MetricPill label="Compliance" value={`${Math.round(p.Compliance_Score)}%`} highlight={p.Compliance_Score < 60} />
        </div>

        {/* Alert indicators */}
        {alerts.length > 0 && (
          <Badge variant="danger" size="sm" className="shrink-0 hidden md:flex">
            {alerts.length} alert{alerts.length > 1 ? "s" : ""}
          </Badge>
        )}

        <ChevronRight size={14} className={cn(
          "text-gray-400 shrink-0 transition-transform duration-200",
          expanded && "rotate-90"
        )} />
      </div>

      {/* ── Expanded detail ── */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-800 pt-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                {/* AI Metrics + SHAP */}
                <div className="space-y-3">
                  <p className="text-xs font-bold uppercase tracking-wide text-gray-500 flex items-center gap-1.5">
                    <Zap size={11} className="text-primary-500" /> AI Analysis
                  </p>
                  <ProgressBar label="Readmission Risk"  value={riskPct}                   color={riskPct > 60 ? "#ef4444" : riskPct > 30 ? "#f59e0b" : "#22c55e"} showValue size="sm" />
                  <ProgressBar label="Compliance Score"  value={Math.round(p.Compliance_Score)} color={p.Compliance_Score < 60 ? "#ef4444" : "#22c55e"} showValue size="sm" />

                  <div className="pt-1">
                    <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mb-1.5">
                      Why this risk level:
                    </p>
                    <ul className="space-y-1">
                      {shapReasons.map((r, i) => (
                        <li key={i} className="text-xs text-gray-600 dark:text-gray-400 flex gap-1.5">
                          <span className="text-primary-500 shrink-0">•</span>
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* 7-day Trend Sparkline */}
                <div className="space-y-3">
                  <p className="text-xs font-bold uppercase tracking-wide text-gray-500 flex items-center gap-1.5">
                    <BarChart3 size={11} className="text-blue-500" /> Status
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { label: "Risk",     value: p.Risk_Level,        bg: isCritical ? "bg-red-50 dark:bg-red-900/20" : "bg-green-50 dark:bg-green-900/20" },
                      { label: "Recovery", value: p.Recovery_Status,   bg: "bg-blue-50 dark:bg-blue-900/20" },
                      { label: "Day",      value: `Day ${p.Latest_Day}`,bg: "bg-gray-50 dark:bg-gray-800" },
                      { label: "Doctor Rec", value: p.Doctor_Recommendation.slice(0, 22) + "…", bg: "bg-purple-50 dark:bg-purple-900/20" },
                    ].map(s => (
                      <div key={s.label} className={cn("rounded-xl p-2 text-center", s.bg)}>
                        <p className="text-[10px] text-gray-500 uppercase tracking-wide">{s.label}</p>
                        <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 mt-0.5 truncate">{s.value}</p>
                      </div>
                    ))}
                  </div>

                  {/* Alerts */}
                  {alerts.length > 0 && (
                    <div className="space-y-1">
                      {alerts.map((a, i) => (
                        <p key={i} className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-2 py-1 rounded-lg">{a}</p>
                      ))}
                    </div>
                  )}
                </div>

                {/* Suggested Actions + Quick Links */}
                <div className="space-y-3">
                  <p className="text-xs font-bold uppercase tracking-wide text-gray-500 flex items-center gap-1.5">
                    <ArrowUpRight size={11} className="text-green-500" /> Actions
                  </p>

                  {/* Suggested */}
                  <div className="space-y-1.5">
                    {actions.map(action => (
                      <button key={action.label}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800/50 hover:border-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-all text-left group">
                        <action.icon size={13} className={action.color} />
                        <span className="text-xs font-medium text-gray-700 dark:text-gray-300 group-hover:text-primary-700 dark:group-hover:text-primary-300">
                          {action.label}
                        </span>
                      </button>
                    ))}
                  </div>

                  {/* Quick navigation links */}
                  <div className="grid grid-cols-2 gap-1.5 pt-1">
                    <Link to="/patients/$patientId" params={{ patientId: p.Patient_ID }}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 text-xs font-medium hover:bg-primary-100 transition-colors">
                      <Eye size={11} /> View Record
                    </Link>
                    <Link to="/assistant"
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-xs font-medium hover:bg-blue-100 transition-colors">
                      <Bot size={11} /> AI Assistant
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// ── Small metric pill ─────────────────────────────────────────────────────
function MetricPill({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="text-center">
      <p className="text-[10px] text-gray-400 uppercase tracking-wide">{label}</p>
      <p className={cn("text-sm font-bold tabular-nums", highlight ? "text-red-600 dark:text-red-400" : "text-gray-800 dark:text-gray-200")}>
        {value}
      </p>
    </div>
  );
}
