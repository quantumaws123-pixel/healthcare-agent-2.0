import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, Bell, Sun, Moon } from "lucide-react";
import { Avatar } from "@/components/ui/Avatar";
import { SearchBar } from "@/components/ui/SearchBar";
import { useAuthContext } from "@/context/AuthContext";

interface TopNavProps { onMenuClick: () => void; }

export function TopNav({ onMenuClick }: TopNavProps) {
  const [isDark, setIsDark] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const { user } = useAuthContext();

  const toggleDark = () => {
    setIsDark(v => !v);
    document.documentElement.classList.toggle("dark");
  };

  return (
    <header className="sticky top-0 z-[1100] h-16 shrink-0 flex items-center gap-4 px-4 sm:px-6 bg-white/80 dark:bg-[#1c1c1e]/80 backdrop-blur-xl border-b border-gray-200 dark:border-gray-800">
      <button onClick={onMenuClick} className="lg:hidden flex items-center justify-center w-9 h-9 rounded-xl text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" aria-label="Open menu">
        <Menu size={20} />
      </button>

      <div className="hidden sm:flex items-center gap-1.5 text-sm">
        <span className="text-gray-400">Healthcare</span>
        <span className="text-gray-300 dark:text-gray-600">/</span>
        <span className="font-semibold text-gray-900 dark:text-white">Dashboard</span>
      </div>

      <div className="flex-1" />

      <div className="hidden md:block w-64">
        <SearchBar placeholder="Search patients…" compact />
      </div>

      <button onClick={toggleDark} className="flex items-center justify-center w-9 h-9 rounded-xl text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors" aria-label="Toggle dark mode">
        <motion.div animate={{ rotate: isDark ? 180 : 0 }} transition={{ type: "spring", stiffness: 300, damping: 25 }}>
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
        </motion.div>
      </button>

      {/* Notifications */}
      <div className="relative">
        <button onClick={() => setNotifOpen(v => !v)} className="flex items-center justify-center w-9 h-9 rounded-xl text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
          <Bell size={18} />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-danger-500 border-2 border-white dark:border-gray-900" />
        </button>
        <AnimatePresence>
          {notifOpen && (
            <>
              <div className="fixed inset-0 z-[1000]" onClick={() => setNotifOpen(false)} />
              <motion.div
                initial={{ opacity: 0, y: 8, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 4, scale: 0.98 }}
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
                className="absolute right-0 top-full mt-2 z-[1001] w-80 rounded-2xl p-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-float">
                <p className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Notifications</p>
                {NOTIFS.map((n, i) => (
                  <div key={i} className="flex gap-3 py-2.5 border-b border-gray-100 dark:border-gray-800 last:border-0">
                    <div className={`mt-1 w-2 h-2 rounded-full shrink-0 ${n.urgent ? "bg-danger-500" : "bg-primary-500"}`} />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{n.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{n.time}</p>
                    </div>
                  </div>
                ))}
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>

      {/* User avatar */}
      <Avatar
        name={user?.name ?? user?.email ?? "U"}
        src={user?.avatar_url ?? undefined}
        size="sm"
      />
    </header>
  );
}

const NOTIFS = [
  { title: "Patient HDT-SGH risk level elevated to High", time: "2 minutes ago", urgent: true },
  { title: "3 patients missed medication today",          time: "15 minutes ago", urgent: false },
  { title: "Weekly compliance report ready",             time: "1 hour ago",     urgent: false },
];
