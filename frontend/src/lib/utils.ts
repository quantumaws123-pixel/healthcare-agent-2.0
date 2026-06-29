import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes safely, resolving conflicts. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a number as a percentage string. */
export function formatPercent(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

/** Format a large number with K/M suffixes. */
export function formatCompact(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toString();
}

/** Clamp a number between min and max. */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/** Map a risk level string to a semantic colour token key. */
export type RiskLevel = "Low" | "Medium" | "High" | "Critical";
export type RecoveryStatus =
  | "Recovered"
  | "Improving"
  | "Stable"
  | "Delayed Recovery"
  | "Worsening"
  | "Critical";

export const RISK_COLOR: Record<RiskLevel, string> = {
  Low: "text-success-600 bg-success-50",
  Medium: "text-warning-600 bg-warning-50",
  High: "text-danger-600 bg-danger-50",
  Critical: "text-purple-700 bg-purple-50",
};

export const RISK_DOT: Record<RiskLevel, string> = {
  Low: "bg-success-500",
  Medium: "bg-warning-500",
  High: "bg-danger-500",
  Critical: "bg-purple-600",
};

export const RECOVERY_COLOR: Record<RecoveryStatus, string> = {
  Recovered: "text-success-600 bg-success-50",
  Improving: "text-primary-600 bg-primary-50",
  Stable: "text-indigo-600 bg-indigo-50",
  "Delayed Recovery": "text-warning-600 bg-warning-50",
  Worsening: "text-orange-600 bg-orange-50",
  Critical: "text-danger-600 bg-danger-50",
};

/** Sleep a given number of milliseconds (for animations). */
export const sleep = (ms: number) =>
  new Promise<void>((resolve) => setTimeout(resolve, ms));

/** Generate initials from a full name string. */
export function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0]?.toUpperCase() ?? "")
    .join("");
}

/** Format a date string to a readable label. */
export function formatDate(dateStr: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(dateStr));
}
