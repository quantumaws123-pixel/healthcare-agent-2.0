import { jsx, jsxs } from 'react/jsx-runtime';
import x__default, { useId, createContext, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { p } from './utils-DSi8ROt9.mjs';

const m = createContext(null);
function u() {
  const t = useContext(m);
  if (!t) throw new Error("Tab components must be inside <Tabs>");
  return t;
}
function A({ defaultTab: t, activeTab: a, onTabChange: e, variant: i = "line", children: s, className: d }) {
  const b = useId(), [p$1, o] = x__default.useState(t != null ? t : ""), c = a != null ? a : p$1, n = (x) => {
    o(x), e == null ? void 0 : e(x);
  };
  return jsx(m.Provider, { value: { activeTab: c, setActiveTab: n, variant: i, baseId: b }, children: jsx("div", { className: p("w-full", d), children: s }) });
}
function C({ children: t, className: a }) {
  const { variant: e } = u();
  return jsx("div", { role: "tablist", className: p("flex items-center gap-1", e === "line" && "border-b border-gray-200 dark:border-gray-800", e === "pill" && "bg-gray-100 dark:bg-gray-800 rounded-xl p-1", e === "card" && "gap-2", a), children: t });
}
function P({ id: t, children: a, icon: e, badge: i, disabled: s, className: d }) {
  const { activeTab: b, setActiveTab: p$1, variant: o, baseId: c } = u(), n = b === t;
  return jsxs("button", { role: "tab", id: `${c}-tab-${t}`, "aria-controls": `${c}-panel-${t}`, "aria-selected": n, disabled: s, onClick: () => p$1(t), className: p("relative flex items-center gap-2 font-medium text-sm transition-colors duration-150", "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:rounded-lg", "disabled:opacity-40 disabled:pointer-events-none", o === "line" && ["px-3 pb-3 pt-1", n ? "text-gray-900 dark:text-white" : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"], o === "pill" && ["px-4 py-1.5 rounded-lg", n ? "text-gray-900 dark:text-white bg-white dark:bg-gray-900 shadow-sm" : "text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"], o === "card" && ["px-4 py-2 rounded-xl border", n ? "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 shadow-sm text-gray-900 dark:text-white" : "bg-transparent border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"], d), children: [e && jsx("span", { className: "shrink-0", "aria-hidden": true, children: e }), a, i != null && jsx("span", { className: "ml-0.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[9px] font-bold bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300", children: i }), o === "line" && n && jsx(motion.span, { layoutId: "tab-line-indicator", className: "absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-primary-500", transition: { type: "spring", stiffness: 500, damping: 35 } })] });
}
function j({ children: t, className: a }) {
  return jsx("div", { className: p("mt-4", a), children: t });
}
function _({ id: t, children: a, className: e }) {
  const { activeTab: i, baseId: s } = u();
  return jsx(AnimatePresence, { mode: "wait", initial: false, children: i === t && jsx(motion.div, { role: "tabpanel", id: `${s}-panel-${t}`, "aria-labelledby": `${s}-tab-${t}`, initial: { opacity: 0, y: 6 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -4 }, transition: { duration: 0.2, ease: [0.16, 1, 0.3, 1] }, className: p("outline-none", e), tabIndex: 0, children: a }, t) });
}

export { A, C, P, _, j };
//# sourceMappingURL=Tabs-CG0WxNoy.mjs.map
