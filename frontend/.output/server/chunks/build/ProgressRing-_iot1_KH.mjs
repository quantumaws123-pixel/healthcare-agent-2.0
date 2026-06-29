import { jsxs, jsx } from 'react/jsx-runtime';
import { useEffect, useRef } from 'react';
import { useMotionValue, useTransform, animate, motion } from 'framer-motion';
import { p } from './utils-DSi8ROt9.mjs';

function $({ value: a, size: e = 80, strokeWidth: t = 7, color: s = "#3b82f6", trackColor: r = "#f3f4f6", showLabel: n = true, label: l, className: i, animationDuration: d = 1.2 }) {
  const c = Math.min(100, Math.max(0, a)), u = (e - t) / 2, f = 2 * Math.PI * u, m = useMotionValue(0), b = useTransform(m, (h) => f - h / 100 * f);
  return useEffect(() => animate(m, c, { duration: d, ease: [0.16, 1, 0.3, 1] }).stop, [c, m, d]), jsxs("div", { className: p("relative inline-flex items-center justify-center", i), style: { width: e, height: e }, role: "progressbar", "aria-valuenow": c, "aria-valuemin": 0, "aria-valuemax": 100, children: [jsxs("svg", { width: e, height: e, viewBox: `0 0 ${e} ${e}`, className: "-rotate-90", "aria-hidden": true, children: [jsx("circle", { cx: e / 2, cy: e / 2, r: u, fill: "none", stroke: r, strokeWidth: t }), jsx(motion.circle, { cx: e / 2, cy: e / 2, r: u, fill: "none", stroke: s, strokeWidth: t, strokeLinecap: "round", strokeDasharray: f, style: { strokeDashoffset: b } })] }), n && jsx("div", { className: "absolute inset-0 flex flex-col items-center justify-center", children: l != null ? l : jsx(k, { value: c, className: "text-sm font-bold text-gray-900 dark:text-white tabular-nums" }) })] });
}
function k({ value: a, className: e }) {
  const t = useMotionValue(0), s = useTransform(t, (n) => Math.round(n)), r = useRef(null);
  return useEffect(() => {
    const n = animate(t, a, { duration: 1.2, ease: [0.16, 1, 0.3, 1] }), l = s.on("change", (i) => {
      r.current && (r.current.textContent = `${i}%`);
    });
    return () => {
      n.stop(), l();
    };
  }, [a, t, s]), jsx("span", { ref: r, className: e, children: "0%" });
}

export { $ };
//# sourceMappingURL=ProgressRing-_iot1_KH.mjs.map
