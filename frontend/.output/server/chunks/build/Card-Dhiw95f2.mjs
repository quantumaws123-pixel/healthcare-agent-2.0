import { jsx } from 'react/jsx-runtime';
import x__default from 'react';
import { motion } from 'framer-motion';
import { cva } from 'class-variance-authority';
import { p } from './utils-DSi8ROt9.mjs';

const m = { type: "spring", stiffness: 300, damping: 30, mass: 1 }, s = { type: "tween", ease: [0.16, 1, 0.3, 1], duration: 0.35 }, c = { type: "tween", ease: [0.16, 1, 0.3, 1], duration: 0.2 }, N = { hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0, transition: s }, exit: { opacity: 0, y: 8, transition: c } }, I = { hidden: { opacity: 0, y: 24, scale: 0.96 }, visible: { opacity: 1, y: 0, scale: 1, transition: { ...m, delay: 0.05 } }, exit: { opacity: 0, y: 12, scale: 0.98, transition: c } }, j = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.06, delayChildren: 0.05 } } }, H = { hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0, transition: s } };
({ ...s });
const u = cva("relative rounded-2xl overflow-hidden transition-all duration-200", { variants: { variant: { default: "bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-card", elevated: "bg-white dark:bg-gray-900 shadow-float", glass: "bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border border-white/40 dark:border-gray-700/40 shadow-panel", flat: "bg-gray-50 dark:bg-gray-800", outline: "bg-transparent border border-gray-200 dark:border-gray-700" }, hoverable: { true: "cursor-pointer hover:shadow-float hover:-translate-y-0.5 active:translate-y-0", false: "" }, padding: { none: "", sm: "p-4", md: "p-5", lg: "p-6", xl: "p-8" } }, defaultVariants: { variant: "default", hoverable: false, padding: "md" } }), v = x__default.forwardRef(({ className: t, variant: e, hoverable: a, padding: y, asMotion: g, children: n, ...o }, d) => {
  const l = p(u({ variant: e, hoverable: a, padding: y, className: t }));
  return g ? jsx(motion.div, { ref: d, className: l, whileHover: a ? { y: -2 } : void 0, whileTap: a ? { scale: 0.995 } : void 0, transition: { type: "spring", stiffness: 400, damping: 30 }, ...o, children: n }) : jsx("div", { ref: d, className: l, ...o, children: n });
});
v.displayName = "Card";
function O({ className: t, children: e, ...a }) {
  return jsx("div", { className: p("flex items-start justify-between gap-4 mb-4", t), ...a, children: e });
}
function R({ className: t, children: e, ...a }) {
  return jsx("h3", { className: p("text-base font-semibold text-gray-900 dark:text-white leading-tight", t), ...a, children: e });
}
function T({ className: t, children: e, ...a }) {
  return jsx("p", { className: p("text-sm text-gray-500 dark:text-gray-400 mt-0.5", t), ...a, children: e });
}
function V({ className: t, children: e, ...a }) {
  return jsx("div", { className: p("", t), ...a, children: e });
}

export { H, I, N, O, R, T, V, j, v };
//# sourceMappingURL=Card-Dhiw95f2.mjs.map
