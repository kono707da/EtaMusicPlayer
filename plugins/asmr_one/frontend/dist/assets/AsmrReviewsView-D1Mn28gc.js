import { c as l, a as i, b as n, w as d, u as t, d as c, f as I, F as E, r as F, x as K, o as r, t as m, n as M, k as U, e as C, K as W } from "./api-BVwVWTpM.js";
import { u as q } from "./store-KZ0YZNeM.js";
import { _ as G } from "./_plugin-vue_export-helper-CHgC5LLL.js";
const H = { class: "flex h-full flex-col gap-4" }, J = { class: "flex items-center justify-between" }, O = { class: "flex items-center gap-3" }, P = { class: "flex-1 min-h-0 overflow-auto" }, Q = {
  key: 0,
  class: "flex items-center justify-center py-12 text-muted-foreground"
}, X = {
  key: 2,
  class: "flex flex-col gap-2 pb-4"
}, Y = ["src", "onClick"], Z = { class: "flex-1 min-w-0 flex flex-col gap-1" }, ee = { class: "flex items-center gap-2" }, te = { class: "text-sm font-medium text-foreground truncate" }, se = {
  key: 0,
  class: "text-sm text-muted-foreground line-clamp-3"
}, oe = { class: "flex items-center justify-between mt-auto" }, ae = { class: "text-xs text-muted-foreground" }, ne = {
  __name: "AsmrReviewsView",
  setup(ie) {
    const { ref: _, onMounted: R } = window.__etamusic.vue, { useRouter: B } = window.__etamusic.vueRouter, { Button: w, Badge: k, Empty: V, useToast: z } = window.__etamusic.ui, { ArrowLeft: A, Star: y, Loader2: L, Trash2: N, RefreshCw: $ } = window.__etamusic.icons, v = B(), x = z(), h = q(), u = _([]), f = _(!1), j = _(1), b = _(0);
    async function p() {
      var a, s, e;
      if (!h.isLoggedIn) {
        v.push("/asmr/account");
        return;
      }
      f.value = !0;
      try {
        const o = await K("create_date", "desc", j.value);
        u.value = o.reviews || o.works || [], b.value = ((a = o.pagination) == null ? void 0 : a.totalCount) || u.value.length;
      } catch (o) {
        x.error("加载失败", ((e = (s = o == null ? void 0 : o.response) == null ? void 0 : s.data) == null ? void 0 : e.detail) || o.message);
      } finally {
        f.value = !1;
      }
    }
    async function S(a) {
      var e, o;
      const s = a.work_id || a.id;
      try {
        await W(s), x.success("已删除评价"), await p();
      } catch (g) {
        x.error("删除失败", ((o = (e = g == null ? void 0 : g.response) == null ? void 0 : e.data) == null ? void 0 : o.detail) || g.message);
      }
    }
    function T(a) {
      v.push(`/asmr/work/${a}`);
    }
    function D(a) {
      if (!a) return "--";
      try {
        return new Date(a).toLocaleString("zh-CN", { hour12: !1 });
      } catch {
        return a;
      }
    }
    return R(() => {
      h.loaded ? p() : h.load().then(p);
    }), (a, s) => (r(), l("div", H, [
      i("div", J, [
        i("div", O, [
          n(t(w), {
            variant: "ghost",
            size: "sm",
            onClick: s[0] || (s[0] = (e) => t(v).push("/asmr"))
          }, {
            default: d(() => [
              n(t(A), { class: "h-4 w-4" }),
              s[2] || (s[2] = c(" 返回 ", -1))
            ]),
            _: 1
          }),
          s[3] || (s[3] = i("h2", { class: "text-lg font-semibold" }, "我的评价", -1)),
          n(t(k), {
            variant: "outline",
            class: "text-xs"
          }, {
            default: d(() => [
              c("共 " + m(t(b)) + " 条", 1)
            ]),
            _: 1
          })
        ]),
        n(t(w), {
          variant: "ghost",
          size: "sm",
          disabled: t(f),
          onClick: p
        }, {
          default: d(() => [
            n(t($), {
              class: M(["h-4 w-4", { "animate-spin": t(f) }])
            }, null, 8, ["class"]),
            s[4] || (s[4] = c(" 刷新 ", -1))
          ]),
          _: 1
        }, 8, ["disabled"])
      ]),
      i("div", P, [
        t(f) && t(u).length === 0 ? (r(), l("div", Q, [
          n(t(L), { class: "mr-2 h-5 w-5 animate-spin" }),
          s[5] || (s[5] = c(" 加载中... ", -1))
        ])) : t(u).length === 0 ? (r(), I(t(V), {
          key: 1,
          icon: t(y),
          title: "还没有评价",
          description: "在作品详情页可以给作品打分评价",
          class: "h-full"
        }, {
          default: d(() => [
            n(t(w), {
              variant: "gold",
              onClick: s[1] || (s[1] = (e) => t(v).push("/asmr"))
            }, {
              default: d(() => [...s[6] || (s[6] = [
                c("去浏览", -1)
              ])]),
              _: 1
            })
          ]),
          _: 1
        }, 8, ["icon"])) : (r(), l("div", X, [
          (r(!0), l(E, null, F(t(u), (e) => (r(), l("div", {
            key: e.id || e.work_id,
            class: "flex gap-3 rounded-lg border border-border bg-card/40 p-3"
          }, [
            e.work_id || e.id ? (r(), l("img", {
              key: 0,
              src: t(U)(e.work_id || e.id),
              class: "h-20 w-20 rounded-md object-cover border border-border shrink-0 cursor-pointer",
              onClick: (o) => T(e.work_id || e.id)
            }, null, 8, Y)) : C("", !0),
            i("div", Z, [
              i("div", ee, [
                i("span", te, m(e.work_title || e.title || "#" + (e.work_id || e.id)), 1),
                n(t(k), {
                  variant: "gold",
                  class: "shrink-0"
                }, {
                  default: d(() => [
                    n(t(y), { class: "h-3 w-3" }),
                    c(" " + m(e.rating), 1)
                  ]),
                  _: 2
                }, 1024)
              ]),
              e.review_text ? (r(), l("div", se, m(e.review_text), 1)) : C("", !0),
              i("div", oe, [
                i("span", ae, m(D(e.create_date || e.updated_at)), 1),
                n(t(w), {
                  variant: "ghost",
                  size: "sm",
                  class: "text-destructive h-7",
                  onClick: (o) => S(e)
                }, {
                  default: d(() => [
                    n(t(N), { class: "h-3 w-3" }),
                    s[7] || (s[7] = c(" 删除 ", -1))
                  ]),
                  _: 1
                }, 8, ["onClick"])
              ])
            ])
          ]))), 128))
        ]))
      ])
    ]));
  }
}, ce = /* @__PURE__ */ G(ne, [["__scopeId", "data-v-a07841e8"]]);
export {
  ce as default
};
