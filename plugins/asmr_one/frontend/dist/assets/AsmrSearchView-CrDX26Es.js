import { c as d, a as o, b as l, w as n, u as e, d as u, F as N, r as B, e as k, i as oe, f as V, t as f, s as Fe, l as Ie, g as Oe, h as Ue, j as De, o as i, n as ne, k as Ae } from "./api-BVwVWTpM.js";
import { g as Me, a as Le, b as He, P as Ke } from "./history-C9KjQtlt.js";
import { _ as We } from "./_plugin-vue_export-helper-CHgC5LLL.js";
import { w as re } from "./runtime-dom.esm-bundler-KgcpFXTz.js";
const Ge = { class: "flex h-full gap-4" }, Je = { class: "hidden md:flex w-56 shrink-0 flex-col gap-4 overflow-y-auto pb-4" }, Xe = { class: "flex flex-col gap-1.5" }, Ze = { class: "flex items-center gap-1.5 text-xs font-medium text-muted-foreground px-1" }, Qe = { class: "flex flex-wrap gap-1" }, Ye = {
  key: 0,
  class: "flex flex-col gap-1.5"
}, et = { class: "flex items-center gap-1.5 text-xs font-medium text-muted-foreground px-1" }, tt = { class: "flex flex-wrap gap-1" }, at = {
  key: 1,
  class: "flex flex-col gap-1.5"
}, st = { class: "flex items-center gap-1.5 text-xs font-medium text-muted-foreground px-1" }, lt = { class: "flex flex-col gap-1" }, ot = ["onClick"], nt = {
  key: 2,
  class: "flex flex-col gap-1.5"
}, rt = { class: "flex items-center gap-1.5 text-xs font-medium text-muted-foreground px-1" }, ut = { class: "flex flex-col gap-1" }, it = ["onClick"], dt = { class: "flex-1 min-w-0 flex flex-col gap-3" }, ct = { class: "flex items-center justify-between gap-3" }, ft = { class: "flex items-center gap-2" }, mt = { class: "flex items-center gap-2" }, vt = { class: "flex flex-wrap items-center gap-2" }, gt = { class: "relative flex-1 min-w-[200px] max-w-xl" }, pt = { class: "flex items-center gap-1.5 ml-auto" }, xt = {
  key: 0,
  class: "flex items-center gap-2 text-sm flex-wrap"
}, yt = {
  key: 2,
  class: "text-xs text-muted-foreground"
}, _t = { class: "flex-1 min-h-0 overflow-auto" }, ht = {
  key: 0,
  class: "flex h-full items-center justify-center text-muted-foreground"
}, bt = {
  key: 2,
  class: "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 pb-4"
}, wt = ["onClick"], kt = { class: "aspect-square relative overflow-hidden bg-muted" }, qt = ["src", "alt"], St = { class: "absolute top-2 right-2 flex flex-col gap-1 items-end" }, Ct = { class: "p-2.5" }, Nt = { class: "line-clamp-2 text-sm font-medium text-foreground min-h-[2.5rem]" }, Bt = { class: "mt-1.5 flex items-center justify-between text-xs text-muted-foreground" }, Pt = { class: "truncate max-w-[60%]" }, Vt = { class: "mt-1 text-[10px] text-muted-foreground" }, zt = {
  key: 3,
  class: "flex flex-wrap items-center justify-center gap-2 py-4"
}, Tt = { class: "flex items-center gap-1.5" }, $t = { class: "text-sm text-muted-foreground" }, Rt = { class: "ml-1 text-xs text-muted-foreground" }, jt = {
  __name: "AsmrSearchView",
  setup(Et) {
    const { ref: _, computed: O, watch: ue, onMounted: ie } = window.__etamusic.vue, { useRouter: de, useRoute: ce } = window.__etamusic.vueRouter, { Input: K, Button: h, Badge: P, Empty: fe, useToast: me } = window.__etamusic.ui, {
      Select: j,
      SelectTrigger: E,
      SelectValue: F,
      SelectContent: I,
      SelectItem: $
    } = window.__etamusic.ui, {
      Search: ve,
      Headphones: W,
      Download: ge,
      Settings: pe,
      Loader2: G,
      Tag: J,
      Mic2: xe,
      Users: ye,
      X,
      Home: _e,
      Captions: Z
    } = window.__etamusic.icons, g = de(), r = ce(), he = me(), be = [
      { value: "create_date", label: "最新收录" },
      { value: "release", label: "发售日" },
      { value: "dl_count", label: "销量" },
      { value: "rate_average_2dp", label: "评分" },
      { value: "review_count", label: "评价数" },
      { value: "price", label: "价格" }
    ], we = [24, 30, 60, 120], ke = [3, 5, 10, 20], z = _(""), p = _(r.query.orderBy || "create_date"), x = _(r.query.sort || "desc"), v = _(Number(r.query.page) || 1), q = _(Number(r.query.pageSize) || 30), y = _(Number(r.query.subtitle) === 1), S = _(5), T = _(""), b = _(!1), m = _({
      works: [],
      pagination: { totalCount: 0, currentPage: 1, totalPage: 1 }
    }), U = _([]), D = _([]), A = _([]), C = O(() => r.query.q ? "search" : r.query.tag ? "tag" : r.query.va ? "va" : r.query.circle ? "circle" : "home"), qe = O(() => {
      switch (C.value) {
        case "search":
          return `关键词: ${r.query.q}`;
        case "tag":
          return `标签: ${r.query.tagName || r.query.tag}`;
        case "va":
          return `声优: ${r.query.vaName || r.query.va}`;
        case "circle":
          return `社团: ${r.query.circleName || r.query.circle}`;
        default:
          return "全部作品";
      }
    }), M = O(() => m.value.works.length > 0);
    function Q(a) {
      return C.value === "tag" && String(r.query.tag) === String(a);
    }
    async function Y() {
      var a, t;
      b.value = !0;
      try {
        let c;
        const s = C.value, w = y.value ? 1 : 0;
        s === "search" ? c = await Fe(
          r.query.q,
          v.value,
          q.value,
          p.value,
          x.value,
          w
        ) : s === "tag" ? c = await Ie(
          Number(r.query.tag),
          v.value,
          q.value,
          p.value,
          x.value,
          w
        ) : s === "va" ? c = await Oe(
          r.query.va,
          v.value,
          q.value,
          p.value,
          x.value,
          w
        ) : s === "circle" ? c = await Ue(
          Number(r.query.circle),
          v.value,
          q.value,
          p.value,
          x.value,
          w
        ) : c = await De(
          v.value,
          q.value,
          p.value,
          x.value,
          w
        ), m.value = c;
      } catch (c) {
        he.error("加载失败", ((t = (a = c == null ? void 0 : c.response) == null ? void 0 : a.data) == null ? void 0 : t.detail) || c.message, c), m.value = { works: [], pagination: { totalCount: 0, totalPage: 1 } };
      } finally {
        b.value = !1;
      }
    }
    function Se() {
      const a = z.value.trim(), t = y.value ? 1 : void 0;
      if (!a) {
        g.push({ path: "/asmr", query: { ...t ? { subtitle: t } : {}, orderBy: p.value, sort: x.value, page: 1 } });
        return;
      }
      g.push({
        path: "/asmr",
        query: { q: a, orderBy: p.value, sort: x.value, page: 1, ...t ? { subtitle: t } : {} }
      });
    }
    function ee() {
      Se();
    }
    function te(a) {
      const t = y.value ? 1 : void 0;
      g.push({
        path: "/asmr",
        query: { tag: a.id, tagName: a.name, orderBy: p.value, sort: x.value, page: 1, ...t ? { subtitle: t } : {} }
      });
    }
    function Ce(a) {
      const t = y.value ? 1 : void 0;
      g.push({
        path: "/asmr",
        query: { va: a.id, vaName: a.name, orderBy: p.value, sort: x.value, page: 1, ...t ? { subtitle: t } : {} }
      });
    }
    function Ne(a) {
      const t = y.value ? 1 : void 0;
      g.push({
        path: "/asmr",
        query: { circle: a.id, circleName: a.name, orderBy: p.value, sort: x.value, page: 1, ...t ? { subtitle: t } : {} }
      });
    }
    function ae() {
      const a = y.value ? 1 : void 0;
      g.push({
        path: "/asmr",
        query: { orderBy: p.value, sort: x.value, page: 1, ...a ? { subtitle: a } : {} }
      });
    }
    function Be() {
      ae();
    }
    function R(a) {
      const t = { ...r.query, page: a };
      g.push({ path: "/asmr", query: t });
    }
    function L(a, t) {
      return !t || t < 1 || (a = Math.floor(Number(a)), !Number.isFinite(a) || a < 1) ? 1 : a > t ? t : a;
    }
    function Pe() {
      var t;
      const a = ((t = m.value.pagination) == null ? void 0 : t.totalPage) || 1;
      R(L(v.value + S.value, a));
    }
    function Ve() {
      var t;
      const a = ((t = m.value.pagination) == null ? void 0 : t.totalPage) || 1;
      R(L(v.value - S.value, a));
    }
    function se() {
      var c;
      const a = Number(T.value);
      if (!Number.isFinite(a) || a < 1) {
        T.value = "";
        return;
      }
      const t = ((c = m.value.pagination) == null ? void 0 : c.totalPage) || 1;
      R(L(a, t)), T.value = "";
    }
    function ze(a) {
      p.value = a;
      const t = { ...r.query, orderBy: a, page: 1 };
      g.push({ path: "/asmr", query: t });
    }
    function Te(a) {
      x.value = a;
      const t = { ...r.query, sort: a, page: 1 };
      g.push({ path: "/asmr", query: t });
    }
    function $e(a) {
      q.value = a;
      const t = { ...r.query, pageSize: a, page: 1 };
      g.push({ path: "/asmr", query: t });
    }
    function le() {
      y.value = !y.value;
      const a = { ...r.query, page: 1 };
      y.value ? a.subtitle = 1 : delete a.subtitle, g.push({ path: "/asmr", query: a });
    }
    function Re(a) {
      g.push(`/asmr/work/${a}`);
    }
    function je() {
      g.push("/asmr/downloads");
    }
    function Ee() {
      g.push("/asmr/settings");
    }
    ue(
      () => r.query,
      (a) => {
        p.value = a.orderBy || "create_date", x.value = a.sort || "desc", v.value = Number(a.page) || 1, q.value = Number(a.pageSize) || 30, y.value = Number(a.subtitle) === 1, a.q && (z.value = a.q), Y();
      },
      { deep: !0 }
    );
    function H(a) {
      return a ? a >= 1e4 ? (a / 1e4).toFixed(1) + "w" : a >= 1e3 ? (a / 1e3).toFixed(1) + "k" : String(a) : "0";
    }
    return ie(() => {
      U.value = Me(), D.value = Le(), A.value = He(), r.query.q && (z.value = r.query.q), Y();
    }), (a, t) => {
      var c;
      return i(), d("div", Ge, [
        o("aside", Je, [
          o("div", null, [
            l(e(h), {
              variant: e(C) === "home" ? "gold" : "ghost",
              size: "sm",
              class: "w-full justify-start",
              onClick: ae
            }, {
              default: n(() => [
                l(e(_e), { class: "h-4 w-4" }),
                t[6] || (t[6] = u(" 全部作品 ", -1))
              ]),
              _: 1
            }, 8, ["variant"])
          ]),
          o("div", Xe, [
            o("div", Ze, [
              l(e(J), { class: "h-3 w-3" }),
              t[7] || (t[7] = u(" 热门标签 ", -1))
            ]),
            o("div", Qe, [
              (i(!0), d(N, null, B(e(Ke), (s) => (i(), V(e(P), {
                key: s.id,
                variant: Q(s.id) ? "default" : "outline",
                class: "cursor-pointer text-xs",
                onClick: (w) => te(s)
              }, {
                default: n(() => [
                  u(f(s.name), 1)
                ]),
                _: 2
              }, 1032, ["variant", "onClick"]))), 128))
            ])
          ]),
          e(U).length > 0 ? (i(), d("div", Ye, [
            o("div", et, [
              l(e(J), { class: "h-3 w-3" }),
              t[8] || (t[8] = u(" 最近访问的标签 ", -1))
            ]),
            o("div", tt, [
              (i(!0), d(N, null, B(e(U), (s) => (i(), V(e(P), {
                key: s.id,
                variant: Q(s.id) ? "default" : "outline",
                class: "cursor-pointer text-xs",
                onClick: (w) => te(s)
              }, {
                default: n(() => [
                  u(f(s.name), 1)
                ]),
                _: 2
              }, 1032, ["variant", "onClick"]))), 128))
            ])
          ])) : k("", !0),
          e(D).length > 0 ? (i(), d("div", at, [
            o("div", st, [
              l(e(xe), { class: "h-3 w-3" }),
              t[9] || (t[9] = u(" 最近访问的声优 ", -1))
            ]),
            o("div", lt, [
              (i(!0), d(N, null, B(e(D), (s) => (i(), d("button", {
                key: s.id,
                class: ne(["text-left text-xs px-2 py-1 rounded hover:bg-accent truncate", e(C) === "va" && e(r).query.va === s.id ? "bg-accent text-foreground" : "text-muted-foreground"]),
                onClick: (w) => Ce(s)
              }, f(s.name), 11, ot))), 128))
            ])
          ])) : k("", !0),
          e(A).length > 0 ? (i(), d("div", nt, [
            o("div", rt, [
              l(e(ye), { class: "h-3 w-3" }),
              t[10] || (t[10] = u(" 最近访问的社团 ", -1))
            ]),
            o("div", ut, [
              (i(!0), d(N, null, B(e(A), (s) => (i(), d("button", {
                key: s.id,
                class: ne(["text-left text-xs px-2 py-1 rounded hover:bg-accent truncate", e(C) === "circle" && String(e(r).query.circle) === String(s.id) ? "bg-accent text-foreground" : "text-muted-foreground"]),
                onClick: (w) => Ne(s)
              }, f(s.name), 11, it))), 128))
            ])
          ])) : k("", !0)
        ]),
        o("div", dt, [
          o("div", ct, [
            o("div", ft, [
              l(e(W), { class: "h-5 w-5 text-primary" }),
              t[12] || (t[12] = o("h2", { class: "text-lg font-semibold tracking-tight text-foreground" }, "ASMR 资源", -1)),
              l(e(P), {
                variant: "outline",
                class: "ml-1 text-muted-foreground"
              }, {
                default: n(() => [...t[11] || (t[11] = [
                  u("asmr.one", -1)
                ])]),
                _: 1
              })
            ]),
            o("div", mt, [
              l(e(h), {
                variant: "ghost",
                size: "sm",
                onClick: je
              }, {
                default: n(() => [
                  l(e(ge), { class: "h-4 w-4" }),
                  t[13] || (t[13] = u(" 下载任务 ", -1))
                ]),
                _: 1
              }),
              l(e(h), {
                variant: "ghost",
                size: "sm",
                onClick: Ee
              }, {
                default: n(() => [
                  l(e(pe), { class: "h-4 w-4" }),
                  t[14] || (t[14] = u(" 设置 ", -1))
                ]),
                _: 1
              })
            ])
          ]),
          o("div", vt, [
            o("div", gt, [
              l(e(ve), { class: "pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" }),
              l(e(K), {
                modelValue: e(z),
                "onUpdate:modelValue": t[0] || (t[0] = (s) => oe(z) ? z.value = s : null),
                placeholder: "搜索关键词（如：asmr、催眠、耳语）...",
                class: "h-9 pl-9",
                onKeyup: re(ee, ["enter"])
              }, null, 8, ["modelValue"])
            ]),
            l(e(h), {
              variant: "gold",
              size: "sm",
              disabled: e(b),
              onClick: ee
            }, {
              default: n(() => [
                e(b) ? (i(), V(e(G), {
                  key: 0,
                  class: "h-4 w-4 animate-spin"
                })) : k("", !0),
                t[15] || (t[15] = u(" 搜索 ", -1))
              ]),
              _: 1
            }, 8, ["disabled"]),
            o("div", pt, [
              l(e(j), {
                "model-value": e(p),
                "onUpdate:modelValue": ze
              }, {
                default: n(() => [
                  l(e(E), { class: "h-9 w-[120px]" }, {
                    default: n(() => [
                      l(e(F))
                    ]),
                    _: 1
                  }),
                  l(e(I), null, {
                    default: n(() => [
                      (i(), d(N, null, B(be, (s) => l(e($), {
                        key: s.value,
                        value: s.value
                      }, {
                        default: n(() => [
                          u(f(s.label), 1)
                        ]),
                        _: 2
                      }, 1032, ["value"])), 64))
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }, 8, ["model-value"]),
              l(e(j), {
                "model-value": e(x),
                "onUpdate:modelValue": Te
              }, {
                default: n(() => [
                  l(e(E), { class: "h-9 w-[80px]" }, {
                    default: n(() => [
                      l(e(F))
                    ]),
                    _: 1
                  }),
                  l(e(I), null, {
                    default: n(() => [
                      l(e($), { value: "desc" }, {
                        default: n(() => [...t[16] || (t[16] = [
                          u("降序", -1)
                        ])]),
                        _: 1
                      }),
                      l(e($), { value: "asc" }, {
                        default: n(() => [...t[17] || (t[17] = [
                          u("升序", -1)
                        ])]),
                        _: 1
                      })
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }, 8, ["model-value"]),
              l(e(j), {
                "model-value": String(e(q)),
                "onUpdate:modelValue": t[1] || (t[1] = (s) => $e(Number(s)))
              }, {
                default: n(() => [
                  l(e(E), { class: "h-9 w-[90px]" }, {
                    default: n(() => [
                      l(e(F))
                    ]),
                    _: 1
                  }),
                  l(e(I), null, {
                    default: n(() => [
                      (i(), d(N, null, B(we, (s) => l(e($), {
                        key: s,
                        value: String(s)
                      }, {
                        default: n(() => [
                          u(f(s) + "/页 ", 1)
                        ]),
                        _: 2
                      }, 1032, ["value"])), 64))
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }, 8, ["model-value"]),
              l(e(h), {
                variant: e(y) ? "gold" : "outline",
                size: "sm",
                class: "h-9 gap-1.5",
                title: e(y) ? "当前仅显示含字幕作品，点击取消" : "仅显示含字幕作品",
                onClick: le
              }, {
                default: n(() => [
                  l(e(Z), { class: "h-4 w-4" }),
                  t[18] || (t[18] = u(" 字幕 ", -1))
                ]),
                _: 1
              }, 8, ["variant", "title"])
            ])
          ]),
          e(C) !== "home" || e(y) ? (i(), d("div", xt, [
            t[20] || (t[20] = o("span", { class: "text-muted-foreground" }, "当前筛选:", -1)),
            e(C) !== "home" ? (i(), V(e(P), {
              key: 0,
              variant: "gold",
              class: "gap-1"
            }, {
              default: n(() => [
                u(f(e(qe)) + " ", 1),
                o("button", {
                  class: "ml-0.5 hover:bg-primary/20 rounded",
                  onClick: Be
                }, [
                  l(e(X), { class: "h-3 w-3" })
                ])
              ]),
              _: 1
            })) : k("", !0),
            e(y) ? (i(), V(e(P), {
              key: 1,
              variant: "gold",
              class: "gap-1"
            }, {
              default: n(() => [
                l(e(Z), { class: "h-3 w-3" }),
                t[19] || (t[19] = u(" 含字幕 ", -1)),
                o("button", {
                  class: "ml-0.5 hover:bg-primary/20 rounded",
                  onClick: le
                }, [
                  l(e(X), { class: "h-3 w-3" })
                ])
              ]),
              _: 1
            })) : k("", !0),
            (c = e(m).pagination) != null && c.totalCount ? (i(), d("span", yt, " (共 " + f(H(e(m).pagination.totalCount)) + " 个作品) ", 1)) : k("", !0)
          ])) : k("", !0),
          o("div", _t, [
            e(b) && !e(M) ? (i(), d("div", ht, [
              l(e(G), { class: "mr-2 h-5 w-5 animate-spin" }),
              t[21] || (t[21] = u(" 加载中... ", -1))
            ])) : e(M) ? (i(), d("div", bt, [
              (i(!0), d(N, null, B(e(m).works, (s) => (i(), d("div", {
                key: s.id,
                class: "group cursor-pointer rounded-lg border border-border bg-card/40 overflow-hidden transition-all hover:border-primary/60 hover:shadow-lg",
                onClick: (w) => Re(s.id)
              }, [
                o("div", kt, [
                  o("img", {
                    src: e(Ae)(s.id),
                    alt: s.title,
                    loading: "lazy",
                    class: "absolute inset-0 h-full w-full object-cover transition-transform group-hover:scale-105"
                  }, null, 8, qt),
                  o("div", St, [
                    s.nsfw ? (i(), V(e(P), {
                      key: 0,
                      variant: "destructive",
                      class: "text-[10px]"
                    }, {
                      default: n(() => [...t[22] || (t[22] = [
                        u("R18", -1)
                      ])]),
                      _: 1
                    })) : k("", !0),
                    l(e(P), {
                      variant: "secondary",
                      class: "text-[10px]"
                    }, {
                      default: n(() => [
                        u(f(H(s.dl_count)) + " DL", 1)
                      ]),
                      _: 2
                    }, 1024)
                  ])
                ]),
                o("div", Ct, [
                  o("div", Nt, f(s.title), 1),
                  o("div", Bt, [
                    o("span", Pt, f(s.name || "—"), 1),
                    o("span", null, "★ " + f(s.rate_average_2dp || "—"), 1)
                  ]),
                  o("div", Vt, f(s.release), 1)
                ])
              ], 8, wt))), 128))
            ])) : (i(), V(e(fe), {
              key: 1,
              icon: e(W),
              title: "没有找到作品",
              description: "试试其他关键词或筛选条件",
              class: "h-full"
            }, null, 8, ["icon"])),
            e(M) && e(m).pagination && e(m).pagination.totalPage > 1 ? (i(), d("div", zt, [
              l(e(j), {
                "model-value": String(e(S)),
                "onUpdate:modelValue": t[2] || (t[2] = (s) => S.value = Number(s))
              }, {
                default: n(() => [
                  l(e(E), { class: "h-8 w-[70px]" }, {
                    default: n(() => [
                      l(e(F))
                    ]),
                    _: 1
                  }),
                  l(e(I), null, {
                    default: n(() => [
                      (i(), d(N, null, B(ke, (s) => l(e($), {
                        key: s,
                        value: String(s)
                      }, {
                        default: n(() => [
                          u(f(s) + "页 ", 1)
                        ]),
                        _: 2
                      }, 1032, ["value"])), 64))
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }, 8, ["model-value"]),
              l(e(h), {
                variant: "outline",
                size: "sm",
                class: "h-8",
                disabled: e(v) <= 1 || e(b),
                title: `后退 ${e(S)} 页`,
                onClick: Ve
              }, {
                default: n(() => [
                  u(" «" + f(e(S)), 1)
                ]),
                _: 1
              }, 8, ["disabled", "title"]),
              l(e(h), {
                variant: "ghost",
                size: "sm",
                class: "h-8",
                disabled: e(v) <= 1 || e(b),
                onClick: t[3] || (t[3] = (s) => R(e(v) - 1))
              }, {
                default: n(() => [...t[23] || (t[23] = [
                  u(" 上一页 ", -1)
                ])]),
                _: 1
              }, 8, ["disabled"]),
              o("div", Tt, [
                l(e(K), {
                  modelValue: e(T),
                  "onUpdate:modelValue": t[4] || (t[4] = (s) => oe(T) ? T.value = s : null),
                  type: "number",
                  min: "1",
                  max: e(m).pagination.totalPage,
                  placeholder: String(e(v)),
                  class: "h-8 w-16 text-center",
                  onKeyup: re(se, ["enter"])
                }, null, 8, ["modelValue", "max", "placeholder"]),
                o("span", $t, "/ " + f(e(m).pagination.totalPage), 1),
                l(e(h), {
                  variant: "outline",
                  size: "sm",
                  class: "h-8",
                  disabled: e(b),
                  onClick: se
                }, {
                  default: n(() => [...t[24] || (t[24] = [
                    u(" 跳转 ", -1)
                  ])]),
                  _: 1
                }, 8, ["disabled"])
              ]),
              l(e(h), {
                variant: "ghost",
                size: "sm",
                class: "h-8",
                disabled: e(v) >= e(m).pagination.totalPage || e(b),
                onClick: t[5] || (t[5] = (s) => R(e(v) + 1))
              }, {
                default: n(() => [...t[25] || (t[25] = [
                  u(" 下一页 ", -1)
                ])]),
                _: 1
              }, 8, ["disabled"]),
              l(e(h), {
                variant: "outline",
                size: "sm",
                class: "h-8",
                disabled: e(v) >= e(m).pagination.totalPage || e(b),
                title: `前进 ${e(S)} 页`,
                onClick: Pe
              }, {
                default: n(() => [
                  u(f(e(S)) + "» ", 1)
                ]),
                _: 1
              }, 8, ["disabled", "title"]),
              o("span", Rt, " (共 " + f(H(e(m).pagination.totalCount)) + " 个作品) ", 1)
            ])) : k("", !0)
          ])
        ])
      ]);
    };
  }
}, Dt = /* @__PURE__ */ We(jt, [["__scopeId", "data-v-7218cd7f"]]);
export {
  Dt as default
};
