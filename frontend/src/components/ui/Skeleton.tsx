import React from "react";
import { cn } from "@/lib/utils";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  rounded?: "none" | "sm" | "md" | "lg" | "xl" | "full";
}

const ROUNDED = { none: "", sm: "rounded-sm", md: "rounded-md", lg: "rounded-lg", xl: "rounded-xl", full: "rounded-full" };

export function Skeleton({ className, rounded = "lg", ...props }: SkeletonProps) {
  return (
    <div
      className={cn("relative overflow-hidden bg-gray-100 dark:bg-gray-800", "before:absolute before:inset-0 before:bg-gradient-to-r before:from-transparent before:via-white/60 dark:before:via-white/10 before:to-transparent before:animate-shimmer", ROUNDED[rounded], className)}
      aria-hidden="true" {...props}
    />
  );
}

export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} className="h-3.5" style={{ width: i === lines - 1 ? "65%" : "100%" }} />
      ))}
    </div>
  );
}

export function SkeletonKPICard({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5", className)}>
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-7 w-28" />
          <Skeleton className="h-3 w-16" />
        </div>
        <Skeleton className="w-10 h-10 rounded-xl" rounded="none" />
      </div>
    </div>
  );
}

export function SkeletonTableRow({ columns = 5, className }: { columns?: number; className?: string }) {
  return (
    <div className={cn("flex items-center gap-4 px-5 py-3.5", className)}>
      <Skeleton className="w-8 h-8" rounded="full" />
      {Array.from({ length: columns - 1 }).map((_, i) => (
        <Skeleton key={i} className="h-3 flex-1" style={{ maxWidth: `${80 + (i % 3) * 15}px` }} />
      ))}
    </div>
  );
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn("rounded-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-5", className)}>
      <div className="flex items-center gap-3 mb-4">
        <Skeleton className="w-10 h-10" rounded="full" />
        <div className="flex-1 space-y-1.5">
          <Skeleton className="h-3.5 w-32" />
          <Skeleton className="h-3 w-20" />
        </div>
      </div>
      <SkeletonText lines={3} />
    </div>
  );
}
