import { jsxs, jsx } from 'react/jsx-runtime';
import { useEffect } from 'react';
import { useMotionValue, useTransform, animate, motion } from 'framer-motion';
import { p } from './utils-DSi8ROt9.mjs';

const w = { xs: "h-1", sm: "h-1.5", md: "h-2", lg: "h-3" };
function j({ value: o, max: n = 100, label: t, showValue: l = false, size: c = "md", color: u, trackClassName: f, className: h, animated: i = true }) {
  const e = Math.min(100, Math.max(0, o / n * 100)), r = useMotionValue(0), x = useTransform(r, (m) => `${m}%`);
  return useEffect(() => {
    if (!i) {
      r.set(e);
      return;
    }
    return animate(r, e, { duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 0.05 }).stop;
  }, [e, r, i]), jsxs("div", { className: p("w-full", h), children: [(t || l) && jsxs("div", { className: "flex items-center justify-between mb-1.5", children: [t && jsx("span", { className: "text-xs font-medium text-gray-500 dark:text-gray-400", children: t }), l && jsxs("span", { className: "text-xs font-semibold text-gray-900 dark:text-white tabular-nums", children: [Math.round(e), "%"] })] }), jsx("div", { className: p("w-full rounded-full overflow-hidden", w[c], f != null ? f : "bg-gray-100 dark:bg-gray-800"), role: "progressbar", "aria-valuenow": o, "aria-valuemin": 0, "aria-valuemax": n, children: jsx(motion.div, { className: "h-full rounded-full", style: { width: x, backgroundColor: u != null ? u : "#3b82f6" } }) })] });
}

export { j };
//# sourceMappingURL=ProgressBar-DtEKHEw5.mjs.map
