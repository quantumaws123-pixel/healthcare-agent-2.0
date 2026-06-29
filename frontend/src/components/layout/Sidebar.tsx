import React from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity, LayoutDashboard, Users, AlertTriangle,
  FlaskConical, BarChart3, Settings, ChevronLeft, ChevronRight, Heart,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/Avatar";

interface SidebarProps { collapsed: boolean; onToggle: () => void; }
interface NavItem { label: string; to: string; icon: React.ElementType; badge?: number; }

const navItems: NavItem[] = [
  { label: "Dashboard",    to: "/",          icon: LayoutDashboard },
  { label: "Patients",     to: "/patients",  icon: Users },
  { label: "Risk Alerts",  to: "/alerts",    icon: AlertTriangle, badge: 3 },
  { label: "Digital Twins",to: "/twins",     icon: Activity },
  { label: "ML Models",    to: "/models",    icon: FlaskConical },
  { label: "Analytics",    to: "/analytics", icon: BarChart3 },
];

const bottomItems: NavItem[] = [
  { label: "Settings", to: "/settings", icon: Settings },
];

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const routerState = useRouterState();
  const path = routerState.location.pathname;
  const isActive = (to: string) => to === "/" ? path === "/" : path.startsWith(to);

  return (
    <aside className={cn(
      "relative flex h-full flex-col bg-white dark:bg-[#1c1c1e] border-r border-gray-200 dark:border-gray-800 transition-all duration-300 overflow-hidden",
      collapsed ? "w-[72px]" : "w-64"
    )}>
      {/* Logo */}
      <div className={cn("flex items-center h-16 px-4 border-b border-gray-100 dark:border-gray-800 shrink-0", collapsed ? "justify-center" : "gap-3")}>
        <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-primary-500 text-white shrink-0">
          <Heart size={18} strokeWidth={2.5} />
        </div>
        <AnimatePresence initial={false}>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, width: 0 }} animate={{ opacity: 1, width: "auto" }} exit={{ opacity: 0, width: 0 }}
              transition={{ duration: 0.2 }} className="overflow-hidden whitespace-nowrap"
            >
              <span className="text-sm font-bold text-gray-900 dark:text-white">Healthcare</span>
              <span className="text-sm font-bold text-primary-500"> Agent 2.0</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-4 px-2 space-y-0.5">
        {navItems.map(item => <NavLink key={item.to} item={item} collapsed={collapsed} active={isActive(item.to)} />)}
      </nav>

      {/* Bottom */}
      <div className="shrink-0 border-t border-gray-100 dark:border-gray-800 py-3 px-2 space-y-0.5">
        {bottomItems.map(item => <NavLink key={item.to} item={item} collapsed={collapsed} active={isActive(item.to)} />)}
        <div className={cn("mt-2 flex items-center rounded-xl px-2 py-2 gap-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors", collapsed && "justify-center")}>
          <Avatar name="Dr. Smith" size="sm" />
          <AnimatePresence initial={false}>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }} animate={{ opacity: 1, width: "auto" }} exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.2 }} className="overflow-hidden min-w-0"
              >
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate whitespace-nowrap">Dr. Smith</p>
                <p className="text-xs text-gray-500 truncate whitespace-nowrap">Cardiologist</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Toggle button */}
      <button
        onClick={onToggle}
        className="absolute -right-3 top-[72px] z-10 flex items-center justify-center w-6 h-6 rounded-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 shadow-sm text-gray-500 hover:text-gray-900 dark:hover:text-white transition-colors cursor-pointer"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? <ChevronRight size={12} /> : <ChevronLeft size={12} />}
      </button>
    </aside>
  );
}

function NavLink({ item, collapsed, active }: { item: NavItem; collapsed: boolean; active: boolean }) {
  const Icon = item.icon;
  return (
    <Link
      to={item.to}
      className={cn(
        "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500",
        active
          ? "bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400"
          : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white",
        collapsed && "justify-center px-2"
      )}
      title={collapsed ? item.label : undefined}
    >
      {active && (
        <motion.span
          layoutId="sidebar-active-pill"
          className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full bg-primary-500"
          transition={{ type: "spring", stiffness: 500, damping: 35 }}
        />
      )}
      <Icon size={18} strokeWidth={active ? 2.5 : 2} className="shrink-0" aria-hidden />
      <AnimatePresence initial={false}>
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0, width: 0 }} animate={{ opacity: 1, width: "auto" }} exit={{ opacity: 0, width: 0 }}
            transition={{ duration: 0.2 }} className="overflow-hidden whitespace-nowrap flex-1"
          >
            {item.label}
          </motion.span>
        )}
      </AnimatePresence>
      {item.badge != null && !collapsed && (
        <span className="ml-auto flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full text-[10px] font-bold bg-danger-500 text-white">
          {item.badge}
        </span>
      )}
      {item.badge != null && collapsed && (
        <span className="absolute top-1 right-1 flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-bold bg-danger-500 text-white">
          {item.badge}
        </span>
      )}
    </Link>
  );
}
