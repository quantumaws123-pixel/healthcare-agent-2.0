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
import type { RiskLevel, RecoveryStatus, DiseaseType, PatientSummary } from "@/types";
import { usePatients } from "@/hooks/usePatients";

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

  const { data: patientsData, isLoading, refetch } = usePatients({
    page,
    page_size: 10,
    disease_type: diseaseFilter === "All" ? undefined : diseaseFilter,
    risk_level: riskFilter === "All" ? undefined : riskFilter,
  });

  const patients = patientsData?.data ?? [];
  const filtered = patients.filter((p) => {
    return !search || p.Patient_ID.toLowerCase().includes(search.toLowerCase());
  });

  const totalPages = patientsData?.total_pages ?? 1;
  const totalCount = patientsData?.total ?? 0;

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
            {totalCount} patients · Post-discharge monitoring
          </p>
        </div>
        <Button leftIcon={<RefreshCw size={14} />} variant="secondary" size="sm" onClick={() => refetch()}>
          Refresh
        </Button>
      </motion.div>

      {/* Filters */}
      <motion.div variants={staggerItem} className="flex flex-wrap gap-3 items-center">
        <div className="w-64">
          <SearchBar
            placeholder="Search patient ID…"
            value={search}
            onChange={(val) => { setSearch(val); setPage(1); }}
          />
        </div>
        <select
          value={diseaseFilter}
          onChange={(e) => { setDiseaseFilter(e.target.value); setPage(1); }}
          className="h-9 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm text-[var(--color-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-400)]"
        >
          <option value="All">All Diseases</option>
          {DISEASE_TYPES.map((d) => <option key={d}>{d}</option>)}
        </select>
        <select
          value={riskFilter}
          onChange={(e) => { setRiskFilter(e.target.value); setPage(1); }}
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
            : filtered.map((p) => (
                <PatientRow key={p.Patient_ID} patient={p} />
              ))
          }

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-[var(--color-border-subtle)]">
              <p className="text-xs text-[var(--color-muted)]">
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <Button size="xs" variant="secondary" disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
                <Button size="xs" variant="secondary" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</Button>
              </div>
            </div>
          )}
        </Card>
      </motion.div>
    </motion.div>
  );
}

function PatientRow({ patient: p }: { patient: PatientSummary }) {
  const readmissionPct = Math.round(p.Readmission_Probability * 100);
  const isHighRisk = readmissionPct > 70;
  return (
    <div className={`grid grid-cols-[auto_1fr] sm:grid-cols-[2fr_1.5fr_1fr_1fr_1fr_1fr_auto] gap-4 items-center px-5 py-3.5 border-b border-[var(--color-border-subtle)] last:border-0 hover:bg-[var(--color-border-subtle)]/50 transition-colors ${isHighRisk ? "bg-[var(--color-danger-50)]/30" : ""}`}>
      {/* Patient info */}
      <div className="flex items-center gap-3 min-w-0">
        <Avatar name={p.Patient_ID} size="sm" />
        <div className="min-w-0">
          <p className="text-sm font-medium text-[var(--color-foreground)] truncate">{p.Patient_ID}</p>
          <p className="text-xs text-[var(--color-muted)]">{p.Age}y · {p.Gender}</p>
        </div>
        {isHighRisk && <span className="hidden sm:inline w-2 h-2 rounded-full bg-[var(--color-danger-500)] shrink-0" />}
      </div>
      <div className="hidden sm:block">
        <Badge variant="default" size="sm">{p.Disease_Type}</Badge>
      </div>
      <span className="hidden sm:block text-sm text-[var(--color-muted)] tabular-nums">Day {p.Latest_Day}</span>
      <div className="hidden sm:block"><RiskBadge level={p.Risk_Level as RiskLevel} size="sm" /></div>
      <div className="hidden sm:block"><RecoveryBadge status={p.Recovery_Status as RecoveryStatus} size="sm" /></div>
      <div className="hidden sm:block text-right">
        <span className={`text-sm font-bold tabular-nums ${readmissionPct > 70 ? "text-[var(--color-danger-500)]" : readmissionPct > 50 ? "text-[var(--color-warning-600)]" : "text-[var(--color-success-600)]"}`}>
          {readmissionPct}%
        </span>
      </div>
      <Link to="/patients/$patientId" params={{ patientId: p.Patient_ID }}>
        <Button variant="ghost" size="icon-sm" aria-label="View patient">
          <ChevronRight size={14} />
        </Button>
      </Link>
    </div>
  );
}
