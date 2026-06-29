import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function p(...t) {
  return twMerge(clsx(t));
}
function s(t) {
  return t.split(" ").slice(0, 2).map((r) => {
    var _a, _b;
    return (_b = (_a = r[0]) == null ? void 0 : _a.toUpperCase()) != null ? _b : "";
  }).join("");
}

export { p, s };
//# sourceMappingURL=utils-DSi8ROt9.mjs.map
