import { c as i, a as o, b as r, w as f, u as s, e as v, F as X, r as q, l as A, o as l, n as z, t as d, d as c, j as G, f as D, k as H, m as J } from "./api-BBDGHqfl.js";
const O = { class: "max-w-4xl mx-auto p-6 space-y-4" }, Q = { class: "flex items-center justify-between" }, W = { class: "flex gap-2" }, Y = {
  key: 0,
  class: "flex items-center gap-2 text-muted-foreground py-8 justify-center"
}, Z = {
  key: 1,
  class: "text-center text-muted-foreground py-12"
}, ee = {
  key: 2,
  class: "space-y-3"
}, te = { class: "flex items-start justify-between gap-3" }, se = { class: "flex-1 min-w-0" }, ne = { class: "flex items-center gap-2 mb-1" }, oe = { class: "font-medium truncate" }, ae = { class: "text-sm text-muted-foreground space-y-0.5" }, le = { key: 0 }, ie = { key: 1 }, re = { class: "flex items-center gap-3" }, de = { key: 0 }, ce = {
  key: 2,
  class: "mt-2"
}, ue = { class: "w-full bg-secondary rounded-full h-1.5" }, me = { class: "text-xs" }, pe = {
  key: 3,
  class: "text-red-500 text-xs mt-1"
}, _e = { class: "flex gap-1 shrink-0" }, xe = {
  __name: "BiliTasksView",
  setup(fe) {
    const { ref: g, onMounted: T, onUnmounted: F } = window.__etamusic.vue, { useRouter: N } = window.__etamusic.vueRouter, { Button: u, useToast: V } = window.__etamusic.ui, { Download: h, Trash2: j, X: M, Loader2: S, RefreshCw: $, Music: L } = window.__etamusic.icons, y = N(), m = V(), x = g([]), R = g(0), U = g(1), p = g(!1);
    let w = null;
    const b = {
      pending: { label: "等待中", color: "text-yellow-500" },
      running: { label: "下载中", color: "text-blue-500" },
      completed: { label: "已完成", color: "text-green-500" },
      failed: { label: "失败", color: "text-red-500" },
      canceled: { label: "已取消", color: "text-gray-500" },
      partial: { label: "部分完成", color: "text-orange-500" }
    };
    async function _() {
      var n, t;
      p.value = !0;
      try {
        const e = await A(U.value, 20);
        x.value = e.items || [], R.value = e.total || 0;
      } catch (e) {
        m.error("加载失败", ((t = (n = e == null ? void 0 : e.response) == null ? void 0 : n.data) == null ? void 0 : t.detail) || e.message, e);
      } finally {
        p.value = !1;
      }
    }
    async function I(n) {
      var t, e;
      try {
        await H(n), m.success("已取消"), _();
      } catch (a) {
        m.error("取消失败", ((e = (t = a == null ? void 0 : a.response) == null ? void 0 : t.data) == null ? void 0 : e.detail) || a.message, a);
      }
    }
    async function P(n) {
      var t, e;
      try {
        await J(n), m.success("已删除"), _();
      } catch (a) {
        m.error("删除失败", ((e = (t = a == null ? void 0 : a.response) == null ? void 0 : t.data) == null ? void 0 : e.detail) || a.message, a);
      }
    }
    function k(n) {
      return n ? n < 1024 ? n + " B" : n < 1024 * 1024 ? (n / 1024).toFixed(1) + " KB" : (n / 1024 / 1024).toFixed(1) + " MB" : "-";
    }
    function E(n) {
      return n ? new Date(n).toLocaleString("zh-CN") : "-";
    }
    return T(() => {
      _(), w = setInterval(_, 5e3);
    }), F(() => {
      w && clearInterval(w);
    }), (n, t) => (l(), i("div", O, [
      o("div", Q, [
        t[4] || (t[4] = o("h1", { class: "text-2xl font-bold" }, "B站下载任务", -1)),
        o("div", W, [
          r(s(u), {
            variant: "outline",
            size: "sm",
            onClick: _,
            disabled: s(p)
          }, {
            default: f(() => [
              r(s($), {
                class: z(["w-4 h-4 mr-1", { "animate-spin": s(p) }])
              }, null, 8, ["class"]),
              t[2] || (t[2] = v(" 刷新 ", -1))
            ]),
            _: 1
          }, 8, ["disabled"]),
          r(s(u), {
            size: "sm",
            onClick: t[0] || (t[0] = (e) => s(y).push("/bili"))
          }, {
            default: f(() => [
              r(s(h), { class: "w-4 h-4 mr-1" }),
              t[3] || (t[3] = v(" 新建下载 ", -1))
            ]),
            _: 1
          })
        ])
      ]),
      s(p) && s(x).length === 0 ? (l(), i("div", Y, [
        r(s(S), { class: "w-5 h-5 animate-spin" }),
        t[5] || (t[5] = v(" 加载中... ", -1))
      ])) : s(x).length === 0 ? (l(), i("div", Z, [
        r(s(L), { class: "w-12 h-12 mx-auto mb-3 opacity-30" }),
        t[7] || (t[7] = o("p", null, "暂无下载任务", -1)),
        r(s(u), {
          variant: "outline",
          class: "mt-4",
          onClick: t[1] || (t[1] = (e) => s(y).push("/bili"))
        }, {
          default: f(() => [
            r(s(h), { class: "w-4 h-4 mr-1" }),
            t[6] || (t[6] = v(" 从B站下载音频 ", -1))
          ]),
          _: 1
        })
      ])) : (l(), i("div", ee, [
        (l(!0), i(X, null, q(s(x), (e) => {
          var a, C, B;
          return l(), i("div", {
            key: e.id,
            class: "border rounded-lg p-4 hover:bg-accent/50 transition-colors"
          }, [
            o("div", te, [
              o("div", se, [
                o("div", ne, [
                  o("span", oe, d(e.title || e.bvid), 1),
                  o("span", {
                    class: z([(a = b[e.status]) == null ? void 0 : a.color, "text-xs font-medium"])
                  }, d(((C = b[e.status]) == null ? void 0 : C.label) || e.status), 3)
                ]),
                o("div", ae, [
                  e.upper_name ? (l(), i("div", le, "UP主: " + d(e.upper_name), 1)) : c("", !0),
                  e.page_title ? (l(), i("div", ie, "分P: " + d(e.page_title), 1)) : c("", !0),
                  o("div", re, [
                    o("span", null, d((B = e.output_format) == null ? void 0 : B.toUpperCase()), 1),
                    e.file_size ? (l(), i("span", de, d(k(e.file_size)), 1)) : c("", !0),
                    o("span", null, d(E(e.created_at)), 1)
                  ]),
                  e.status === "running" ? (l(), i("div", ce, [
                    o("div", ue, [
                      o("div", {
                        class: "bg-primary h-1.5 rounded-full transition-all",
                        style: G({ width: e.progress + "%" })
                      }, null, 4)
                    ]),
                    o("span", me, d(e.progress.toFixed(1)) + "%", 1)
                  ])) : c("", !0),
                  e.error_message ? (l(), i("div", pe, d(e.error_message), 1)) : c("", !0)
                ])
              ]),
              o("div", _e, [
                e.status === "pending" || e.status === "running" ? (l(), D(s(u), {
                  key: 0,
                  variant: "ghost",
                  size: "icon",
                  onClick: (K) => I(e.id),
                  title: "取消"
                }, {
                  default: f(() => [
                    r(s(M), { class: "w-4 h-4" })
                  ]),
                  _: 1
                }, 8, ["onClick"])) : c("", !0),
                e.status !== "pending" && e.status !== "running" ? (l(), D(s(u), {
                  key: 1,
                  variant: "ghost",
                  size: "icon",
                  onClick: (K) => P(e.id),
                  title: "删除"
                }, {
                  default: f(() => [
                    r(s(j), { class: "w-4 h-4" })
                  ]),
                  _: 1
                }, 8, ["onClick"])) : c("", !0)
              ])
            ])
          ]);
        }), 128))
      ]))
    ]));
  }
};
export {
  xe as default
};
