import React from "react";
import { cn } from "@/lib/utils";
import type { RiskLevel, RecoveryStatus } from "@/types";

type HealthTrend = "Increasing" | "Stable" | "Declining";

const RISK_STYLES: Record<RiskLevel, string> = {
  Low:      "bg-success-50 dark:bg-green-900/30 text-success-700 dark:text-green-400",
  Medium:   "bg-warning-50 dark:bg-yellow-900/30 text-warning-600 dark:text-yellow-400",
  High:     "bg-danger-50 dark:bg-red-900/30 text-danger-600 dark:text-red-400",
  Critical: "bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400",
};
const RISK_DOT: Record<RiskLevel, string> = {
  Low: "bg-success-500", Medium: "bg-warning-500", High: "bg-danger-500", Critical: "bg-purple-500",
};

export function RiskBadge({ level, size = "md", className }: { level: RiskLevel; size?: "sm" | "md"; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full font-medium", RISK_STYLES[level], size === "sm" ? "text-[10px] px-2 py-0.5" : "text-xs px-2.5 py-1", className)}>
      <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", RISK_DOT[level])} aria-hidden />
      {level}
    </span>
  );
}

const RECOVERY_STYLES: Record<RecoveryStatus, string> = {
  Recovered:          "bg-success-50 dark:bg-green-900/30 text-success-700 dark:text-green-400",
  Improving:          "bg-primary-50 dark:bg-blue-900/30 text-primary-700 dark:text-blue-400",
  Stable:             "bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400",
  "Delayed Recovery": "bg-warning-50 dark:bg-yellow-900/30 text-warning-600 dark:text-yellow-400",
  Worsening:          "bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400",
  Critical:           "bg-danger-50 dark:bg-red-900/30 text-danger-600 dark:text-red-400",
};
const RECOVERY_DOT: Record<RecoveryStatus, string> = {
  Recovered: "bg-success-500", Improving: "bg-primary-500", Stable: "bg-indigo-500",
  "Delayed Recovery": "bg-warning-500", Worsening: "bg-orange-500", Critical: "bg-danger-500",
};

export function RecoveryBadge({ status, size = "md", className }: { status: RecoveryStatus; size?: "sm" | "md"; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full font-medium", RECOVERY_STYLES[status], size === "sm" ? "text-[10px] px-2 py-0.5" : "text-xs px-2.5 py-1", className)}>
      <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", RECOVERY_DOT[status])} aria-hidden />
      {status}
    </span>
  );
}

const TREND_STYLES: Record<HealthTrend, string> = {
  Increasing: "bg-success-50 dark:bg-green-900/30 text-success-700 dark:text-green-400",
  Stable:     "bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400",
  Declining:  "bg-danger-50 dark:bg-red-900/30 text-danger-600 dark:text-red-400",
};
const TREND_SYMBOL: Record<HealthTrend, string> = { Increasing: "↑", Stable: "→", Declining: "↓" };

export function TrendBadge({ trend, size = "md", className }: { trend: HealthTrend; size?: "sm" | "md"; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full font-medium", TREND_STYLES[trend], size === "sm" ? "text-[10px] px-2 py-0.5" : "text-xs px-2.5 py-1", className)}>
      <span aria-hidden>{TREND_SYMBOL[trend]}</span>
      {trend}
    </span>
  );
}
