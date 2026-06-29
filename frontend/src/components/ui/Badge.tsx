import React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center gap-1.5 rounded-full font-medium transition-colors", {
  variants: {
    variant: {
      default:  "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300",
      primary:  "bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400",
      success:  "bg-success-50 dark:bg-green-900/30 text-success-700 dark:text-green-400",
      warning:  "bg-warning-50 dark:bg-yellow-900/30 text-warning-600 dark:text-yellow-400",
      danger:   "bg-danger-50 dark:bg-red-900/30 text-danger-600 dark:text-red-400",
      info:     "bg-info-50 dark:bg-blue-900/30 text-info-600 dark:text-blue-400",
      purple:   "bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400",
      outline:  "border border-gray-200 dark:border-gray-700 text-gray-500",
    },
    size: { sm: "text-[10px] px-2 py-0.5", md: "text-xs px-2.5 py-1", lg: "text-sm px-3 py-1" },
  },
  defaultVariants: { variant: "default", size: "md" },
});

const DOT_COLORS: Record<string, string> = {
  default: "bg-gray-500", primary: "bg-primary-500", success: "bg-success-500",
  warning: "bg-warning-500", danger: "bg-danger-500", info: "bg-info-500",
  purple: "bg-purple-500", outline: "bg-gray-400",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {
  dot?: boolean;
}

export function Badge({ className, variant = "default", size, dot, children, ...props }: BadgeProps) {
  return (
    <span className={cn(badgeVariants({ variant, size, className }))} {...props}>
      {dot && <span className={cn("inline-block w-1.5 h-1.5 rounded-full shrink-0", DOT_COLORS[variant ?? "default"])} aria-hidden />}
      {children}
    </span>
  );
}
