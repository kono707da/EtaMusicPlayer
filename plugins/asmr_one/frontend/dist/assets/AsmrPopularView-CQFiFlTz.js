import { o as r, c as m, a as f, d, f as B, u as e, F as T, r as E, b as s, w as l, t as z, e as R, _ as M, $ as U } from "./api-BVwVWTpM.js";
import { W as Z } from "./WorkCard-B-OrDsz5.js";
import { u as q } from "./store-KZ0YZNeM.js";
const J = { class: "flex-1 min-h-0 overflow-auto" }, K = {
  key: 0,
  class: "flex h-full items-center justify-center text-muted-foreground"
}, Q = {
  key: 2,
  class: "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 pb-4"
}, X = {
  __name: "WorkGrid",
  props: {
    works: { type: Array, default: () => [] },
    loading: { type: Boolean, default: !1 }
  },
  setup(v) {
    const { useRouter: i } = window.__etamusic.vueRouter, { Empty: C } = window.__etamusic.ui, { Headphones: $ } = window.__etamusic.icons, c = i();
    function P(w) {
      c.push(`/asmr/work/${w}`);
    }
    return (w, k) => (r(), m("div", J, [
      v.loading ? (r(), m("div", K, [...k[0] || (k[0] = [
        f("div", { class: "h-6 w-6 border-2 border-primary border-t-transparent rounded-full animate-spin mr-2" }, null, -1),
        d(" 加载中... ", -1)
      ])])) : v.works.length === 0 ? (r(), B(e(C), {
        key: 1,
        icon: e($),
        title: "没有找到作品",
        class: "h-full"
      }, null, 8, ["icon"])) : (r(), m("div", Q, [
        (r(!0), m(T, null, E(v.works, (_) => (r(), B(Z, {
          key: _.id,
          work: _,
          onClick: P
        }, null, 8, ["work"]))), 128))
      ]))
    ]));
  }
}, Y = { class: "flex h-full flex-col gap-4" }, ee = { class: "flex items-center justify-between" }, te = { class: "flex items-center gap-3" }, se = { class: "flex items-center gap-2" }, oe = {
  key: 0,
  class: "flex items-center justify-center gap-2 py-2"
}, ae = { class: "text-sm text-muted-foreground" }, ue = {
  __name: "AsmrPopularView",
  setup(v) {
    const { ref: i, onMounted: C } = window.__etamusic.vue, { useRouter: $ } = window.__etamusic.vueRouter, {
      Button: c,
      Badge: P,
      Select: w,
      SelectTrigger: k,
      SelectValue: _,
      SelectContent: W,
      SelectItem: j,
      useToast: F
    } = window.__etamusic.ui, { ArrowLeft: G, Flame: V, Sparkles: O, Loader2: ne } = window.__etamusic.icons, A = $(), N = F(), x = q(), D = [24, 30, 60, 120], g = i("popular"), y = i([]), p = i(!1), n = i(1), b = i(30), S = i(1);
    async function h() {
      var o, t, a;
      p.value = !0;
      try {
        const u = g.value === "popular" ? await M(n.value, b.value) : await U(n.value, b.value);
        y.value = u.works || [], S.value = ((o = u.pagination) == null ? void 0 : o.totalPage) || 1;
      } catch (u) {
        N.error("加载失败", ((a = (t = u == null ? void 0 : u.response) == null ? void 0 : t.data) == null ? void 0 : a.detail) || u.message, u), y.value = [];
      } finally {
        p.value = !1;
      }
    }
    function I(o) {
      if (g.value !== o) {
        if (o === "recommendations" && !x.isLoggedIn) {
          N.warning("个性化推荐需要登录"), A.push("/asmr/account");
          return;
        }
        g.value = o, n.value = 1, h();
      }
    }
    function H(o) {
      b.value = Number(o), n.value = 1, h();
    }
    function L(o) {
      n.value = o, h();
    }
    return C(() => {
      x.loaded || x.load(), h();
    }), (o, t) => (r(), m("div", Y, [
      f("div", ee, [
        f("div", te, [
          s(e(c), {
            variant: "ghost",
            size: "sm",
            onClick: t[0] || (t[0] = (a) => e(A).push("/asmr"))
          }, {
            default: l(() => [
              s(e(G), { class: "h-4 w-4" }),
              t[5] || (t[5] = d(" 返回 ", -1))
            ]),
            _: 1
          }),
          s(e(V), { class: "h-5 w-5 text-primary" }),
          t[6] || (t[6] = f("h2", { class: "text-lg font-semibold" }, "推荐", -1))
        ]),
        f("div", se, [
          s(e(w), {
            "model-value": String(e(b)),
            "onUpdate:modelValue": H
          }, {
            default: l(() => [
              s(e(k), { class: "h-9 w-[90px]" }, {
                default: l(() => [
                  s(e(_))
                ]),
                _: 1
              }),
              s(e(W), null, {
                default: l(() => [
                  (r(), m(T, null, E(D, (a) => s(e(j), {
                    key: a,
                    value: String(a)
                  }, {
                    default: l(() => [
                      d(z(a) + "/页 ", 1)
                    ]),
                    _: 2
                  }, 1032, ["value"])), 64))
                ]),
                _: 1
              })
            ]),
            _: 1
          }, 8, ["model-value"]),
          s(e(c), {
            variant: e(g) === "popular" ? "gold" : "ghost",
            size: "sm",
            onClick: t[1] || (t[1] = (a) => I("popular"))
          }, {
            default: l(() => [
              s(e(V), { class: "h-4 w-4" }),
              t[7] || (t[7] = d(" 热门 ", -1))
            ]),
            _: 1
          }, 8, ["variant"]),
          s(e(c), {
            variant: e(g) === "recommendations" ? "gold" : "ghost",
            size: "sm",
            onClick: t[2] || (t[2] = (a) => I("recommendations"))
          }, {
            default: l(() => [
              s(e(O), { class: "h-4 w-4" }),
              t[9] || (t[9] = d(" 个性化 ", -1)),
              e(x).isLoggedIn ? R("", !0) : (r(), B(e(P), {
                key: 0,
                variant: "outline",
                class: "ml-1 text-[10px]"
              }, {
                default: l(() => [...t[8] || (t[8] = [
                  d("需登录", -1)
                ])]),
                _: 1
              }))
            ]),
            _: 1
          }, 8, ["variant"])
        ])
      ]),
      s(X, {
        works: e(y),
        loading: e(p)
      }, null, 8, ["works", "loading"]),
      e(y).length > 0 && e(S) > 1 ? (r(), m("div", oe, [
        s(e(c), {
          variant: "ghost",
          size: "sm",
          disabled: e(n) <= 1 || e(p),
          onClick: t[3] || (t[3] = (a) => L(e(n) - 1))
        }, {
          default: l(() => [...t[10] || (t[10] = [
            d(" 上一页 ", -1)
          ])]),
          _: 1
        }, 8, ["disabled"]),
        f("span", ae, z(e(n)) + " / " + z(e(S)), 1),
        s(e(c), {
          variant: "ghost",
          size: "sm",
          disabled: e(n) >= e(S) || e(p),
          onClick: t[4] || (t[4] = (a) => L(e(n) + 1))
        }, {
          default: l(() => [...t[11] || (t[11] = [
            d(" 下一页 ", -1)
          ])]),
          _: 1
        }, 8, ["disabled"])
      ])) : R("", !0)
    ]));
  }
};
export {
  ue as default
};
