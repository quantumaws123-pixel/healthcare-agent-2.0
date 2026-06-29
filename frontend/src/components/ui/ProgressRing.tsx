import React, { useEffect, useRef } from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { cn } from "@/lib/utils";

export interface ProgressRingProps {
  value: number; size?: number; strokeWidth?: number; color?: string;
  trackColor?: string; showLabel?: boolean; label?: React.ReactNode;
  className?: string; animationDuration?: number;
}

export function ProgressRing({ value, size = 80, strokeWidth = 7, color = "#3b82f6", trackColor = "#f3f4f6", showLabel = true, label, className, animationDuration = 1.2 }: ProgressRingProps) {
  const clampedValue = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const motionValue = useMotionValue(0);
  const strokeDashoffset = useTransform(motionValue, v => circumference - (v / 100) * circumference);

  useEffect(() => {
    const controls = animate(motionValue, clampedValue, { duration: animationDuration, ease: [0.16, 1, 0.3, 1] });
    return controls.stop;
  }, [clampedValue, motionValue, animationDuration]);

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)} style={{ width: size, height: size }}
      role="progressbar" aria-valuenow={clampedValue} aria-valuemin={0} aria-valuemax={100}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90" aria-hidden>
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={trackColor} strokeWidth={strokeWidth} />
        <motion.circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" strokeDasharray={circumference} style={{ strokeDashoffset }} />
      </svg>
      {showLabel && (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {label ?? <CountUp value={clampedValue} className="text-sm font-bold text-gray-900 dark:text-white tabular-nums" />}
        </div>
      )}
    </div>
  );
}

function CountUp({ value, className }: { value: number; className?: string }) {
  const motionValue = useMotionValue(0);
  const rounded = useTransform(motionValue, v => Math.round(v));
  const displayRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const controls = animate(motionValue, value, { duration: 1.2, ease: [0.16, 1, 0.3, 1] });
    const unsubscribe = rounded.on("change", v => { if (displayRef.current) displayRef.current.textContent = `${v}%`; });
    return () => { controls.stop(); unsubscribe(); };
  }, [value, motionValue, rounded]);

  return <span ref={displayRef} className={className}>0%</span>;
}
