import { c as n, a as o, b as l, u as t, d, w as k, e as v, i as me, f, F as X, r as G, s as he, j as pe, o as r, t as y, n as T, k as z } from "./api-D4goXXVb.js";
import { u as ye } from "./store-C7cC6z1j.js";
import { a as ve, w as J } from "./runtime-dom.esm-bundler-fg28wYCK.js";
const xe = { class: "flex h-full flex-col gap-3" }, _e = { class: "flex items-center justify-between gap-3" }, ke = { class: "flex items-center gap-2" }, ge = { class: "flex items-center gap-2" }, we = { class: "relative flex-1 max-w-2xl" }, be = { class: "flex-1 min-h-0 overflow-auto" }, Ce = {
  key: 0,
  class: "flex h-full items-center justify-center text-muted-foreground"
}, Se = {
  key: 1,
  class: "flex flex-col gap-4"
}, $e = { class: "flex items-center gap-2 text-sm text-muted-foreground" }, qe = {
  key: 0,
  class: "flex items-center text-muted-foreground text-sm"
}, Ve = {
  key: 1,
  class: "text-sm text-muted-foreground"
}, Pe = {
  key: 2,
  class: "flex flex-wrap gap-2"
}, je = { class: "text-muted-foreground mr-1.5" }, Me = {
  key: 3,
  class: "flex flex-col gap-1 pb-4"
}, Ne = ["onDblclick"], Te = { class: "w-8 h-8 flex items-center justify-center shrink-0" }, ze = ["onClick"], Be = {
  key: 2,
  class: "text-sm text-muted-foreground group-hover:hidden"
}, Ie = ["src", "alt"], Re = {
  key: 1,
  class: "h-10 w-10 rounded bg-muted flex items-center justify-center shrink-0"
}, De = { class: "flex-1 min-w-0 flex flex-col gap-0.5" }, Le = ["title"], Fe = {
  key: 0,
  class: "text-muted-foreground text-xs ml-1"
}, He = { class: "text-xs text-muted-foreground truncate" }, Ke = {
  key: 0,
  class: "mx-1"
}, Ue = {
  key: 1,
  class: "truncate"
}, Ae = { class: "text-xs text-muted-foreground shrink-0 hidden sm:block" }, Ee = { class: "flex items-center gap-1 shrink-0" }, Oe = {
  __name: "NeteaseSearchView",
  setup(We) {
    const { ref: _, computed: B, onMounted: O, watch: Q } = window.__etamusic.vue, { useRoute: Y, useRouter: Z } = window.__etamusic.vueRouter, {
      Search: I,
      Music: R,
      Loader2: g,
      Play: D,
      Plus: ee,
      Flame: te,
      X: L,
      AlertCircle: se
    } = window.__etamusic.icons, { Input: ae, Button: b, Badge: F, Empty: re, useToast: ne } = window.__etamusic.ui, { usePlayerStore: oe } = window.__etamusic.stores, C = Y(), j = Z(), i = ne(), S = oe(), H = ye(), c = _(C.query.q || ""), m = _(!1), h = _({ songs: [], songCount: 0 }), $ = _([]), M = _(!1), w = B(() => C.query.q || ""), p = _(/* @__PURE__ */ new Set()), q = B(() => h.value.songs.length > 0);
    async function le() {
      var s;
      M.value = !0;
      try {
        const e = await pe();
        $.value = (((s = e == null ? void 0 : e.result) == null ? void 0 : s.hots) || []).slice(0, 20);
      } catch {
        $.value = [];
      } finally {
        M.value = !1;
      }
    }
    async function N() {
      var e, a;
      const s = w.value;
      if (!s) {
        h.value = { songs: [], songCount: 0 };
        return;
      }
      m.value = !0;
      try {
        const x = (Number(C.query.page) || 1) - 1, u = await he(s, 1, 50, Math.max(0, x) * 50);
        h.value = {
          songs: ((e = u == null ? void 0 : u.result) == null ? void 0 : e.songs) || [],
          songCount: ((a = u == null ? void 0 : u.result) == null ? void 0 : a.songCount) || 0
        };
      } catch (x) {
        i.error("搜索失败：" + (x.message || "未知错误")), h.value = { songs: [], songCount: 0 };
      } finally {
        m.value = !1;
      }
    }
    function K() {
      const s = c.value.trim();
      if (!s) {
        i.error("请输入搜索关键词");
        return;
      }
      if (s === w.value) {
        N();
        return;
      }
      j.push({ path: "/netease/search", query: { q: s, page: 1 } });
    }
    function ie(s) {
      c.value = s, j.push({ path: "/netease/search", query: { q: s, page: 1 } });
    }
    function ce() {
      c.value = "", j.push({ path: "/netease/search" });
    }
    async function U(s) {
      if (!p.value.has(s.id)) {
        p.value.add(s.id);
        try {
          const e = await z([s], "standard");
          if (e.length === 0) {
            i.error(`「${s.name}」无可用播放源（VIP/版权限制）`);
            return;
          }
          S.playTracks(e, 0), i.success(`正在播放：${s.name}`);
        } catch (e) {
          i.error("播放失败：" + (e.message || "未知错误"));
        } finally {
          p.value.delete(s.id);
        }
      }
    }
    async function ue() {
      if (!q.value) return;
      const s = h.value.songs.slice(0, 100);
      m.value = !0;
      try {
        const e = await z(s, "standard");
        if (e.length === 0) {
          i.error("当前搜索结果无可用播放源（VIP/版权限制）");
          return;
        }
        S.playTracks(e, 0), i.success(`已加入播放队列：${e.length} 首`);
      } catch (e) {
        i.error("加入播放队列失败：" + (e.message || "未知错误"));
      } finally {
        m.value = !1;
      }
    }
    async function de(s) {
      if (!p.value.has(s.id)) {
        p.value.add(s.id);
        try {
          const e = await z([s], "standard");
          if (e.length === 0) {
            i.error(`「${s.name}」无可用播放源（VIP/版权限制）`);
            return;
          }
          S.appendTracks(e), i.success(`已加入队列：${s.name}`);
        } catch (e) {
          i.error("加入队列失败：" + (e.message || "未知错误"));
        } finally {
          p.value.delete(s.id);
        }
      }
    }
    function fe(s) {
      if (!s || s <= 0) return "--:--";
      const e = Math.floor(s / 60), a = Math.floor(s % 60);
      return `${e}:${String(a).padStart(2, "0")}`;
    }
    function V(s) {
      const e = S.currentTrack;
      return e && e.id === s.id && e.__source === "netease";
    }
    return Q(
      () => C.query,
      (s) => {
        s.q !== c.value && (c.value = s.q || ""), s.q ? N() : h.value = { songs: [], songCount: 0 };
      },
      { deep: !0 }
    ), O(() => {
      H.loaded || H.load(), w.value ? N() : le();
    }), (s, e) => (r(), n("div", xe, [
      o("div", _e, [
        o("div", ke, [
          l(t(R), { class: "h-5 w-5 text-primary" }),
          e[2] || (e[2] = o("h2", { class: "text-lg font-semibold tracking-tight" }, "网易云搜索", -1)),
          t(h).songCount ? (r(), d(t(F), {
            key: 0,
            variant: "outline",
            class: "text-muted-foreground"
          }, {
            default: k(() => [
              f(" 共 " + y(t(h).songCount) + " 首 ", 1)
            ]),
            _: 1
          })) : v("", !0)
        ]),
        t(q) ? (r(), d(t(b), {
          key: 0,
          variant: "gold",
          size: "sm",
          disabled: t(m),
          onClick: ue
        }, {
          default: k(() => [
            t(m) ? (r(), d(t(g), {
              key: 0,
              class: "h-4 w-4 animate-spin"
            })) : (r(), d(t(D), {
              key: 1,
              class: "h-4 w-4"
            })),
            e[3] || (e[3] = f(" 播放全部 ", -1))
          ]),
          _: 1
        }, 8, ["disabled"])) : v("", !0)
      ]),
      o("div", ge, [
        o("div", we, [
          l(t(I), { class: "pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" }),
          l(t(ae), {
            modelValue: t(c),
            "onUpdate:modelValue": e[0] || (e[0] = (a) => me(c) ? c.value = a : null),
            placeholder: "搜索歌曲、歌手、专辑...",
            class: "h-9 pl-9 pr-9",
            onKeyup: ve(K, ["enter"])
          }, null, 8, ["modelValue"]),
          t(c) ? (r(), n("button", {
            key: 0,
            class: "absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground",
            onClick: e[1] || (e[1] = (a) => c.value = "")
          }, [
            l(t(L), { class: "h-4 w-4" })
          ])) : v("", !0)
        ]),
        l(t(b), {
          variant: "gold",
          size: "sm",
          disabled: t(m),
          onClick: K
        }, {
          default: k(() => [
            t(m) ? (r(), d(t(g), {
              key: 0,
              class: "h-4 w-4 animate-spin"
            })) : (r(), d(t(I), {
              key: 1,
              class: "h-4 w-4"
            })),
            e[4] || (e[4] = f(" 搜索 ", -1))
          ]),
          _: 1
        }, 8, ["disabled"]),
        t(w) ? (r(), d(t(b), {
          key: 0,
          variant: "ghost",
          size: "sm",
          onClick: ce
        }, {
          default: k(() => [
            l(t(L), { class: "h-4 w-4" }),
            e[5] || (e[5] = f(" 清空 ", -1))
          ]),
          _: 1
        })) : v("", !0)
      ]),
      o("div", be, [
        t(m) && !t(q) ? (r(), n("div", Ce, [
          l(t(g), { class: "mr-2 h-5 w-5 animate-spin" }),
          e[6] || (e[6] = f(" 搜索中... ", -1))
        ])) : t(w) ? t(q) ? (r(), n("div", Me, [
          (r(!0), n(X, null, G(t(h).songs, (a, x) => {
            var u, A, E, W;
            return r(), n("div", {
              key: a.id,
              class: T(["group flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50", { "bg-primary/10": V(a) }]),
              onDblclick: (P) => U(a)
            }, [
              o("div", Te, [
                t(p).has(a.id) ? (r(), d(t(g), {
                  key: 0,
                  class: "h-4 w-4 animate-spin text-muted-foreground"
                })) : (r(), n("button", {
                  key: 1,
                  class: T(["opacity-0 group-hover:opacity-100 transition-opacity", { "!opacity-100": V(a) }]),
                  onClick: J((P) => U(a), ["stop"])
                }, [
                  l(t(D), {
                    class: T(["h-4 w-4", V(a) ? "text-primary" : "text-foreground"])
                  }, null, 8, ["class"])
                ], 10, ze)),
                !t(p).has(a.id) && !V(a) ? (r(), n("span", Be, y(x + 1), 1)) : v("", !0)
              ]),
              (u = a.al) != null && u.picUrl ? (r(), n("img", {
                key: 0,
                src: a.al.picUrl,
                alt: a.name,
                class: "h-10 w-10 rounded object-cover shrink-0",
                referrerpolicy: "no-referrer",
                loading: "lazy"
              }, null, 8, Ie)) : (r(), n("div", Re, [
                l(t(R), { class: "h-4 w-4 text-muted-foreground" })
              ])),
              o("div", De, [
                o("div", {
                  class: "text-sm font-medium truncate",
                  title: a.name
                }, [
                  f(y(a.name) + " ", 1),
                  (A = a.alia) != null && A.length ? (r(), n("span", Fe, " (" + y(a.alia[0]) + ") ", 1)) : v("", !0)
                ], 8, Le),
                o("div", He, [
                  f(y((a.ar || []).map((P) => P.name).join(" / ") || "未知艺术家") + " ", 1),
                  (E = a.al) != null && E.name ? (r(), n("span", Ke, "·")) : v("", !0),
                  (W = a.al) != null && W.name ? (r(), n("span", Ue, y(a.al.name), 1)) : v("", !0)
                ])
              ]),
              o("div", Ae, y(fe(Math.floor((a.dt || 0) / 1e3))), 1),
              o("div", Ee, [
                l(t(b), {
                  variant: "ghost",
                  size: "sm",
                  class: "h-8 w-8 p-0",
                  disabled: t(p).has(a.id),
                  title: "加入队列",
                  onClick: J((P) => de(a), ["stop"])
                }, {
                  default: k(() => [
                    l(t(ee), { class: "h-4 w-4" })
                  ]),
                  _: 1
                }, 8, ["disabled", "onClick"])
              ])
            ], 42, Ne);
          }), 128))
        ])) : (r(), d(t(re), {
          key: 2,
          icon: t(se),
          title: "没有找到相关歌曲",
          description: "试试其他关键词",
          class: "h-full"
        }, null, 8, ["icon"])) : (r(), n("div", Se, [
          o("div", $e, [
            l(t(te), { class: "h-4 w-4 text-primary" }),
            e[7] || (e[7] = f(" 热门搜索 ", -1))
          ]),
          t(M) ? (r(), n("div", qe, [
            l(t(g), { class: "mr-2 h-4 w-4 animate-spin" }),
            e[8] || (e[8] = f(" 加载中... ", -1))
          ])) : t($).length === 0 ? (r(), n("div", Ve, " 暂无热搜 ")) : (r(), n("div", Pe, [
            (r(!0), n(X, null, G(t($), (a, x) => (r(), d(t(F), {
              key: a.first,
              variant: "outline",
              class: "cursor-pointer px-3 py-1.5 text-sm hover:bg-accent",
              onClick: (u) => ie(a.first)
            }, {
              default: k(() => [
                o("span", je, y(x + 1) + ".", 1),
                f(" " + y(a.first), 1)
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
  Oe as default
};
