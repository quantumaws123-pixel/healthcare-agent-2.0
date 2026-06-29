import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { fadeInUp } from "@/lib/motion";
import { Button } from "./Button";

export interface EmptyStateProps {
  icon?: React.ReactNode; title: string; description?: string;
  action?: { label: string; onClick: () => void };
  secondaryAction?: { label: string; onClick: () => void };
  className?: string; size?: "sm" | "md" | "lg";
}

const SIZE = {
  sm: { wrapper: "py-8",  iconWrapper: "w-10 h-10", title: "text-sm",  desc: "text-xs" },
  md: { wrapper: "py-12", iconWrapper: "w-14 h-14", title: "text-base", desc: "text-sm" },
  lg: { wrapper: "py-16", iconWrapper: "w-16 h-16", title: "text-lg",  desc: "text-sm" },
};

export function EmptyState({ icon, title, description, action, secondaryAction, className, size = "md" }: EmptyStateProps) {
  const s = SIZE[size];
  return (
    <motion.div variants={fadeInUp} initial="hidden" animate="visible"
      className={cn("flex flex-col items-center justify-center text-center", s.wrapper, className)}>
      {icon && (
        <div className={cn("flex items-center justify-center rounded-2xl mb-4 bg-gray-100 dark:bg-gray-800 text-gray-400", s.iconWrapper)}>
          {icon}
        </div>
      )}
      <h3 className={cn("font-semibold text-gray-900 dark:text-white", s.title)}>{title}</h3>
      {description && <p className={cn("mt-1.5 text-gray-500 dark:text-gray-400 max-w-xs", s.desc)}>{description}</p>}
      {(action || secondaryAction) && (
        <div className="mt-5 flex items-center gap-3">
          {action && <Button size="sm" onClick={action.onClick}>{action.label}</Button>}
          {secondaryAction && <Button size="sm" variant="secondary" onClick={secondaryAction.onClick}>{secondaryAction.label}</Button>}
        </div>
      )}
    </motion.div>
  );
}
