import React from "react";
import { motion, type HTMLMotionProps } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { floatIn } from "@/lib/motion";

export interface FloatingPanelProps extends Omit<HTMLMotionProps<"div">, "children"> {
  title?: string; description?: string; onClose?: () => void;
  actions?: React.ReactNode; headerClassName?: string; bodyClassName?: string; noPadding?: boolean;
  children?: React.ReactNode;
}

export function FloatingPanel({ title, description, onClose, actions, headerClassName, bodyClassName, noPadding, children, className, ...motionProps }: FloatingPanelProps) {
  return (
    <motion.div
      variants={floatIn} initial="hidden" animate="visible" exit="exit"
      className={cn(
        "relative rounded-2xl overflow-hidden",
        "bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl",
        "border border-white/60 dark:border-gray-700/60",
        "shadow-panel",
        className
      )}
      {...motionProps}
    >
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/80 to-transparent pointer-events-none" aria-hidden />
      {(title || onClose || actions) && (
        <div className={cn("flex items-start justify-between gap-4 px-5 pt-5", !noPadding && "pb-1", headerClassName)}>
          <div className="min-w-0">
            {title && <h3 className="text-base font-semibold text-gray-900 dark:text-white leading-tight">{title}</h3>}
            {description && <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">{description}</p>}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {actions}
            {onClose && (
              <button onClick={onClose} className="flex items-center justify-center w-7 h-7 rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" aria-label="Close panel">
                <X size={15} />
              </button>
            )}
          </div>
        </div>
      )}
      <div className={cn(!noPadding && "px-5 pb-5 pt-4", bodyClassName)}>{children}</div>
    </motion.div>
  );
}
