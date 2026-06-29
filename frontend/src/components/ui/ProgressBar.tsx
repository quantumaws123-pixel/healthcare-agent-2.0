import React, { useEffect } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { cn } from "@/lib/utils";

export interface ProgressBarProps {
  value: number; max?: number; label?: string; showValue?: boolean;
  size?: "xs" | "sm" | "md" | "lg"; color?: string; trackClassName?: string;
  className?: string; animated?: boolean;
}

const SIZE_CLASSES = { xs: "h-1", sm: "h-1.5", md: "h-2", lg: "h-3" };

export function ProgressBar({ value, max = 100, label, showValue = false, size = "md", color, trackClassName, className, animated = true }: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const motionValue = useMotionValue(0);
  const width = useTransform(motionValue, v => `${v}%`);

  useEffect(() => {
    if (!animated) { motionValue.set(percentage); return; }
    const controls = animate(motionValue, percentage, { duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 0.05 });
    return controls.stop;
  }, [percentage, motionValue, animated]);

  return (
    <div className={cn("w-full", className)}>
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && <span className="text-xs font-medium text-gray-500 dark:text-gray-400">{label}</span>}
          {showValue && <span className="text-xs font-semibold text-gray-900 dark:text-white tabular-nums">{Math.round(percentage)}%</span>}
        </div>
      )}
      <div className={cn("w-full rounded-full overflow-hidden", SIZE_CLASSES[size], trackClassName ?? "bg-gray-100 dark:bg-gray-800")}
        role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={max}>
        <motion.div className="h-full rounded-full" style={{ width, backgroundColor: color ?? "#3b82f6" }} />
      </div>
    </div>
  );
}
