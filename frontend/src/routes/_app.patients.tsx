import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { motion } from "framer-motion";
import { Users, Search, Filter, ChevronRight, RefreshCw } from "lucide-react";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { SearchBar } from "@/components/ui/SearchBar";
import { RiskBadge, RecoveryBadge } from "@/components/ui/StatusBadge";
import { Avatar } from "@/components/ui/Avatar";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { SkeletonTableRow } from "@/components/ui/Skeleton";
import { ProgressBar } from "@/components/ui/ProgressBar";
import type { RiskLevel, RecoveryStatus, DiseaseType } from "@/types";

export const Route = createFileRoute("/_app/patients")({
  component: PatientsPage,
});

const DISEASE_TYPES: DiseaseType[] = [
  "Cardiac", "Diabetes", "Hypertension", "COPD",
  "Kidney Disease", "Asthma", "Stroke Recovery", "Post Surgery",
];
const RISK_LEVELS: RiskLevel[] = ["Low", "Medium", "High"];

function PatientsPage() {
  const [search, setSearch] = useState("");
  const [diseaseFilter, setDiseaseFilter] = useState<string>("All");
  const [riskFilter, setRiskFilter] = useState<string>("All");
  const [page, setPage] = useState(1);
  const isLoading = false;

  const filtered = MOCK_PATIENTS.filter((p) => {
    const matchSearch =
      !search || p.id.toLowerCase().includes(search.toLowerCase());
    const matchDisease = diseaseFilter === "All" || p.disease === diseaseFilter;
    const matchRisk = riskFilter === "All" || p.risk === riskFilter;
    return matchSearch && matchDisease && matchRisk;
  });

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={staggerItem} className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-foreground)] tracking-tight">
            Patients
          </h1>
          <p className="mt-1 text-sm text-[var(--color-muted)]">
            {filtered.length} patients · Post-discharge monitoring
          </p>
        </div>
        <Button leftIcon={<RefreshCw size={14} />} variant="secondary" size="sm">
          Refresh
        </Button>
      </motion.div>

      {/* Filters */}
      <motion.div variants={staggerItem} className="flex flex-wrap gap-3 items-center">
        <div className="w-64">
          <SearchBar
            placeholder="Search patient ID…"
            value={search}
            onChange={setSearch}
          />
        </div>
        <select
          value={diseaseFilter}
          onChange={(e) => setDiseaseFilter(e.target.value)}
          className="h-9 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-400)]"
        >
          <option value="All">All Diseases</option>
          {DISEASE_TYPES.map((d) => <option key={d}>{d}</option>)}
        </select>
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          className="h-9 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-400)]"
        >
          <option value="All">All Risk Levels</option>
          {RISK_LEVELS.map((r) => <option key={r}>{r}</option>)}
        </select>
      </motion.div>

      {/* Table card */}
      <motion.div variants={staggerItem}>
        <Card padding="none">
          {/* Table header */}
          <div className="hidden sm:grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_1fr_auto] gap-4 px-5 py-3 border-b border-[var(--color-border-subtle)] text-xs font-semibold text-[var(--color-muted)] uppercase tracking-wide">
            <span>Patient</span>
            <span>Disease</span>
            <span>Day</span>
            <span>Risk</span>
            <span>Recovery</span>
            <span>Readmission</span>
            <span />
          </div>

          {isLoading
            ? Array.from({ length: 8 }).map((_, i) => (
                <SkeletonTableRow key={i} columns={7} />
              ))
            : filtered.length === 0
            ? <EmptyState
                title="No patients found"
                description="Try adjusting your search or filters."
                size="sm"
                className="py-12"
              />
            : filtered.slice((page - 1) * 20, page * 20).map((p) => (
                <PatientRow key={p.id} patient={p} />
              ))
          }

          {/* Pagination */}
          {filtered.length > 20 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-[var(--color-border-subtle)]">
              <p className="text-xs text-[var(--color-muted)]">
                Page {page} of {Math.ceil(filtered.length / 20)}
              </p>
              <div className="flex gap-2">
                <Button size="xs" variant="secondary" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
                <Button size="xs" variant="secondary" disabled={page >= Math.ceil(filtered.length / 20)} onClick={() => setPage(p => p + 1)}>Next</Button>
              </div>
            </div>
          )}
        </Card>
      </motion.div>
    </motion.div>
  );
}

