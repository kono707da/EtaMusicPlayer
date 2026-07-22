import { c as l, a as o, b as i, u as t, d as c, w as _, e as v, i as xe, f as d, F as O, r as Q, s as _e, j as ke, o as n, t as x, n as N, k as Y, l as T } from "./api-CJ1Y_yWo.js";
import { u as ge } from "./store-CKZLSlHE.js";
import { a as we, w as B } from "./runtime-dom.esm-bundler-1Zj72-Aa.js";
const be = { class: "flex h-full flex-col gap-3" }, Ce = { class: "flex items-center justify-between gap-3" }, Se = { class: "flex items-center gap-2" }, $e = { class: "flex items-center gap-2" }, qe = { class: "flex items-center gap-2" }, Ve = { class: "relative flex-1 max-w-2xl" }, ze = { class: "flex-1 min-h-0 overflow-auto" }, Pe = {
  key: 0,
  class: "flex h-full items-center justify-center text-muted-foreground"
}, je = {
  key: 1,
  class: "flex flex-col gap-4"
}, Ie = { class: "flex items-center gap-2 text-sm text-muted-foreground" }, Me = {
  key: 0,
  class: "flex items-center text-muted-foreground text-sm"
}, Ne = {
  key: 1,
  class: "text-sm text-muted-foreground"
}, Te = {
  key: 2,
  class: "flex flex-wrap gap-2"
}, Be = { class: "text-muted-foreground mr-1.5" }, De = {
  key: 3,
  class: "flex flex-col gap-1 pb-4"
}, Re = ["onDblclick"], Le = { class: "w-8 h-8 flex items-center justify-center shrink-0" }, Ae = ["onClick"], Fe = {
  key: 2,
  class: "text-sm text-muted-foreground group-hover:hidden"
}, He = ["src", "alt"], Ke = {
  key: 1,
  class: "h-10 w-10 rounded bg-muted flex items-center justify-center shrink-0"
}, Ue = { class: "flex-1 min-w-0 flex flex-col gap-0.5" }, Ee = ["title"], We = {
  key: 0,
  class: "text-muted-foreground text-xs ml-1"
}, Xe = { class: "text-xs text-muted-foreground truncate" }, Ge = {
  key: 0,
  class: "mx-1"
}, Je = {
  key: 1,
  class: "truncate"
}, Oe = { class: "text-xs text-muted-foreground shrink-0 hidden sm:block" }, Qe = { class: "flex items-center gap-1 shrink-0" }, st = {
  __name: "NeteaseSearchView",
  setup(Ye) {
    const { ref: k, computed: D, onMounted: Z, watch: ee } = window.__etamusic.vue, { useRoute: te, useRouter: se } = window.__etamusic.vueRouter, {
      Search: R,
      Music: L,
      Loader2: g,
      Play: A,
      Plus: ae,
      Flame: ne,
      X: F,
      AlertCircle: le,
      Download: H
    } = window.__etamusic.icons, { Input: re, Button: w, Badge: K, Empty: oe, useToast: ie } = window.__etamusic.ui, { usePlayerStore: ce } = window.__etamusic.stores, q = te(), j = se(), r = ie(), V = ce(), U = ge(), f = k(q.query.q || ""), u = k(!1), m = k({ songs: [], songCount: 0 }), z = k([]), I = k(!1), C = D(() => q.query.q || ""), p = k(/* @__PURE__ */ new Set()), S = k(/* @__PURE__ */ new Set()), b = D(() => m.value.songs.length > 0);
    async function ue() {
      var s;
      I.value = !0;
      try {
        const e = await ke();
        z.value = (((s = e == null ? void 0 : e.result) == null ? void 0 : s.hots) || []).slice(0, 20);
      } catch {
        z.value = [];
      } finally {
        I.value = !1;
      }
    }
    async function M() {
      var e, a;
      const s = C.value;
      if (!s) {
        m.value = { songs: [], songCount: 0 };
        return;
      }
      u.value = !0;
      try {
        const y = (Number(q.query.page) || 1) - 1, h = await _e(s, 1, 50, Math.max(0, y) * 50);
        m.value = {
          songs: ((e = h == null ? void 0 : h.result) == null ? void 0 : e.songs) || [],
          songCount: ((a = h == null ? void 0 : h.result) == null ? void 0 : a.songCount) || 0
        };
      } catch (y) {
        r.error("搜索失败：" + (y.message || "未知错误")), m.value = { songs: [], songCount: 0 };
      } finally {
        u.value = !1;
      }
    }
    function E() {
      const s = f.value.trim();
      if (!s) {
        r.error("请输入搜索关键词");
        return;
      }
      if (s === C.value) {
        M();
        return;
      }
      j.push({ path: "/netease/search", query: { q: s, page: 1 } });
    }
    function de(s) {
      f.value = s, j.push({ path: "/netease/search", query: { q: s, page: 1 } });
    }
    function fe() {
      f.value = "", j.push({ path: "/netease/search" });
    }
    async function W(s) {
      if (!p.value.has(s.id)) {
        p.value.add(s.id);
        try {
          const e = await T([s], "standard");
          if (e.length === 0) {
            r.error(`「${s.name}」无可用播放源（VIP/版权限制）`);
            return;
          }
          V.playTracks(e, 0), r.success(`正在播放：${s.name}`);
        } catch (e) {
          r.error("播放失败：" + (e.message || "未知错误"));
        } finally {
          p.value.delete(s.id);
        }
      }
    }
    async function me() {
      if (!b.value) return;
      const s = m.value.songs.slice(0, 100);
      u.value = !0;
      try {
        const e = await T(s, "standard");
        if (e.length === 0) {
          r.error("当前搜索结果无可用播放源（VIP/版权限制）");
          return;
        }
        V.playTracks(e, 0), r.success(`已加入播放队列：${e.length} 首`);
      } catch (e) {
        r.error("加入播放队列失败：" + (e.message || "未知错误"));
      } finally {
        u.value = !1;
      }
    }
    async function he(s) {
      if (!p.value.has(s.id)) {
        p.value.add(s.id);
        try {
          const e = await T([s], "standard");
          if (e.length === 0) {
            r.error(`「${s.name}」无可用播放源（VIP/版权限制）`);
            return;
          }
          V.appendTracks(e), r.success(`已加入队列：${s.name}`);
        } catch (e) {
          r.error("加入队列失败：" + (e.message || "未知错误"));
        } finally {
          p.value.delete(s.id);
        }
      }
    }
    async function pe(s) {
      if (!S.value.has(s.id)) {
        S.value.add(s.id);
        try {
          const e = await Y([s.id], { level: "exhigh" });
          r.success(e.message || "下载任务已创建");
        } catch (e) {
          r.error("下载失败：" + (e.message || "未知错误"));
        } finally {
          S.value.delete(s.id);
        }
      }
    }
    async function ye() {
      if (!b.value) return;
      const s = m.value.songs.slice(0, 100);
      u.value = !0;
      try {
        const e = s.map((y) => y.id), a = await Y(e, { level: "exhigh" });
        r.success(a.message || "下载任务已创建");
      } catch (e) {
        r.error("下载失败：" + (e.message || "未知错误"));
      } finally {
        u.value = !1;
      }
    }
    function ve(s) {
      if (!s || s <= 0) return "--:--";
      const e = Math.floor(s / 60), a = Math.floor(s % 60);
      return `${e}:${String(a).padStart(2, "0")}`;
    }
    function P(s) {
      const e = V.currentTrack;
      return e && e.id === s.id && e.__source === "netease";
    }
    return ee(
      () => q.query,
      (s) => {
        s.q !== f.value && (f.value = s.q || ""), s.q ? M() : m.value = { songs: [], songCount: 0 };
      },
      { deep: !0 }
    ), Z(() => {
      U.loaded || U.load(), C.value ? M() : ue();
    }), (s, e) => (n(), l("div", be, [
      o("div", Ce, [
        o("div", Se, [
          i(t(L), { class: "h-5 w-5 text-primary" }),
          e[2] || (e[2] = o("h2", { class: "text-lg font-semibold tracking-tight" }, "网易云搜索", -1)),
          t(m).songCount ? (n(), c(t(K), {
            key: 0,
            variant: "outline",
            class: "text-muted-foreground"
          }, {
            default: _(() => [
              d(" 共 " + x(t(m).songCount) + " 首 ", 1)
            ]),
            _: 1
          })) : v("", !0)
        ]),
        o("div", $e, [
          t(b) ? (n(), c(t(w), {
            key: 0,
            variant: "secondary",
            size: "sm",
            disabled: t(u),
            onClick: ye
          }, {
            default: _(() => [
              i(t(H), { class: "h-4 w-4" }),
              e[3] || (e[3] = d(" 下载全部 ", -1))
            ]),
            _: 1
          }, 8, ["disabled"])) : v("", !0),
          t(b) ? (n(), c(t(w), {
            key: 1,
            variant: "gold",
            size: "sm",
            disabled: t(u),
            onClick: me
          }, {
            default: _(() => [
              t(u) ? (n(), c(t(g), {
                key: 0,
                class: "h-4 w-4 animate-spin"
              })) : (n(), c(t(A), {
                key: 1,
                class: "h-4 w-4"
              })),
              e[4] || (e[4] = d(" 播放全部 ", -1))
            ]),
            _: 1
          }, 8, ["disabled"])) : v("", !0)
        ])
      ]),
      o("div", qe, [
        o("div", Ve, [
          i(t(R), { class: "pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" }),
          i(t(re), {
            modelValue: t(f),
            "onUpdate:modelValue": e[0] || (e[0] = (a) => xe(f) ? f.value = a : null),
            placeholder: "搜索歌曲、歌手、专辑...",
            class: "h-9 pl-9 pr-9",
            onKeyup: we(E, ["enter"])
          }, null, 8, ["modelValue"]),
          t(f) ? (n(), l("button", {
            key: 0,
            class: "absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground",
            onClick: e[1] || (e[1] = (a) => f.value = "")
          }, [
            i(t(F), { class: "h-4 w-4" })
          ])) : v("", !0)
        ]),
        i(t(w), {
          variant: "gold",
          size: "sm",
          disabled: t(u),
          onClick: E
        }, {
          default: _(() => [
            t(u) ? (n(), c(t(g), {
              key: 0,
              class: "h-4 w-4 animate-spin"
            })) : (n(), c(t(R), {
              key: 1,
              class: "h-4 w-4"
            })),
            e[5] || (e[5] = d(" 搜索 ", -1))
          ]),
          _: 1
        }, 8, ["disabled"]),
        t(C) ? (n(), c(t(w), {
          key: 0,
          variant: "ghost",
          size: "sm",
          onClick: fe
        }, {
          default: _(() => [
            i(t(F), { class: "h-4 w-4" }),
            e[6] || (e[6] = d(" 清空 ", -1))
          ]),
          _: 1
        })) : v("", !0)
      ]),
      o("div", ze, [
        t(u) && !t(b) ? (n(), l("div", Pe, [
          i(t(g), { class: "mr-2 h-5 w-5 animate-spin" }),
          e[7] || (e[7] = d(" 搜索中... ", -1))
        ])) : t(C) ? t(b) ? (n(), l("div", De, [
          (n(!0), l(O, null, Q(t(m).songs, (a, y) => {
            var h, X, G, J;
            return n(), l("div", {
              key: a.id,
              class: N(["group flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50", { "bg-primary/10": P(a) }]),
              onDblclick: ($) => W(a)
            }, [
              o("div", Le, [
                t(p).has(a.id) ? (n(), c(t(g), {
                  key: 0,
                  class: "h-4 w-4 animate-spin text-muted-foreground"
                })) : (n(), l("button", {
                  key: 1,
                  class: N(["opacity-0 group-hover:opacity-100 transition-opacity", { "!opacity-100": P(a) }]),
                  onClick: B(($) => W(a), ["stop"])
                }, [
                  i(t(A), {
                    class: N(["h-4 w-4", P(a) ? "text-primary" : "text-foreground"])
                  }, null, 8, ["class"])
                ], 10, Ae)),
                !t(p).has(a.id) && !P(a) ? (n(), l("span", Fe, x(y + 1), 1)) : v("", !0)
              ]),
              (h = a.al) != null && h.picUrl ? (n(), l("img", {
                key: 0,
                src: a.al.picUrl,
                alt: a.name,
                class: "h-10 w-10 rounded object-cover shrink-0",
                referrerpolicy: "no-referrer",
                loading: "lazy"
              }, null, 8, He)) : (n(), l("div", Ke, [
                i(t(L), { class: "h-4 w-4 text-muted-foreground" })
              ])),
              o("div", Ue, [
                o("div", {
                  class: "text-sm font-medium truncate",
                  title: a.name
                }, [
                  d(x(a.name) + " ", 1),
                  (X = a.alia) != null && X.length ? (n(), l("span", We, " (" + x(a.alia[0]) + ") ", 1)) : v("", !0)
                ], 8, Ee),
                o("div", Xe, [
                  d(x((a.ar || []).map(($) => $.name).join(" / ") || "未知艺术家") + " ", 1),
                  (G = a.al) != null && G.name ? (n(), l("span", Ge, "·")) : v("", !0),
                  (J = a.al) != null && J.name ? (n(), l("span", Je, x(a.al.name), 1)) : v("", !0)
                ])
              ]),
              o("div", Oe, x(ve(Math.floor((a.dt || 0) / 1e3))), 1),
              o("div", Qe, [
                i(t(w), {
                  variant: "ghost",
                  size: "sm",
                  class: "h-8 w-8 p-0",
                  disabled: t(S).has(a.id),
                  title: "下载",
                  onClick: B(($) => pe(a), ["stop"])
                }, {
                  default: _(() => [
                    t(S).has(a.id) ? (n(), c(t(g), {
                      key: 0,
                      class: "h-4 w-4 animate-spin"
                    })) : (n(), c(t(H), {
                      key: 1,
                      class: "h-4 w-4"
                    }))
                  ]),
                  _: 2
                }, 1032, ["disabled", "onClick"]),
                i(t(w), {
                  variant: "ghost",
                  size: "sm",
                  class: "h-8 w-8 p-0",
                  disabled: t(p).has(a.id),
                  title: "加入队列",
                  onClick: B(($) => he(a), ["stop"])
                }, {
                  default: _(() => [
                    i(t(ae), { class: "h-4 w-4" })
                  ]),
                  _: 1
                }, 8, ["disabled", "onClick"])
              ])
            ], 42, Re);
          }), 128))
        ])) : (n(), c(t(oe), {
          key: 2,
          icon: t(le),
          title: "没有找到相关歌曲",
          description: "试试其他关键词",
          class: "h-full"
        }, null, 8, ["icon"])) : (n(), l("div", je, [
          o("div", Ie, [
            i(t(ne), { class: "h-4 w-4 text-primary" }),
            e[8] || (e[8] = d(" 热门搜索 ", -1))
          ]),
          t(I) ? (n(), l("div", Me, [
            i(t(g), { class: "mr-2 h-4 w-4 animate-spin" }),
            e[9] || (e[9] = d(" 加载中... ", -1))
          ])) : t(z).length === 0 ? (n(), l("div", Ne, " 暂无热搜 ")) : (n(), l("div", Te, [
            (n(!0), l(O, null, Q(t(z), (a, y) => (n(), c(t(K), {
              key: a.first,
              variant: "outline",
              class: "cursor-pointer px-3 py-1.5 text-sm hover:bg-accent",
              onClick: (h) => de(a.first)
            }, {
              default: _(() => [
                o("span", Be, x(y + 1) + ".", 1),
                d(" " + x(a.first), 1)
              ]),
              _: 2
            }, 1032, ["onClick"]))), 128))
          ]))
        ]))
      ])
    ]));
  }
};
export {
  st as default
};
