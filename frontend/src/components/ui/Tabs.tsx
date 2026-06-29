import React, { createContext, useContext, useId } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (id: string) => void;
  variant: "line" | "pill" | "card";
  baseId: string;
}

const TabsContext = createContext<TabsContextValue | null>(null);
function useTabsContext() {
  const ctx = useContext(TabsContext);
  if (!ctx) throw new Error("Tab components must be inside <Tabs>");
  return ctx;
}

export interface TabsProps {
  defaultTab?: string;
  activeTab?: string;
  onTabChange?: (id: string) => void;
  variant?: "line" | "pill" | "card";
  children: React.ReactNode;
  className?: string;
}

export function Tabs({ defaultTab, activeTab: controlledTab, onTabChange, variant = "line", children, className }: TabsProps) {
  const baseId = useId();
  const [internalTab, setInternalTab] = React.useState(defaultTab ?? "");
  const activeTab = controlledTab ?? internalTab;
  const setActiveTab = (id: string) => { setInternalTab(id); onTabChange?.(id); };
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab, variant, baseId }}>
      <div className={cn("w-full", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabList({ children, className }: { children: React.ReactNode; className?: string }) {
  const { variant } = useTabsContext();
  return (
    <div role="tablist" className={cn("flex items-center gap-1",
      variant === "line" && "border-b border-gray-200 dark:border-gray-800",
      variant === "pill" && "bg-gray-100 dark:bg-gray-800 rounded-xl p-1",
      variant === "card" && "gap-2",
      className)}>
      {children}
    </div>
  );
}

export interface TabTriggerProps {
  id: string; children: React.ReactNode; icon?: React.ReactNode;
  badge?: string | number; disabled?: boolean; className?: string;
}

export function TabTrigger({ id, children, icon, badge, disabled, className }: TabTriggerProps) {
  const { activeTab, setActiveTab, variant, baseId } = useTabsContext();
  const isActive = activeTab === id;
  return (
    <button
      role="tab"
      id={`${baseId}-tab-${id}`}
      aria-controls={`${baseId}-panel-${id}`}
      aria-selected={isActive}
      disabled={disabled}
      onClick={() => setActiveTab(id)}
      className={cn(
        "relative flex items-center gap-2 font-medium text-sm transition-colors duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:rounded-lg",
        "disabled:opacity-40 disabled:pointer-events-none",
        variant === "line" && [
          "px-3 pb-3 pt-1",
          isActive ? "text-gray-900 dark:text-white" : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white",
        ],
        variant === "pill" && [
          "px-4 py-1.5 rounded-lg",
          isActive ? "text-gray-900 dark:text-white bg-white dark:bg-gray-900 shadow-sm" : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white",
        ],
        variant === "card" && [
          "px-4 py-2 rounded-xl border",
          isActive ? "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 shadow-sm text-gray-900 dark:text-white" : "bg-transparent border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white",
        ],
        className
      )}
    >
      {icon && <span className="shrink-0" aria-hidden>{icon}</span>}
      {children}
      {badge != null && (
        <span className="ml-0.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[9px] font-bold bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300">
          {badge}
        </span>
      )}
      {variant === "line" && isActive && (
        <motion.span
          layoutId="tab-line-indicator"
          className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-primary-500"
          transition={{ type: "spring", stiffness: 500, damping: 35 }}
        />
      )}
    </button>
  );
}

export function TabPanels({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("mt-4", className)}>{children}</div>;
}

export interface TabPanelProps { id: string; children: React.ReactNode; className?: string; }

export function TabPanel({ id, children, className }: TabPanelProps) {
  const { activeTab, baseId } = useTabsContext();
  const isActive = activeTab === id;
  return (
    <AnimatePresence mode="wait" initial={false}>
      {isActive && (
        <motion.div
          key={id}
          role="tabpanel"
          id={`${baseId}-panel-${id}`}
          aria-labelledby={`${baseId}-tab-${id}`}
          initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
          className={cn("outline-none", className)}
          tabIndex={0}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
