import { m as S, q as _, v as m, x as w } from "./api-D4goXXVb.js";
const { defineStore: h } = window.__etamusic.pinia, { ref: c, computed: s } = window.__etamusic.vue, y = h("netease", () => {
  const e = c([]), u = c(null), a = s(
    () => e.value.find((n) => String(n.ncm_uid) === String(u.value)) || null
  ), l = s(() => !!a.value);
  async function r() {
    var n;
    try {
      const t = await w();
      e.value = t.accounts || [], u.value = t.current || (((n = e.value[0]) == null ? void 0 : n.ncm_uid) ?? null);
    } catch {
      e.value = [], u.value = null;
    }
  }
  async function o(n) {
    const t = await m(n);
    u.value = String(n);
    const i = e.value.findIndex((g) => String(g.ncm_uid) === String(n));
    i >= 0 && t.account && (e.value[i] = { ...e.value[i], ...t.account });
  }
  async function v(n) {
    var t;
    await _(n), e.value = e.value.filter((i) => String(i.ncm_uid) !== String(n)), String(u.value) === String(n) && (u.value = ((t = e.value[0]) == null ? void 0 : t.ncm_uid) ?? null);
  }
  async function d() {
    try {
      await S();
    } catch {
    }
  }
  function f(n) {
    if (!n || !n.ncm_uid) return;
    const t = e.value.findIndex((i) => String(i.ncm_uid) === String(n.ncm_uid));
    t >= 0 ? e.value[t] = { ...e.value[t], ...n } : e.value.push(n), u.value = String(n.ncm_uid);
  }
  return {
    accounts: e,
    currentUid: u,
    currentAccount: a,
    isLoggedIn: l,
    load: r,
    switchTo: o,
    remove: v,
    refresh: d,
    onLoginSuccess: f
  };
});
export {
  y as u
};
