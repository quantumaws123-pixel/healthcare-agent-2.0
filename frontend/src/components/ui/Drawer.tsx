import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { overlayBackdrop } from "@/lib/motion";

export interface DrawerProps {
  open: boolean; onClose: () => void; title?: string; description?: string;
  children: React.ReactNode; footer?: React.ReactNode;
  side?: "right" | "left" | "bottom"; size?: "sm" | "md" | "lg" | "xl"; className?: string;
}

const SIDE_CLASSES = { right: "right-0 top-0 bottom-0", left: "left-0 top-0 bottom-0", bottom: "bottom-0 left-0 right-0" };
const SIDE_INITIAL = { right: { x: "100%" }, left: { x: "-100%" }, bottom: { y: "100%" } };
const SIDE_ANIMATE = { right: { x: 0 }, left: { x: 0 }, bottom: { y: 0 } };
const WIDTH_CLASSES = { sm: "w-80", md: "w-96", lg: "w-[480px]", xl: "w-[600px]" };

export function Drawer({ open, onClose, title, description, children, footer, side = "right", size = "md", className }: DrawerProps) {
  useEffect(() => { document.body.style.overflow = open ? "hidden" : ""; return () => { document.body.style.overflow = ""; }; }, [open]);
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape" && open) onClose(); };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  }, [open, onClose]);

  const isBottom = side === "bottom";

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[1300]" role="dialog" aria-modal="true">
          <motion.div variants={overlayBackdrop} initial="hidden" animate="visible" exit="exit"
            className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
          <motion.div
            initial={SIDE_INITIAL[side]} animate={SIDE_ANIMATE[side]} exit={SIDE_INITIAL[side]}
            transition={{ type: "spring", stiffness: 380, damping: 38, mass: 0.9 }}
            className={cn(
              "absolute z-10 flex flex-col bg-white dark:bg-gray-900 shadow-2xl",
              SIDE_CLASSES[side],
              !isBottom && ["border-l border-gray-200 dark:border-gray-800", WIDTH_CLASSES[size]],
              isBottom && "rounded-t-2xl max-h-[85dvh]",
              className
            )}
          >
            {isBottom && <div className="flex justify-center pt-3 pb-1 shrink-0"><div className="w-8 h-1 rounded-full bg-gray-300 dark:bg-gray-700" /></div>}
            {(title || description) && (
              <div className="flex items-start justify-between gap-4 px-6 py-5 border-b border-gray-100 dark:border-gray-800 shrink-0">
                <div>
                  {title && <h2 className="text-base font-semibold text-gray-900 dark:text-white leading-tight">{title}</h2>}
                  {description && <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">{description}</p>}
                </div>
                <button onClick={onClose} className="flex items-center justify-center w-8 h-8 rounded-xl shrink-0 text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" aria-label="Close">
                  <X size={16} />
                </button>
              </div>
            )}
            <div className="flex-1 overflow-y-auto px-6 py-5">{children}</div>
            {footer && <div className="shrink-0 px-6 py-4 border-t border-gray-100 dark:border-gray-800 flex items-center justify-end gap-3">{footer}</div>}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
