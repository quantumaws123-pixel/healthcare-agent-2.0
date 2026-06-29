import React, { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SearchBarProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSearch?: (value: string) => void;
  loading?: boolean;
  compact?: boolean;
  className?: string;
  autoFocus?: boolean;
}

export function SearchBar({ placeholder = "Search…", value: controlledValue, onChange, onSearch, loading, compact, className, autoFocus }: SearchBarProps) {
  const [internalValue, setInternalValue] = useState("");
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const value = controlledValue ?? internalValue;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInternalValue(e.target.value);
    onChange?.(e.target.value);
  };
  const handleClear = () => {
    setInternalValue("");
    onChange?.("");
    inputRef.current?.focus();
  };
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") onSearch?.(value);
    if (e.key === "Escape") handleClear();
  };

  return (
    <div className={cn(
      "relative flex items-center w-full rounded-xl border bg-white dark:bg-gray-900 transition-all duration-200",
      focused ? "border-primary-400 ring-2 ring-primary-400/20" : "border-gray-200 dark:border-gray-700",
      compact ? "h-8" : "h-10",
      className
    )}>
      <div className="flex items-center justify-center shrink-0 pl-3 text-gray-400">
        {loading ? <Loader2 size={compact ? 13 : 15} className="animate-spin" /> : <Search size={compact ? 13 : 15} />}
      </div>
      <input
        ref={inputRef}
        type="search"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className={cn("flex-1 min-w-0 bg-transparent outline-none text-gray-900 dark:text-white placeholder:text-gray-400 px-2.5", compact ? "text-xs" : "text-sm")}
      />
      <AnimatePresence>
        {value && (
          <motion.button
            initial={{ opacity: 0, scale: 0.7 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.7 }}
            transition={{ duration: 0.15 }}
            onClick={handleClear}
            className="flex items-center justify-center shrink-0 mr-2 w-5 h-5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 hover:bg-gray-200 hover:text-gray-900 transition-colors"
            type="button"
          >
            <X size={10} strokeWidth={2.5} />
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
