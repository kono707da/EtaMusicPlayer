import { A as u, B as y } from "./api-CJ1Y_yWo.js";
/**
* @vue/runtime-dom v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
let p;
const i = typeof window < "u" && window.trustedTypes;
if (i)
  try {
    p = /* @__PURE__ */ i.createPolicy("vue", {
      createHTML: (t) => t
    });
  } catch (t) {
    process.env.NODE_ENV !== "production" && y(`Error creating trusted types policy: ${t}`);
  }
process.env.NODE_ENV;
const l = ["ctrl", "shift", "alt", "meta"], h = {
  stop: (t) => t.stopPropagation(),
  prevent: (t) => t.preventDefault(),
  self: (t) => t.target !== t.currentTarget,
  ctrl: (t) => !t.ctrlKey,
  shift: (t) => !t.shiftKey,
  alt: (t) => !t.altKey,
  meta: (t) => !t.metaKey,
  left: (t) => "button" in t && t.button !== 0,
  middle: (t) => "button" in t && t.button !== 1,
  right: (t) => "button" in t && t.button !== 2,
  exact: (t, e) => l.some((r) => t[`${r}Key`] && !e.includes(r))
}, K = (t, e) => {
  if (!t) return t;
  const r = t._withMods || (t._withMods = {}), c = e.join(".");
  return r[c] || (r[c] = (o, ...n) => {
    for (let s = 0; s < e.length; s++) {
      const a = h[e[s]];
      if (a && a(o, e)) return;
    }
    return t(o, ...n);
  });
}, d = {
  esc: "escape",
  space: " ",
  up: "arrow-up",
  left: "arrow-left",
  right: "arrow-right",
  down: "arrow-down",
  delete: "backspace"
}, f = (t, e) => {
  const r = t._withKeys || (t._withKeys = {}), c = e.join(".");
  return r[c] || (r[c] = (o) => {
    if (!("key" in o))
      return;
    const n = u(o.key);
    if (e.some(
      (s) => s === n || d[s] === n
    ))
      return t(o);
  });
};
export {
  f as a,
  K as w
};