function PatientRow({ patient: p }: { patient: typeof MOCK_PATIENTS[0] }) {
  const isHighRisk = p.readmission > 70;
  return (
    <div className={`grid grid-cols-[auto_1fr] sm:grid-cols-[2fr_1.5fr_1fr_1fr_1fr_1fr_auto] gap-4 items-center px-5 py-3.5 border-b border-[var(--color-border-subtle)] last:border-0 hover:bg-[var(--color-border-subtle)]/50 transition-colors ${isHighRisk ? "bg-[var(--color-danger-50)]/30" : ""}`}>
      {/* Patient info */}
      <div className="flex items-center gap-3 min-w-0">
        <Avatar name={p.id} size="sm" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-[var(--color-foreground)] truncate">{p.id}</p>
          <p className="text-xs text-[var(--color-muted)]">{p.age}y · {p.gender}</p>
        </div>
        {isHighRisk && <span className="hidden sm:inline w-2 h-2 rounded-full bg-[var(--color-danger-500)] shrink-0" />}
      </div>
      <div className="hidden sm:block">
        <Badge variant="default" size="sm">{p.disease}</Badge>
      </div>
      <span className="hidden sm:block text-sm text-[var(--color-muted)] tabular-nums">Day {p.day}</span>
      <div className="hidden sm:block"><RiskBadge level={p.risk as RiskLevel} size="sm" /></div>
      <div className="hidden sm:block"><RecoveryBadge status={p.recovery as RecoveryStatus} size="sm" /></div>
      <div className="hidden sm:block text-right">
        <span className={`text-sm font-bold tabular-nums ${p.readmission > 70 ? "text-[var(--color-danger-500)]" : p.readmission > 50 ? "text-[var(--color-warning-600)]" : "text-[var(--color-success-600)]"}`}>
          {p.readmission}%
        </span>
      </div>
      <Link to="/patients/$patientId" params={{ patientId: p.id }}>
        <Button variant="ghost" size="icon-sm" aria-label="View patient">
          <ChevronRight size={14} />
        </Button>
      </Link>
    </div>
  );
}

/* ── Mock data ─────────────────────────────────────────────────────────── */
const MOCK_PATIENTS = [
  { id: "HDT-AHD-2026-501118", age: 53, gender: "Male", disease: "Asthma", day: 30, risk: "High", recovery: "Delayed Recovery", readmission: 44.3, compliance: 64.5 },
  { id: "HDT-LCC-2026-450186", age: 60, gender: "Male", disease: "Cardiac", day: 30, risk: "Medium", recovery: "Worsening", readmission: 59.7, compliance: 39.0 },
  { id: "HDT-KMC-2026-356698", age: 87, gender: "Male", disease: "Kidney Disease", day: 14, risk: "High", recovery: "Delayed Recovery", readmission: 68.7, compliance: 82.5 },
  { id: "HDT-SGH-2026-749915", age: 42, gender: "Female", disease: "Diabetes", day: 22, risk: "High", recovery: "Critical", readmission: 71.2, compliance: 55.3 },
  { id: "HDT-NHP-2026-782008", age: 65, gender: "Male", disease: "COPD", day: 18, risk: "Medium", recovery: "Stable", readmission: 48.6, compliance: 73.1 },
  { id: "HDT-MCH-2026-839682", age: 55, gender: "Female", disease: "Hypertension", day: 25, risk: "Low", recovery: "Improving", readmission: 22.4, compliance: 88.2 },
  { id: "HDT-SGH-2026-996501", age: 71, gender: "Male", disease: "Stroke Recovery", day: 30, risk: "High", recovery: "Worsening", readmission: 78.5, compliance: 41.7 },
  { id: "HDT-AHD-2026-404857", age: 49, gender: "Female", disease: "Post Surgery", day: 12, risk: "Medium", recovery: "Improving", readmission: 35.1, compliance: 79.6 },
  { id: "HDT-KMC-2026-853458", age: 33, gender: "Male", disease: "Asthma", day: 8, risk: "Low", recovery: "Recovered", readmission: 12.3, compliance: 94.1 },
  { id: "HDT-NHP-2026-693424", age: 78, gender: "Female", disease: "Cardiac", day: 28, risk: "High", recovery: "Critical", readmission: 82.9, compliance: 38.4 },
  { id: "HDT-LCC-2026-724412", age: 61, gender: "Male", disease: "Diabetes", day: 15, risk: "Medium", recovery: "Delayed Recovery", readmission: 51.7, compliance: 66.8 },
  { id: "HDT-SGH-2026-632802", age: 44, gender: "Female", disease: "Kidney Disease", day: 20, risk: "Medium", recovery: "Stable", readmission: 43.2, compliance: 71.5 },
];
