import { jsxs, jsx } from 'react/jsx-runtime';
import { cva } from 'class-variance-authority';
import { s as s$1, p as p$1 } from './utils-DSi8ROt9.mjs';

const h = cva("relative inline-flex items-center justify-center rounded-full shrink-0 font-semibold select-none overflow-hidden", { variants: { size: { xs: "w-6  h-6  text-[9px]", sm: "w-8  h-8  text-xs", md: "w-10 h-10 text-sm", lg: "w-12 h-12 text-base", xl: "w-16 h-16 text-lg", "2xl": "w-20 h-20 text-xl" } }, defaultVariants: { size: "md" } }), s = ["bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300", "bg-success-100 dark:bg-green-900/40 text-success-700 dark:text-green-300", "bg-warning-100 dark:bg-yellow-900/40 text-warning-600 dark:text-yellow-300", "bg-danger-100 dark:bg-red-900/40 text-danger-600 dark:text-red-300", "bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300", "bg-pink-100 dark:bg-pink-900/40 text-pink-700 dark:text-pink-300", "bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300"];
function p(t) {
  let e = 0;
  for (let r = 0; r < t.length; r++) e = t.charCodeAt(r) + ((e << 5) - e);
  return s[Math.abs(e) % s.length];
}
const k = { online: "bg-success-500", away: "bg-warning-500", busy: "bg-danger-500", offline: "bg-gray-400" };
function w({ name: t = "", src: e, alt: r, size: i, className: o, status: n }) {
  const d = s$1(t || "?"), g = p(t);
  return jsxs("div", { className: "relative inline-flex shrink-0", children: [jsx("div", { className: p$1(h({ size: i, className: o }), !e && g), children: e ? jsx("img", { src: e, alt: r != null ? r : t, className: "w-full h-full object-cover" }) : jsx("span", { "aria-label": t, children: d }) }), n && jsx("span", { className: p$1("absolute bottom-0 right-0 rounded-full border-2 border-white dark:border-gray-900", k[n], i === "xs" || i === "sm" ? "w-2 h-2" : "w-3 h-3") })] });
}

export { w };
//# sourceMappingURL=Avatar-Cq-EhdWm.mjs.map
