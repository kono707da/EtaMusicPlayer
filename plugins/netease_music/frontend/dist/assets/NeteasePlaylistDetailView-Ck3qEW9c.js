import { c as l, a as i, b as c, w as v, u as e, f, d as _, F as H, t as d, e as y, r as ce, y as ue, o as a, n as $, k as T } from "./api-D4goXXVb.js";
import { _ as de } from "./_plugin-vue_export-helper-CHgC5LLL.js";
import { w as J } from "./runtime-dom.esm-bundler-fg28wYCK.js";
const fe = { class: "flex h-full flex-col gap-3" }, me = { class: "flex items-center gap-2" }, pe = {
  key: 0,
  class: "flex-1 flex items-center justify-center text-muted-foreground"
}, he = { class: "flex gap-4 p-4 rounded-lg border border-border bg-card/40" }, _e = ["src", "alt"], ye = {
  key: 1,
  class: "h-32 w-32 rounded-lg bg-muted flex items-center justify-center shrink-0"
}, xe = { class: "flex-1 min-w-0 flex flex-col gap-2" }, ve = { class: "flex items-center gap-2 flex-wrap" }, ke = { class: "text-xl font-semibold truncate" }, we = { class: "flex items-center gap-3 text-sm text-muted-foreground flex-wrap" }, ge = { class: "flex items-center gap-1" }, be = {
  key: 0,
  class: "flex items-center gap-1"
}, Ce = {
  key: 0,
  class: "text-xs text-muted-foreground line-clamp-2"
}, Pe = { class: "flex items-center gap-2 mt-auto" }, Ie = { class: "flex-1 min-h-0 overflow-auto" }, Se = {
  key: 1,
  class: "flex flex-col gap-1 pb-4"
}, $e = ["onDblclick"], Te = { class: "w-8 h-8 flex items-center justify-center shrink-0" }, Ve = ["onClick"], je = {
  key: 2,
  class: "text-sm text-muted-foreground group-hover:hidden"
}, Be = ["src", "alt"], De = {
  key: 1,
  class: "h-10 w-10 rounded bg-muted flex items-center justify-center shrink-0"
}, Me = { class: "flex-1 min-w-0 flex flex-col gap-0.5" }, Ne = ["title"], ze = {
  key: 0,
  class: "text-muted-foreground text-xs ml-1"
}, Ae = { class: "text-xs text-muted-foreground truncate" }, Fe = {
  key: 0,
  class: "mx-1"
}, Le = {
  key: 1,
  class: "truncate"
}, Ue = { class: "text-xs text-muted-foreground shrink-0 hidden sm:flex items-center gap-1" }, qe = { class: "flex items-center gap-1 shrink-0" }, Re = {
  __name: "NeteasePlaylistDetailView",
  setup(Ee) {
    const { ref: x, computed: V, onMounted: K, watch: O } = window.__etamusic.vue, { useRoute: Q, useRouter: W } = window.__etamusic.vueRouter, {
      ArrowLeft: X,
      Music: j,
      Loader2: C,
      Play: P,
      Plus: Y,
      Clock: Z,
      ListMusic: ee,
      AlertCircle: B
    } = window.__etamusic.icons, { Button: I, Badge: D, Empty: M, useToast: te } = window.__etamusic.ui, { usePlayerStore: se } = window.__etamusic.stores, N = Q(), z = W(), u = te(), m = se(), A = V(() => Number(N.params.id)), n = x(null), h = x([]), k = x(!1), w = x(!1), p = x(/* @__PURE__ */ new Set()), S = V(() => h.value.length > 0);
    async function F() {
      if (A.value) {
        k.value = !0, n.value = null, h.value = [];
        try {
          const t = await ue(A.value), s = t == null ? void 0 : t.playlist;
          if (!s) {
            u.error("歌单不存在或已被删除");
            return;
          }
          n.value = s, h.value = s.tracks || [];
        } catch (t) {
          u.error("加载歌单失败：" + (t.message || "未知错误"));
        } finally {
          k.value = !1;
        }
      }
    }
    async function ae() {
      var t;
      if (S.value) {
        if (m.queue.value.length > 0 && ((t = m.currentTrack) == null ? void 0 : t.__source) === "netease" && m.queue.value.every((s) => s.track.__source === "netease") && m.queue.value.length === h.value.length) {
          m.jumpTo(0);
          return;
        }
        w.value = !0;
        try {
          const s = h.value.slice(0, 200), o = await T(s, "standard");
          if (o.length === 0) {
            u.error("当前歌单无可用播放源（VIP/版权限制）");
            return;
          }
          m.playTracks(o, 0), u.success(`已加入播放队列：${o.length} 首`);
        } catch (s) {
          u.error("加入播放队列失败：" + (s.message || "未知错误"));
        } finally {
          w.value = !1;
        }
      }
    }
    async function L(t, s) {
      if (!p.value.has(t.id)) {
        p.value.add(t.id);
        try {
          const o = await T([t], "standard");
          if (o.length === 0) {
            u.error(`「${t.name}」无可用播放源（VIP/版权限制）`);
            return;
          }
          m.playTracks(o, 0), u.success(`正在播放：${t.name}`);
        } catch (o) {
          u.error("播放失败：" + (o.message || "未知错误"));
        } finally {
          p.value.delete(t.id);
        }
      }
    }
    async function re(t) {
      if (!p.value.has(t.id)) {
        p.value.add(t.id);
        try {
          const s = await T([t], "standard");
          if (s.length === 0) {
            u.error(`「${t.name}」无可用播放源（VIP/版权限制）`);
            return;
          }
          m.appendTracks(s), u.success(`已加入队列：${t.name}`);
        } catch (s) {
          u.error("加入队列失败：" + (s.message || "未知错误"));
        } finally {
          p.value.delete(t.id);
        }
      }
    }
    function le() {
      window.history.length > 1 ? z.back() : z.push("/netease/playlists");
    }
    function ne(t) {
      if (!t || t <= 0) return "--:--";
      const s = Math.floor(t / 60), o = Math.floor(t % 60);
      return `${s}:${String(o).padStart(2, "0")}`;
    }
    function ie(t) {
      return t ? t >= 1e8 ? (t / 1e8).toFixed(1) + "亿" : t >= 1e4 ? (t / 1e4).toFixed(1) + "万" : String(t) : "0";
    }
    function g(t) {
      const s = m.currentTrack;
      return s && s.id === t.id && s.__source === "netease";
    }
    return O(
      () => N.params.id,
      (t) => {
        t && F();
      }
    ), K(() => {
      F();
    }), (t, s) => {
      var o, U;
      return a(), l("div", fe, [
        i("div", me, [
          c(e(I), {
            variant: "ghost",
            size: "sm",
            onClick: le
          }, {
            default: v(() => [
              c(e(X), { class: "h-4 w-4" }),
              s[0] || (s[0] = f(" 返回 ", -1))
            ]),
            _: 1
          })
        ]),
        e(k) && !e(n) ? (a(), l("div", pe, [
          c(e(C), { class: "mr-2 h-5 w-5 animate-spin" }),
          s[1] || (s[1] = f(" 加载中... ", -1))
        ])) : e(n) ? (a(), l(H, { key: 2 }, [
          i("div", he, [
            e(n).coverImgUrl ? (a(), l("img", {
              key: 0,
              src: e(n).coverImgUrl,
              alt: e(n).name,
              class: "h-32 w-32 rounded-lg object-cover shrink-0",
              referrerpolicy: "no-referrer"
            }, null, 8, _e)) : (a(), l("div", ye, [
              c(e(j), { class: "h-12 w-12 text-muted-foreground" })
            ])),
            i("div", xe, [
              i("div", ve, [
                ((o = e(n).creator) == null ? void 0 : o.userId) === e(n).userId ? (a(), _(e(D), {
                  key: 0,
                  variant: "gold"
                }, {
                  default: v(() => [...s[2] || (s[2] = [
                    f("我创建", -1)
                  ])]),
                  _: 1
                })) : (a(), _(e(D), {
                  key: 1,
                  variant: "outline"
                }, {
                  default: v(() => [...s[3] || (s[3] = [
                    f("收藏", -1)
                  ])]),
                  _: 1
                })),
                i("h2", ke, d(e(n).name), 1)
              ]),
              i("div", we, [
                i("span", null, d(((U = e(n).creator) == null ? void 0 : U.nickname) || "—"), 1),
                i("span", ge, [
                  c(e(ee), { class: "h-3.5 w-3.5" }),
                  f(" " + d(e(n).trackCount || e(h).length) + " 首 ", 1)
                ]),
                e(n).playCount ? (a(), l("span", be, [
                  c(e(P), { class: "h-3.5 w-3.5" }),
                  f(" " + d(ie(e(n).playCount)) + " 次播放 ", 1)
                ])) : y("", !0)
              ]),
              e(n).description ? (a(), l("p", Ce, d(e(n).description), 1)) : y("", !0),
              i("div", Pe, [
                c(e(I), {
                  variant: "gold",
                  size: "sm",
                  disabled: e(w) || !e(S),
                  onClick: ae
                }, {
                  default: v(() => [
                    e(w) ? (a(), _(e(C), {
                      key: 0,
                      class: "h-4 w-4 animate-spin"
                    })) : (a(), _(e(P), {
                      key: 1,
                      class: "h-4 w-4"
                    })),
                    s[4] || (s[4] = f(" 播放全部 ", -1))
                  ]),
                  _: 1
                }, 8, ["disabled"])
              ])
            ])
          ]),
          i("div", Ie, [
            !e(S) && !e(k) ? (a(), _(e(M), {
              key: 0,
              icon: e(B),
              title: "歌单内暂无曲目",
              description: "可能需要登录后才能查看完整曲目",
              class: "h-full"
            }, null, 8, ["icon"])) : (a(), l("div", Se, [
              (a(!0), l(H, null, ce(e(h), (r, oe) => {
                var q, R, E, G;
                return a(), l("div", {
                  key: r.id,
                  class: $(["group flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50", { "bg-primary/10": g(r) }]),
                  onDblclick: (b) => L(r)
                }, [
                  i("div", Te, [
                    e(p).has(r.id) ? (a(), _(e(C), {
                      key: 0,
                      class: "h-4 w-4 animate-spin text-muted-foreground"
                    })) : (a(), l("button", {
                      key: 1,
                      class: $(["opacity-0 group-hover:opacity-100 transition-opacity", { "!opacity-100": g(r) }]),
                      onClick: J((b) => L(r), ["stop"])
                    }, [
                      c(e(P), {
                        class: $(["h-4 w-4", g(r) ? "text-primary" : "text-foreground"])
                      }, null, 8, ["class"])
                    ], 10, Ve)),
                    !e(p).has(r.id) && !g(r) ? (a(), l("span", je, d(oe + 1), 1)) : y("", !0)
                  ]),
                  (q = r.al) != null && q.picUrl ? (a(), l("img", {
                    key: 0,
                    src: r.al.picUrl,
                    alt: r.name,
                    class: "h-10 w-10 rounded object-cover shrink-0",
                    referrerpolicy: "no-referrer",
                    loading: "lazy"
                  }, null, 8, Be)) : (a(), l("div", De, [
                    c(e(j), { class: "h-4 w-4 text-muted-foreground" })
                  ])),
                  i("div", Me, [
                    i("div", {
                      class: "text-sm font-medium truncate",
                      title: r.name
                    }, [
                      f(d(r.name) + " ", 1),
                      (R = r.alia) != null && R.length ? (a(), l("span", ze, " (" + d(r.alia[0]) + ") ", 1)) : y("", !0)
                    ], 8, Ne),
                    i("div", Ae, [
                      f(d((r.ar || []).map((b) => b.name).join(" / ") || "未知艺术家") + " ", 1),
                      (E = r.al) != null && E.name ? (a(), l("span", Fe, "·")) : y("", !0),
                      (G = r.al) != null && G.name ? (a(), l("span", Le, d(r.al.name), 1)) : y("", !0)
                    ])
                  ]),
                  i("div", Ue, [
                    c(e(Z), { class: "h-3 w-3" }),
                    f(" " + d(ne(Math.floor((r.dt || 0) / 1e3))), 1)
                  ]),
                  i("div", qe, [
                    c(e(I), {
                      variant: "ghost",
                      size: "sm",
                      class: "h-8 w-8 p-0",
                      disabled: e(p).has(r.id),
                      title: "加入队列",
                      onClick: J((b) => re(r), ["stop"])
                    }, {
                      default: v(() => [
                        c(e(Y), { class: "h-4 w-4" })
                      ]),
                      _: 1
                    }, 8, ["disabled", "onClick"])
                  ])
                ], 42, $e);
              }), 128))
            ]))
          ])
        ], 64)) : (a(), _(e(M), {
          key: 1,
          icon: e(B),
          title: "歌单不存在",
          description: "歌单可能已被删除或链接无效",
          class: "h-full"
        }, null, 8, ["icon"]))
      ]);
    };
  }
}, Ke = /* @__PURE__ */ de(Re, [["__scopeId", "data-v-6a7f8734"]]);
export {
  Ke as default
};
