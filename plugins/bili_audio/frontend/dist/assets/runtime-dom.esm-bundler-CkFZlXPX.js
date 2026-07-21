import { z as i, A as p } from "./api-BBDGHqfl.js";
/**
* @vue/runtime-dom v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
let y;
const a = typeof window < "u" && window.trustedTypes;
if (a)
  try {
    y = /* @__PURE__ */ a.createPolicy("vue", {
      createHTML: (e) => e
    });
  } catch (e) {
    process.env.NODE_ENV !== "production" && p(`Error creating trusted types policy: ${e}`);
  }
process.env.NODE_ENV;
const w = {
  esc: "escape",
  space: " ",
  up: "arrow-up",
  left: "arrow-left",
  right: "arrow-right",
  down: "arrow-down",
  delete: "backspace"
}, u = (e, r) => {
  const o = e._withKeys || (e._withKeys = {}), c = r.join(".");
  return o[c] || (o[c] = (t) => {
    if (!("key" in t))
      return;
    const s = i(t.key);
    if (r.some(
      (n) => n === s || w[n] === s
    ))
      return e(t);
  });
};
export {
  u as w
};
