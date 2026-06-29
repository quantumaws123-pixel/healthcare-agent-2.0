import React from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card } from "./Card";
import { staggerItem } from "@/lib/motion";

export interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: number;
  trendLabel?: string;
  icon?: React.ReactNode;
  iconColor?: string;
  description?: string;
  className?: string;
  loading?: boolean;
  invertTrend?: boolean;
}

export function KPICard({ title, value, unit, trend, trendLabel, icon, iconColor = "bg-primary-50 dark:bg-primary-900/30", description, className, loading, invertTrend = false }: KPICardProps) {
  const trendPositive = trend != null ? (invertTrend ? trend < 0 : trend > 0) : null;
  const trendNeutral = trend === 0;
  const TrendIcon = trendNeutral ? Minus : trendPositive ? TrendingUp : TrendingDown;
  const trendColor = trendNeutral ? "text-gray-400" : trendPositive ? "text-success-600 dark:text-green-400" : "text-danger-500 dark:text-red-400";

  if (loading) {
    return (
      <Card className={cn("animate-pulse", className)}>
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="h-3.5 w-24 rounded-full bg-gray-200 dark:bg-gray-700" />
            <div className="h-8 w-32 rounded-xl bg-gray-200 dark:bg-gray-700" />
            <div className="h-3 w-20 rounded-full bg-gray-200 dark:bg-gray-700" />
          </div>
          <div className="w-10 h-10 rounded-xl bg-gray-200 dark:bg-gray-700" />
        </div>
      </Card>
    );
  }

  return (
    <motion.div variants={staggerItem}>
      <Card className={cn("group hover:shadow-float hover:-translate-y-0.5 transition-all duration-200", className)}>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide truncate">{title}</p>
            <div className="mt-2 flex items-baseline gap-1">
              <motion.span className="text-2xl font-bold text-gray-900 dark:text-white tabular-nums"
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}>
                {value}
              </motion.span>
              {unit && <span className="text-sm text-gray-500 dark:text-gray-400 font-medium">{unit}</span>}
            </div>
            {trend != null && (
              <div className={cn("mt-2 flex items-center gap-1", trendColor)}>
                <TrendIcon size={13} strokeWidth={2.5} aria-hidden />
                <span className="text-xs font-semibold tabular-nums">{Math.abs(trend).toFixed(1)}%</span>
                {trendLabel && <span className="text-xs text-gray-400 font-normal">{trendLabel}</span>}
              </div>
            )}
            {description && <p className="mt-1.5 text-xs text-gray-500">{description}</p>}
          </div>
          {icon && (
            <div className={cn("flex items-center justify-center w-10 h-10 rounded-xl shrink-0 transition-transform duration-200 group-hover:scale-110", iconColor)}>
              {icon}
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  );
}
