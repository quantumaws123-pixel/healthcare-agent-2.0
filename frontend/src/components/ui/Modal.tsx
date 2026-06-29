import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { overlayBackdrop, fadeInScale } from "@/lib/motion";

export interface ModalProps {
  open: boolean; onClose: () => void; title?: string; description?: string;
  children: React.ReactNode; footer?: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl" | "full"; closeOnBackdrop?: boolean; className?: string;
}

const SIZE_CLASSES = { sm: "max-w-sm", md: "max-w-md", lg: "max-w-lg", xl: "max-w-2xl", full: "max-w-5xl" };

export function Modal({ open, onClose, title, description, children, footer, size = "md", closeOnBackdrop = true, className }: ModalProps) {
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape" && open) onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[1300] flex items-center justify-center p-4" role="dialog" aria-modal="true">
          <motion.div variants={overlayBackdrop} initial="hidden" animate="visible" exit="exit"
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={closeOnBackdrop ? onClose : undefined} />
          <motion.div variants={fadeInScale} initial="hidden" animate="visible" exit="exit"
            className={cn(
              "relative w-full z-10 bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-2xl overflow-hidden",
              SIZE_CLASSES[size], className
            )}>
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/80 to-transparent pointer-events-none" aria-hidden />
            {(title || description) && (
              <div className="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-gray-100 dark:border-gray-800">
                <div>
                  {title && <h2 className="text-lg font-semibold text-gray-900 dark:text-white leading-tight">{title}</h2>}
                  {description && <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>}
                </div>
                <button onClick={onClose} className="flex items-center justify-center w-8 h-8 rounded-xl shrink-0 text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" aria-label="Close">
                  <X size={16} />
                </button>
              </div>
            )}
            <div className="px-6 py-5 overflow-y-auto max-h-[70dvh]">{children}</div>
            {footer && (
              <div className="px-6 py-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-end gap-3 bg-gray-50/50 dark:bg-gray-800/50">
                {footer}
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
