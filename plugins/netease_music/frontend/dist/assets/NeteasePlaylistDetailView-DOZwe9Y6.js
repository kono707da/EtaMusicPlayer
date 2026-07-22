import { c as r, a as n, b as d, w as v, u as e, f as u, d as f, F as Q, t as m, e as x, r as pe, z as _e, o as a, n as j, k as W, l as z } from "./api-CJ1Y_yWo.js";
import { _ as ye } from "./_plugin-vue_export-helper-CHgC5LLL.js";
import { w as D } from "./runtime-dom.esm-bundler-1Zj72-Aa.js";
const ve = { class: "flex h-full flex-col gap-3" }, xe = { class: "flex items-center gap-2" }, ke = {
  key: 0,
  class: "flex-1 flex items-center justify-center text-muted-foreground"
}, we = { class: "flex gap-4 p-4 rounded-lg border border-border bg-card/40" }, ge = ["src", "alt"], be = {
  key: 1,
  class: "h-32 w-32 rounded-lg bg-muted flex items-center justify-center shrink-0"
}, Ce = { class: "flex-1 min-w-0 flex flex-col gap-2" }, Se = { class: "flex items-center gap-2 flex-wrap" }, Ie = { class: "text-xl font-semibold truncate" }, Pe = { class: "flex items-center gap-3 text-sm text-muted-foreground flex-wrap" }, $e = { class: "flex items-center gap-1" }, Te = {
  key: 0,
  class: "flex items-center gap-1"
}, Ve = {
  key: 0,
  class: "text-xs text-muted-foreground line-clamp-2"
}, je = { class: "flex items-center gap-2 mt-auto" }, ze = { class: "flex-1 min-h-0 overflow-auto" }, De = {
  key: 1,
  class: "flex flex-col gap-1 pb-4"
}, Be = ["onDblclick"], Me = { class: "w-8 h-8 flex items-center justify-center shrink-0" }, Ne = ["onClick"], Ae = {
  key: 2,
  class: "text-sm text-muted-foreground group-hover:hidden"
}, Fe = ["src", "alt"], Le = {
  key: 1,
  class: "h-10 w-10 rounded bg-muted flex items-center justify-center shrink-0"
}, Ue = { class: "flex-1 min-w-0 flex flex-col gap-0.5" }, qe = ["title"], Re = {
  key: 0,
  class: "text-muted-foreground text-xs ml-1"
}, Ee = { class: "text-xs text-muted-foreground truncate" }, Ge = {
  key: 0,
  class: "mx-1"
}, He = {
  key: 1,
  class: "truncate"
}, Je = { class: "text-xs text-muted-foreground shrink-0 hidden sm:flex items-center gap-1" }, Ke = { class: "flex items-center gap-1 shrink-0" }, Oe = {
  __name: "NeteasePlaylistDetailView",
  setup(Qe) {
    const { ref: y, computed: B, onMounted: X, watch: Y } = window.__etamusic.vue, { useRoute: Z, useRouter: ee } = window.__etamusic.vueRouter, {
      ArrowLeft: te,
      Music: M,
      Loader2: k,
      Play: V,
      Plus: se,
      Clock: ae,
      ListMusic: le,
      AlertCircle: N,
      Download: A
    } = window.__etamusic.icons, { Button: w, Badge: F, Empty: L, useToast: re } = window.__etamusic.ui, { usePlayerStore: ie } = window.__etamusic.stores, U = Z(), q = ee(), o = re(), h = ie(), R = B(() => Number(U.params.id)), i = y(null), _ = y([]), S = y(!1), I = y(!1), p = y(/* @__PURE__ */ new Set()), g = y(/* @__PURE__ */ new Set()), P = y(!1), b = B(() => _.value.length > 0);
    async function E() {
      if (R.value) {
        S.value = !0, i.value = null, _.value = [];
        try {
          const t = await _e(R.value), s = t == null ? void 0 : t.playlist;
          if (!s) {
            o.error("歌单不存在或已被删除");
            return;
          }
          i.value = s, _.value = s.tracks || [];
        } catch (t) {
          o.error("加载歌单失败：" + (t.message || "未知错误"));
        } finally {
          S.value = !1;
        }
      }
    }
    async function ne() {
      var t;
      if (b.value) {
        if (h.queue.value.length > 0 && ((t = h.currentTrack) == null ? void 0 : t.__source) === "netease" && h.queue.value.every((s) => s.track.__source === "netease") && h.queue.value.length === _.value.length) {
          h.jumpTo(0);
          return;
        }
        I.value = !0;
        try {
          const s = _.value.slice(0, 200), c = await z(s, "standard");
          if (c.length === 0) {
            o.error("当前歌单无可用播放源（VIP/版权限制）");
            return;
          }
          h.playTracks(c, 0), o.success(`已加入播放队列：${c.length} 首`);
        } catch (s) {
          o.error("加入播放队列失败：" + (s.message || "未知错误"));
        } finally {
          I.value = !1;
        }
      }
    }
    async function G(t, s) {
      if (!p.value.has(t.id)) {
        p.value.add(t.id);
        try {
          const c = await z([t], "standard");
          if (c.length === 0) {
            o.error(`「${t.name}」无可用播放源（VIP/版权限制）`);
            return;
          }
          h.playTracks(c, 0), o.success(`正在播放：${t.name}`);
        } catch (c) {
          o.error("播放失败：" + (c.message || "未知错误"));
        } finally {
          p.value.delete(t.id);
        }
      }
    }
    async function oe(t) {
      if (!p.value.has(t.id)) {
        p.value.add(t.id);
        try {
          const s = await z([t], "standard");
          if (s.length === 0) {
            o.error(`「${t.name}」无可用播放源（VIP/版权限制）`);
            return;
          }
          h.appendTracks(s), o.success(`已加入队列：${t.name}`);
        } catch (s) {
          o.error("加入队列失败：" + (s.message || "未知错误"));
        } finally {
          p.value.delete(t.id);
        }
      }
    }
    async function ce(t) {
      if (!g.value.has(t.id)) {
        g.value.add(t.id);
        try {
          const s = await W([t.id], { level: "exhigh" });
          o.success(s.message || "下载任务已创建");
        } catch (s) {
          o.error("下载失败：" + (s.message || "未知错误"));
        } finally {
          g.value.delete(t.id);
        }
      }
    }
    async function de() {
      if (b.value) {
        P.value = !0;
        try {
          const s = _.value.slice(0, 200).map((T) => T.id), c = await W(s, { level: "exhigh" });
          o.success(c.message || "下载任务已创建");
        } catch (t) {
          o.error("下载失败：" + (t.message || "未知错误"));
        } finally {
          P.value = !1;
        }
      }
    }
    function ue() {
      window.history.length > 1 ? q.back() : q.push("/netease/playlists");
    }
    function fe(t) {
      if (!t || t <= 0) return "--:--";
      const s = Math.floor(t / 60), c = Math.floor(t % 60);
      return `${s}:${String(c).padStart(2, "0")}`;
    }
    function me(t) {
      return t ? t >= 1e8 ? (t / 1e8).toFixed(1) + "亿" : t >= 1e4 ? (t / 1e4).toFixed(1) + "万" : String(t) : "0";
    }
    function $(t) {
      const s = h.currentTrack;
      return s && s.id === t.id && s.__source === "netease";
    }
    return Y(
      () => U.params.id,
      (t) => {
        t && E();
      }
    ), X(() => {
      E();
    }), (t, s) => {
      var c, T;
      return a(), r("div", ve, [
        n("div", xe, [
          d(e(w), {
            variant: "ghost",
            size: "sm",
            onClick: ue
          }, {
            default: v(() => [
              d(e(te), { class: "h-4 w-4" }),
              s[0] || (s[0] = u(" 返回 ", -1))
            ]),
            _: 1
          })
        ]),
        e(S) && !e(i) ? (a(), r("div", ke, [
          d(e(k), { class: "mr-2 h-5 w-5 animate-spin" }),
          s[1] || (s[1] = u(" 加载中... ", -1))
        ])) : e(i) ? (a(), r(Q, { key: 2 }, [
          n("div", we, [
            e(i).coverImgUrl ? (a(), r("img", {
              key: 0,
              src: e(i).coverImgUrl,
              alt: e(i).name,
              class: "h-32 w-32 rounded-lg object-cover shrink-0",
              referrerpolicy: "no-referrer"
            }, null, 8, ge)) : (a(), r("div", be, [
              d(e(M), { class: "h-12 w-12 text-muted-foreground" })
            ])),
            n("div", Ce, [
              n("div", Se, [
                ((c = e(i).creator) == null ? void 0 : c.userId) === e(i).userId ? (a(), f(e(F), {
                  key: 0,
                  variant: "gold"
                }, {
                  default: v(() => [...s[2] || (s[2] = [
                    u("我创建", -1)
                  ])]),
                  _: 1
                })) : (a(), f(e(F), {
                  key: 1,
                  variant: "outline"
                }, {
                  default: v(() => [...s[3] || (s[3] = [
                    u("收藏", -1)
                  ])]),
                  _: 1
                })),
                n("h2", Ie, m(e(i).name), 1)
              ]),
              n("div", Pe, [
                n("span", null, m(((T = e(i).creator) == null ? void 0 : T.nickname) || "—"), 1),
                n("span", $e, [
                  d(e(le), { class: "h-3.5 w-3.5" }),
                  u(" " + m(e(i).trackCount || e(_).length) + " 首 ", 1)
                ]),
                e(i).playCount ? (a(), r("span", Te, [
                  d(e(V), { class: "h-3.5 w-3.5" }),
                  u(" " + m(me(e(i).playCount)) + " 次播放 ", 1)
                ])) : x("", !0)
              ]),
              e(i).description ? (a(), r("p", Ve, m(e(i).description), 1)) : x("", !0),
              n("div", je, [
                d(e(w), {
                  variant: "secondary",
                  size: "sm",
                  disabled: e(P) || !e(b),
                  onClick: de
                }, {
                  default: v(() => [
                    e(P) ? (a(), f(e(k), {
                      key: 0,
                      class: "h-4 w-4 animate-spin"
                    })) : (a(), f(e(A), {
                      key: 1,
                      class: "h-4 w-4"
                    })),
                    s[4] || (s[4] = u(" 下载全部 ", -1))
                  ]),
                  _: 1
                }, 8, ["disabled"]),
                d(e(w), {
                  variant: "gold",
                  size: "sm",
                  disabled: e(I) || !e(b),
                  onClick: ne
                }, {
                  default: v(() => [
                    e(I) ? (a(), f(e(k), {
                      key: 0,
                      class: "h-4 w-4 animate-spin"
                    })) : (a(), f(e(V), {
                      key: 1,
                      class: "h-4 w-4"
                    })),
                    s[5] || (s[5] = u(" 播放全部 ", -1))
                  ]),
                  _: 1
                }, 8, ["disabled"])
              ])
            ])
          ]),
          n("div", ze, [
            !e(b) && !e(S) ? (a(), f(e(L), {
              key: 0,
              icon: e(N),
              title: "歌单内暂无曲目",
              description: "可能需要登录后才能查看完整曲目",
              class: "h-full"
            }, null, 8, ["icon"])) : (a(), r("div", De, [
              (a(!0), r(Q, null, pe(e(_), (l, he) => {
                var H, J, K, O;
                return a(), r("div", {
                  key: l.id,
                  class: j(["group flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer transition-colors hover:bg-accent/50", { "bg-primary/10": $(l) }]),
                  onDblclick: (C) => G(l)
                }, [
                  n("div", Me, [
                    e(p).has(l.id) ? (a(), f(e(k), {
                      key: 0,
                      class: "h-4 w-4 animate-spin text-muted-foreground"
                    })) : (a(), r("button", {
                      key: 1,
                      class: j(["opacity-0 group-hover:opacity-100 transition-opacity", { "!opacity-100": $(l) }]),
                      onClick: D((C) => G(l), ["stop"])
                    }, [
                      d(e(V), {
                        class: j(["h-4 w-4", $(l) ? "text-primary" : "text-foreground"])
                      }, null, 8, ["class"])
                    ], 10, Ne)),
                    !e(p).has(l.id) && !$(l) ? (a(), r("span", Ae, m(he + 1), 1)) : x("", !0)
                  ]),
                  (H = l.al) != null && H.picUrl ? (a(), r("img", {
                    key: 0,
                    src: l.al.picUrl,
                    alt: l.name,
                    class: "h-10 w-10 rounded object-cover shrink-0",
                    referrerpolicy: "no-referrer",
                    loading: "lazy"
                  }, null, 8, Fe)) : (a(), r("div", Le, [
                    d(e(M), { class: "h-4 w-4 text-muted-foreground" })
                  ])),
                  n("div", Ue, [
                    n("div", {
                      class: "text-sm font-medium truncate",
                      title: l.name
                    }, [
                      u(m(l.name) + " ", 1),
                      (J = l.alia) != null && J.length ? (a(), r("span", Re, " (" + m(l.alia[0]) + ") ", 1)) : x("", !0)
                    ], 8, qe),
                    n("div", Ee, [
                      u(m((l.ar || []).map((C) => C.name).join(" / ") || "未知艺术家") + " ", 1),
                      (K = l.al) != null && K.name ? (a(), r("span", Ge, "·")) : x("", !0),
                      (O = l.al) != null && O.name ? (a(), r("span", He, m(l.al.name), 1)) : x("", !0)
                    ])
                  ]),
                  n("div", Je, [
                    d(e(ae), { class: "h-3 w-3" }),
                    u(" " + m(fe(Math.floor((l.dt || 0) / 1e3))), 1)
                  ]),
                  n("div", Ke, [
                    d(e(w), {
                      variant: "ghost",
                      size: "sm",
                      class: "h-8 w-8 p-0",
                      disabled: e(g).has(l.id),
                      title: "下载",
                      onClick: D((C) => ce(l), ["stop"])
                    }, {
                      default: v(() => [
                        e(g).has(l.id) ? (a(), f(e(k), {
                          key: 0,
                          class: "h-4 w-4 animate-spin"
                        })) : (a(), f(e(A), {
                          key: 1,
                          class: "h-4 w-4"
                        }))
                      ]),
                      _: 2
                    }, 1032, ["disabled", "onClick"]),
                    d(e(w), {
                      variant: "ghost",
                      size: "sm",
                      class: "h-8 w-8 p-0",
                      disabled: e(p).has(l.id),
                      title: "加入队列",
                      onClick: D((C) => oe(l), ["stop"])
                    }, {
                      default: v(() => [
                        d(e(se), { class: "h-4 w-4" })
                      ]),
                      _: 1
                    }, 8, ["disabled", "onClick"])
                  ])
                ], 42, Be);
              }), 128))
            ]))
          ])
        ], 64)) : (a(), f(e(L), {
          key: 1,
          icon: e(N),
          title: "歌单不存在",
          description: "歌单可能已被删除或链接无效",
          class: "h-full"
        }, null, 8, ["icon"]))
      ]);
    };
  }
}, Ze = /* @__PURE__ */ ye(Oe, [["__scopeId", "data-v-5ebc9450"]]);
export {
  Ze as default
};
