import { V as w, W as h, X as l, Y as b, Z as v } from "./api-BVwVWTpM.js";
/**
* @vue/runtime-dom v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
let E;
const f = typeof window < "u" && window.trustedTypes;
if (f)
  try {
    E = /* @__PURE__ */ f.createPolicy("vue", {
      createHTML: (t) => t
    });
  } catch (t) {
    process.env.NODE_ENV !== "production" && v(`Error creating trusted types policy: ${t}`);
  }
process.env.NODE_ENV;
function a(t, e, o, r) {
  t.addEventListener(e, o, r);
}
const y = (t) => {
  const e = t.props["onUpdate:modelValue"] || !1;
  return l(e) ? (o) => b(e, o) : e;
};
function K(t) {
  t.target.composing = !0;
}
function g(t) {
  const e = t.target;
  e.composing && (e.composing = !1, e.dispatchEvent(new Event("input")));
}
const d = /* @__PURE__ */ Symbol("_assign");
function m(t, e, o) {
  return e && (t = t.trim()), o && (t = h(t)), t;
}
const M = {
  created(t, { modifiers: { lazy: e, trim: o, number: r } }, n) {
    t[d] = y(n);
    const s = r || n.props && n.props.type === "number";
    a(t, e ? "change" : "input", (i) => {
      i.target.composing || t[d](m(t.value, o, s));
    }), (o || s) && a(t, "change", () => {
      t.value = m(t.value, o, s);
    }), e || (a(t, "compositionstart", K), a(t, "compositionend", g), a(t, "change", g));
  },
  // set value on mounted so it's after min/max for type="range"
  mounted(t, { value: e }) {
    t.value = e ?? "";
  },
  beforeUpdate(t, { value: e, oldValue: o, modifiers: { lazy: r, trim: n, number: s } }, i) {
    if (t[d] = y(i), t.composing) return;
    const c = (s || t.type === "number") && !/^0\d/.test(t.value) ? h(t.value) : t.value, u = e ?? "";
    if (c === u)
      return;
    const p = t.getRootNode();
    (p instanceof Document || p instanceof ShadowRoot) && p.activeElement === t && t.type !== "range" && (r && e === o || n && t.value.trim() === u) || (t.value = u);
  }
}, N = ["ctrl", "shift", "alt", "meta"], _ = {
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
  exact: (t, e) => N.some((o) => t[`${o}Key`] && !e.includes(o))
}, S = (t, e) => {
  if (!t) return t;
  const o = t._withMods || (t._withMods = {}), r = e.join(".");
  return o[r] || (o[r] = (n, ...s) => {
    for (let i = 0; i < e.length; i++) {
      const c = _[e[i]];
      if (c && c(n, e)) return;
    }
    return t(n, ...s);
  });
}, T = {
  esc: "escape",
  space: " ",
  up: "arrow-up",
  left: "arrow-left",
  right: "arrow-right",
  down: "arrow-down",
  delete: "backspace"
}, k = (t, e) => {
  const o = t._withKeys || (t._withKeys = {}), r = e.join(".");
  return o[r] || (o[r] = (n) => {
    if (!("key" in n))
      return;
    const s = w(n.key);
    if (e.some(
      (i) => i === s || T[i] === s
    ))
      return t(n);
  });
};
export {
  S as a,
  M as v,
  k as w
};
