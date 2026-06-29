import { jsxs, jsx } from 'react/jsx-runtime';
import { motion } from 'framer-motion';
import { p } from './utils-DSi8ROt9.mjs';
import { N } from './Card-Dhiw95f2.mjs';
import { y } from './Button-DfssnJWK.mjs';

const f = { sm: { wrapper: "py-8", iconWrapper: "w-10 h-10", title: "text-sm", desc: "text-xs" }, md: { wrapper: "py-12", iconWrapper: "w-14 h-14", title: "text-base", desc: "text-sm" }, lg: { wrapper: "py-16", iconWrapper: "w-16 h-16", title: "text-lg", desc: "text-sm" } };
function k({ icon: i, title: n, description: l, action: t, secondaryAction: r, className: c, size: x = "md" }) {
  const a = f[x];
  return jsxs(motion.div, { variants: N, initial: "hidden", animate: "visible", className: p("flex flex-col items-center justify-center text-center", a.wrapper, c), children: [i && jsx("div", { className: p("flex items-center justify-center rounded-2xl mb-4 bg-gray-100 dark:bg-gray-800 text-gray-400", a.iconWrapper), children: i }), jsx("h3", { className: p("font-semibold text-gray-900 dark:text-white", a.title), children: n }), l && jsx("p", { className: p("mt-1.5 text-gray-500 dark:text-gray-400 max-w-xs", a.desc), children: l }), (t || r) && jsxs("div", { className: "mt-5 flex items-center gap-3", children: [t && jsx(y, { size: "sm", onClick: t.onClick, children: t.label }), r && jsx(y, { size: "sm", variant: "secondary", onClick: r.onClick, children: r.label })] })] });
}

export { k };
//# sourceMappingURL=EmptyState-CKaUPaTz.mjs.map
