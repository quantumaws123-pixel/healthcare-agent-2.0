import { jsxs, jsx } from 'react/jsx-runtime';
import { useState, useRef } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Loader2, Search, X } from 'lucide-react';
import { p } from './utils-DSi8ROt9.mjs';

function R({ placeholder: d = "Search\u2026", value: m, onChange: n, onSearch: y, loading: f, compact: t, className: h, autoFocus: g }) {
  const [x, i] = useState(""), [p$1, s] = useState(false), o = useRef(null), a = m != null ? m : x, b = (r) => {
    i(r.target.value), n == null ? void 0 : n(r.target.value);
  }, l = () => {
    var _a;
    i(""), n == null ? void 0 : n(""), (_a = o.current) == null ? void 0 : _a.focus();
  }, k = (r) => {
    r.key === "Enter" && (y == null ? void 0 : y(a)), r.key === "Escape" && l();
  };
  return jsxs("div", { className: p("relative flex items-center w-full rounded-xl border bg-white dark:bg-gray-900 transition-all duration-200", p$1 ? "border-primary-400 ring-2 ring-primary-400/20" : "border-gray-200 dark:border-gray-700", t ? "h-8" : "h-10", h), children: [jsx("div", { className: "flex items-center justify-center shrink-0 pl-3 text-gray-400", children: f ? jsx(Loader2, { size: t ? 13 : 15, className: "animate-spin" }) : jsx(Search, { size: t ? 13 : 15 }) }), jsx("input", { ref: o, type: "search", value: a, onChange: b, onKeyDown: k, onFocus: () => s(true), onBlur: () => s(false), placeholder: d, autoFocus: g, className: p("flex-1 min-w-0 bg-transparent outline-none text-gray-900 dark:text-white placeholder:text-gray-400 px-2.5", t ? "text-xs" : "text-sm") }), jsx(AnimatePresence, { children: a && jsx(motion.button, { initial: { opacity: 0, scale: 0.7 }, animate: { opacity: 1, scale: 1 }, exit: { opacity: 0, scale: 0.7 }, transition: { duration: 0.15 }, onClick: l, className: "flex items-center justify-center shrink-0 mr-2 w-5 h-5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 hover:bg-gray-200 hover:text-gray-900 transition-colors", type: "button", children: jsx(X, { size: 10, strokeWidth: 2.5 }) }) })] });
}

export { R };
//# sourceMappingURL=SearchBar-CM7su10B.mjs.map
