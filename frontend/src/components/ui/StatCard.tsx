import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card } from "./Card";
import { staggerItem } from "@/lib/motion";

export interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    direction: "up" | "down";
  };
  color?: "blue" | "green" | "red" | "purple" | "amber" | "rose";
  className?: string;
}

const COLOR_MAP = {
  blue: {
    bg: "bg-blue-50 dark:bg-blue-950/30",
    text: "text-blue-600 dark:text-blue-400",
  },
  green: {
    bg: "bg-green-50 dark:bg-green-950/30",
    text: "text-green-600 dark:text-green-400",
  },
  red: {
    bg: "bg-red-50 dark:bg-red-950/30",
    text: "text-red-600 dark:text-red-400",
  },
  purple: {
    bg: "bg-purple-50 dark:bg-purple-950/30",
    text: "text-purple-600 dark:text-purple-400",
  },
  amber: {
    bg: "bg-amber-50 dark:bg-amber-950/30",
    text: "text-amber-600 dark:text-amber-400",
  },
  rose: {
    bg: "bg-rose-50 dark:bg-rose-950/30",
    text: "text-rose-600 dark:text-rose-400",
  },
};

export function StatCard({
  label,
  value,
  icon: Icon,
  trend,
  color = "blue",
  className,
}: StatCardProps) {
  const colorStyle = COLOR_MAP[color] || COLOR_MAP.blue;
  const TrendIcon = trend?.direction === "up" ? TrendingUp : TrendingDown;
  const trendColor = trend?.direction === "up" ? "text-success-600 dark:text-green-400" : "text-danger-500 dark:text-red-400";

  return (
    <motion.div variants={staggerItem} className="w-full">
      <Card className={cn("group hover:shadow-float hover:-translate-y-0.5 transition-all duration-200", className)}>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide truncate">
              {label}
            </p>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="text-2xl font-bold text-gray-900 dark:text-white tabular-nums">
                {value}
              </span>
            </div>
            {trend && (
              <div className={cn("mt-2 flex items-center gap-1", trendColor)}>
                <TrendIcon size={13} strokeWidth={2.5} />
                <span className="text-xs font-semibold tabular-nums">
                  {trend.value}%
                </span>
                <span className="text-xs text-gray-400 font-normal">vs last month</span>
              </div>
            )}
          </div>
          <div className={cn("flex items-center justify-center w-10 h-10 rounded-xl shrink-0 transition-transform duration-200 group-hover:scale-110", colorStyle.bg, colorStyle.text)}>
            <Icon size={20} />
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
