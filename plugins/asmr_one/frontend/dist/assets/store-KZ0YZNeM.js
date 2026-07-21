import { a0 as w, a1 as _, a2 as m, a3 as y } from "./api-BVwVWTpM.js";
const { defineStore: p } = window.__etamusic.pinia, { ref: l, computed: A } = window.__etamusic.vue, $ = p("asmrAccount", () => {
  const a = l(!1), t = l(null), r = l(!1), c = l(!1), u = l(!1), i = A(() => a.value);
  async function g() {
    u.value = !0;
    try {
      const e = await y();
      a.value = e.logged_in, t.value = e.user, r.value = e.reg_enabled;
    } catch {
      a.value = !1, t.value = null;
    } finally {
      c.value = !0, u.value = !1;
    }
  }
  async function d(e, o) {
    const n = await m(e, o);
    return a.value = n.logged_in, t.value = n.user, n;
  }
  async function v(e, o, n = null) {
    const s = await _(e, o, n);
    return s.token_saved && (a.value = !0, t.value = s.user), s;
  }
  async function f() {
    await w(), a.value = !1, t.value = null;
  }
  return {
    loggedIn: a,
    user: t,
    regEnabled: r,
    loaded: c,
    loading: u,
    isLoggedIn: i,
    load: g,
    login: d,
    register: v,
    logout: f
  };
});
export {
  $ as u
};
