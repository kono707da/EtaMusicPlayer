import { c, a as i, b as g, u as e, d as n, w as l, e as h, f as d, F as E, r as T, m as $, o as t, t as _ } from "./api-CJ1Y_yWo.js";
import { u as q } from "./store-CKZLSlHE.js";
import { _ as A } from "./_plugin-vue_export-helper-CHgC5LLL.js";
const G = { class: "flex h-full flex-col gap-3" }, H = { class: "flex items-center justify-between gap-3" }, J = { class: "flex items-center gap-2" }, K = { class: "flex-1 min-h-0 overflow-auto" }, O = {
  key: 1,
  class: "flex h-full items-center justify-center text-muted-foreground"
}, Q = {
  key: 3,
  class: "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 pb-4"
}, W = ["onClick"], X = { class: "aspect-square relative overflow-hidden bg-muted" }, Y = ["src", "alt"], Z = {
  key: 1,
  class: "absolute inset-0 flex items-center justify-center"
}, ee = { class: "absolute top-2 right-2" }, te = { class: "absolute bottom-2 right-2" }, se = { class: "p-2.5" }, oe = { class: "line-clamp-2 text-sm font-medium text-foreground min-h-[2.5rem]" }, ae = { class: "mt-1.5 flex items-center justify-between text-xs text-muted-foreground" }, ie = { class: "truncate" }, re = {
  __name: "NeteasePlaylistsView",
  setup(ne) {
    const { ref: p, computed: N, onMounted: B } = window.__etamusic.vue, { useRouter: V } = window.__etamusic.vueRouter, {
      ListMusic: j,
      Loader2: F,
      RefreshCw: x,
      Music: M,
      User: S,
      AlertCircle: U
    } = window.__etamusic.icons, { Button: w, Badge: f, Empty: k, useToast: z } = window.__etamusic.ui, b = V(), D = z(), r = q(), m = p(!1), u = p([]), v = N(() => u.value.length > 0);
    async function y() {
      if (!r.isLoggedIn) {
        u.value = [];
        return;
      }
      m.value = !0;
      try {
        const s = await $();
        u.value = (s == null ? void 0 : s.playlist) || [];
      } catch (s) {
        D.error("获取歌单失败：" + (s.message || "未知错误")), u.value = [];
      } finally {
        m.value = !1;
      }
    }
    function P(s) {
      b.push(`/netease/playlist/${s.id}`);
    }
    function C(s) {
      return s ? s >= 1e8 ? (s / 1e8).toFixed(1) + "亿" : s >= 1e4 ? (s / 1e4).toFixed(1) + "万" : String(s) : "0";
    }
    function R() {
      b.push("/netease");
    }
    return B(() => {
      r.loaded ? r.isLoggedIn && y() : r.load().then(() => {
        r.isLoggedIn && y();
      });
    }), (s, o) => (t(), c("div", G, [
      i("div", H, [
        i("div", J, [
          g(e(j), { class: "h-5 w-5 text-primary" }),
          o[0] || (o[0] = i("h2", { class: "text-lg font-semibold tracking-tight" }, "我的歌单", -1)),
          e(v) ? (t(), n(e(f), {
            key: 0,
            variant: "outline",
            class: "text-muted-foreground"
          }, {
            default: l(() => [
              d(_(e(u).length) + " 个 ", 1)
            ]),
            _: 1
          })) : h("", !0)
        ]),
        e(r).isLoggedIn ? (t(), n(e(w), {
          key: 0,
          variant: "ghost",
          size: "sm",
          disabled: e(m),
          onClick: y
        }, {
          default: l(() => [
            e(m) ? (t(), n(e(x), {
              key: 0,
              class: "h-4 w-4 animate-spin"
            })) : (t(), n(e(x), {
              key: 1,
              class: "h-4 w-4"
            })),
            o[1] || (o[1] = d(" 刷新 ", -1))
          ]),
          _: 1
        }, 8, ["disabled"])) : h("", !0)
      ]),
      i("div", K, [
        !e(r).isLoggedIn && e(r).loaded ? (t(), n(e(k), {
          key: 0,
          icon: e(S),
          title: "未登录网易云账号",
          description: "请先扫码登录后查看我的歌单",
          class: "h-full"
        }, {
          default: l(() => [
            g(e(w), {
              variant: "gold",
              size: "sm",
              onClick: R
            }, {
              default: l(() => [...o[2] || (o[2] = [
                d(" 去登录 ", -1)
              ])]),
              _: 1
            })
          ]),
          _: 1
        }, 8, ["icon"])) : e(m) && !e(v) ? (t(), c("div", O, [
          g(e(F), { class: "mr-2 h-5 w-5 animate-spin" }),
          o[3] || (o[3] = d(" 加载中... ", -1))
        ])) : !e(v) && e(r).loaded ? (t(), n(e(k), {
          key: 2,
          icon: e(U),
          title: "暂无歌单",
          description: "当前账号没有创建或收藏任何歌单",
          class: "h-full"
        }, null, 8, ["icon"])) : (t(), c("div", Q, [
          (t(!0), c(E, null, T(e(u), (a) => {
            var I, L;
            return t(), c("div", {
              key: a.id,
              class: "group cursor-pointer rounded-lg border border-border bg-card/40 overflow-hidden transition-all hover:border-primary/60 hover:shadow-lg",
              onClick: (le) => P(a)
            }, [
              i("div", X, [
                a.coverImgUrl ? (t(), c("img", {
                  key: 0,
                  src: a.coverImgUrl,
                  alt: a.name,
                  loading: "lazy",
                  referrerpolicy: "no-referrer",
                  class: "absolute inset-0 h-full w-full object-cover transition-transform group-hover:scale-105"
                }, null, 8, Y)) : (t(), c("div", Z, [
                  g(e(M), { class: "h-10 w-10 text-muted-foreground" })
                ])),
                i("div", ee, [
                  g(e(f), {
                    variant: "secondary",
                    class: "text-[10px]"
                  }, {
                    default: l(() => [
                      d(_(C(a.trackCount)) + " 首 ", 1)
                    ]),
                    _: 2
                  }, 1024)
                ]),
                i("div", te, [
                  a.playCount ? (t(), n(e(f), {
                    key: 0,
                    variant: "secondary",
                    class: "text-[10px]"
                  }, {
                    default: l(() => [
                      d(" ▶ " + _(C(a.playCount)), 1)
                    ]),
                    _: 2
                  }, 1024)) : h("", !0)
                ])
              ]),
              i("div", se, [
                i("div", oe, _(a.name), 1),
                i("div", ae, [
                  i("span", ie, _(((I = a.creator) == null ? void 0 : I.nickname) || "—"), 1),
                  ((L = a.creator) == null ? void 0 : L.userId) === Number(e(r).currentUid) ? (t(), n(e(f), {
                    key: 0,
                    variant: "outline",
                    class: "text-[10px]"
                  }, {
                    default: l(() => [...o[4] || (o[4] = [
                      d(" 我创建 ", -1)
                    ])]),
                    _: 1
                  })) : (t(), n(e(f), {
                    key: 1,
                    variant: "outline",
                    class: "text-[10px]"
                  }, {
                    default: l(() => [...o[5] || (o[5] = [
                      d("收藏", -1)
                    ])]),
                    _: 1
                  }))
                ])
              ])
            ], 8, W);
          }), 128))
        ]))
      ])
    ]));
  }
}, fe = /* @__PURE__ */ A(re, [["__scopeId", "data-v-071d8619"]]);
export {
  fe as default
};
