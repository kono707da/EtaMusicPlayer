import { c as v, a as o, b as n, w as u, u as e, f as D, e as x, d as f, F as S, r as Q, t as p, i as U, R as xe, D as ye, S as X, T as ke, o as i, n as Y, y as _e, U as we, C as he, E as be } from "./api-BVwVWTpM.js";
import { u as Ce } from "./store-KZ0YZNeM.js";
import { a as Z, w as Pe, v as De } from "./runtime-dom.esm-bundler-KgcpFXTz.js";
const $e = { class: "flex h-full flex-col gap-3" }, Ve = { class: "flex items-center justify-between shrink-0" }, Le = { class: "flex items-center gap-3" }, Te = { class: "flex gap-2" }, ze = { class: "flex-1 min-h-0 flex gap-3" }, Me = { class: "w-64 shrink-0 flex flex-col gap-1 overflow-auto pr-1 border-r border-border" }, je = {
  key: 0,
  class: "flex items-center justify-center py-8 text-muted-foreground"
}, Be = ["onClick"], Fe = { class: "flex-1 min-w-0" }, Re = { class: "flex items-center gap-1" }, Ne = { class: "text-sm font-medium truncate" }, Ae = { class: "text-[10px] text-muted-foreground" }, Se = ["onClick"], Ue = { class: "flex-1 min-w-0 flex flex-col overflow-auto" }, We = {
  key: 0,
  class: "flex items-center justify-center h-full text-muted-foreground text-sm"
}, Ee = {
  key: 1,
  class: "flex items-center justify-center py-12 text-muted-foreground"
}, Ie = { class: "shrink-0 rounded-lg border border-border bg-card/40 p-3 mb-3 flex items-center gap-3" }, He = { class: "flex-1 min-w-0" }, Ke = { class: "flex items-center gap-2" }, qe = { class: "text-sm font-medium truncate" }, Ge = { class: "text-xs text-muted-foreground truncate" }, Je = {
  key: 1,
  class: "flex flex-col gap-2 pb-4"
}, Oe = ["onClick"], Qe = ["src"], Xe = { class: "flex-1 min-w-0 flex flex-col gap-1" }, Ye = { class: "text-sm font-medium text-foreground truncate" }, Ze = { class: "text-xs text-muted-foreground truncate" }, et = { class: "flex items-center gap-2 text-[10px] text-muted-foreground mt-auto" }, tt = { key: 0 }, st = { key: 1 }, at = { key: 2 }, lt = ["onClick"], ot = {
  key: 0,
  class: "flex items-center justify-center gap-2 pt-3 shrink-0"
}, nt = { class: "text-sm text-muted-foreground" }, it = { class: "flex flex-col gap-3 py-2" }, rt = { class: "flex flex-col gap-1.5" }, ut = { class: "flex flex-col gap-1.5" }, mt = {
  __name: "AsmrFavoritesView",
  setup(dt) {
    const { ref: m, onMounted: ee } = window.__etamusic.vue, { useRouter: te } = window.__etamusic.vueRouter, {
      Button: w,
      Badge: se,
      Empty: W,
      Input: ae,
      Label: E,
      Dialog: le,
      DialogContent: oe,
      DialogHeader: ne,
      DialogTitle: ie,
      DialogFooter: re,
      DialogDescription: ue,
      useToast: de
    } = window.__etamusic.ui, {
      ArrowLeft: ce,
      Heart: F,
      Loader2: R,
      RefreshCw: fe,
      ListMusic: I,
      Plus: ve,
      Trash2: H,
      Folder: K
    } = window.__etamusic.icons, z = te(), y = de(), N = Ce(), k = m([]), A = m(null), g = m(null), r = m(null), $ = m(!1), V = m(!1), _ = m(1), M = m(50), b = m(0), C = m(1), P = m(!1), h = m(""), L = m(""), j = m(!1);
    async function T() {
      var a, t;
      if (!N.isLoggedIn) {
        z.push("/asmr/account");
        return;
      }
      $.value = !0;
      try {
        const [s, l] = await Promise.all([xe(1, 100), ye()]);
        if (k.value = s.playlists || [], A.value = (l == null ? void 0 : l.id) || null, k.value.length > 0) {
          const d = k.value.find((c) => c.id === A.value) || k.value[0];
          await q(d.id);
        } else
          g.value = null, r.value = null;
      } catch (s) {
        y.error("加载失败", ((t = (a = s == null ? void 0 : s.response) == null ? void 0 : a.data) == null ? void 0 : t.detail) || s.message, s);
      } finally {
        $.value = !1;
      }
    }
    async function q(a) {
      var t, s;
      if (!(g.value === a && r.value)) {
        g.value = a, r.value = null, _.value = 1, V.value = !0;
        try {
          const [l, d] = await Promise.all([
            ke(a),
            X(a, _.value, M.value)
          ]);
          r.value = l, r.value.works = d.works || [];
          const c = d.pagination || {};
          b.value = c.totalCount || r.value.works.length, C.value = c.totalPage || Math.ceil(b.value / M.value) || 1;
        } catch (l) {
          y.error("加载播放列表失败", ((s = (t = l == null ? void 0 : l.response) == null ? void 0 : t.data) == null ? void 0 : s.detail) || l.message, l);
        } finally {
          V.value = !1;
        }
      }
    }
    async function G(a) {
      var t, s, l, d;
      if (!(!g.value || a < 1 || a > C.value)) {
        _.value = a, V.value = !0;
        try {
          const c = await X(g.value, _.value, M.value);
          r.value && (r.value.works = c.works || []);
          const O = c.pagination || {};
          b.value = O.totalCount || ((s = (t = r.value) == null ? void 0 : t.works) == null ? void 0 : s.length) || 0, C.value = O.totalPage || Math.ceil(b.value / M.value) || 1;
        } catch (c) {
          y.error("加载失败", ((d = (l = c == null ? void 0 : c.response) == null ? void 0 : l.data) == null ? void 0 : d.detail) || c.message, c);
        } finally {
          V.value = !1;
        }
      }
    }
    async function me(a) {
      var t, s;
      if (confirm(`确定要删除播放列表「${a.name}」吗？此操作不可撤销。`))
        try {
          await we(a.id), y.success("已删除", `播放列表「${a.name}」已删除`), g.value === a.id && (g.value = null, r.value = null), await T();
        } catch (l) {
          y.error("删除失败", ((s = (t = l == null ? void 0 : l.response) == null ? void 0 : t.data) == null ? void 0 : s.detail) || l.message, l);
        }
    }
    async function J() {
      var a, t;
      if (!h.value.trim()) {
        y.error("请输入名称");
        return;
      }
      j.value = !0;
      try {
        await be(h.value.trim(), 0, L.value.trim()), y.success("已创建", `播放列表「${h.value.trim()}」已创建`), P.value = !1, h.value = "", L.value = "", await T();
      } catch (s) {
        y.error("创建失败", ((t = (a = s == null ? void 0 : s.response) == null ? void 0 : a.data) == null ? void 0 : t.detail) || s.message, s);
      } finally {
        j.value = !1;
      }
    }
    async function pe(a) {
      var t, s, l;
      if (g.value)
        try {
          await he(g.value, [a]), (t = r.value) != null && t.works && (r.value.works = r.value.works.filter((c) => c.id !== a)), b.value > 0 && (b.value -= 1);
          const d = k.value.find((c) => c.id === g.value);
          d && d.works_count > 0 && (d.works_count -= 1), y.success("已移除");
        } catch (d) {
          y.error("移除失败", ((l = (s = d == null ? void 0 : d.response) == null ? void 0 : s.data) == null ? void 0 : l.detail) || d.message, d);
        }
    }
    function ge(a) {
      z.push(`/asmr/work/${a}`);
    }
    function B(a) {
      return a === A.value;
    }
    return ee(() => {
      N.loaded ? T() : N.load().then(T);
    }), (a, t) => (i(), v("div", $e, [
      o("div", Ve, [
        o("div", Le, [
          n(e(w), {
            variant: "ghost",
            size: "sm",
            onClick: t[0] || (t[0] = (s) => e(z).push("/asmr"))
          }, {
            default: u(() => [
              n(e(ce), { class: "h-4 w-4" }),
              t[9] || (t[9] = f(" 返回 ", -1))
            ]),
            _: 1
          }),
          t[10] || (t[10] = o("h2", { class: "text-lg font-semibold" }, "我的播放列表", -1)),
          e(k).length ? (i(), D(e(se), {
            key: 0,
            variant: "outline",
            class: "text-xs"
          }, {
            default: u(() => [
              f(p(e(k).length) + " 个 ", 1)
            ]),
            _: 1
          })) : x("", !0)
        ]),
        o("div", Te, [
          n(e(w), {
            variant: "gold",
            size: "sm",
            onClick: t[1] || (t[1] = (s) => P.value = !0)
          }, {
            default: u(() => [
              n(e(ve), { class: "h-4 w-4" }),
              t[11] || (t[11] = f(" 新建 ", -1))
            ]),
            _: 1
          }),
          n(e(w), {
            variant: "ghost",
            size: "sm",
            disabled: e($),
            onClick: T
          }, {
            default: u(() => [
              n(e(fe), {
                class: Y(["h-4 w-4", { "animate-spin": e($) }])
              }, null, 8, ["class"]),
              t[12] || (t[12] = f(" 刷新 ", -1))
            ]),
            _: 1
          }, 8, ["disabled"])
        ])
      ]),
      o("div", ze, [
        o("div", Me, [
          e($) ? (i(), v("div", je, [
            n(e(R), { class: "mr-2 h-4 w-4 animate-spin" }),
            t[13] || (t[13] = f(" 加载中... ", -1))
          ])) : e(k).length === 0 ? (i(), D(e(W), {
            key: 1,
            icon: e(K),
            title: "还没有播放列表",
            description: "点击右上角「新建」创建",
            class: "py-8"
          }, null, 8, ["icon"])) : x("", !0),
          (i(!0), v(S, null, Q(e(k), (s) => (i(), v("button", {
            key: s.id,
            class: Y(["group flex items-start gap-2 rounded-md border border-transparent px-3 py-2 text-left transition-colors hover:bg-accent/30", {
              "border-primary bg-accent/40": e(g) === s.id,
              "opacity-60": B(s.id)
            }]),
            onClick: (l) => q(s.id)
          }, [
            n(e(I), { class: "mt-0.5 h-4 w-4 shrink-0 text-primary" }),
            o("div", Fe, [
              o("div", Re, [
                o("span", Ne, p(s.name), 1),
                B(s.id) ? (i(), D(e(F), {
                  key: 0,
                  class: "h-3 w-3 text-primary shrink-0"
                })) : x("", !0)
              ]),
              o("div", Ae, p(s.works_count || 0) + " 个作品 ", 1)
            ]),
            B(s.id) ? x("", !0) : (i(), v("span", {
              key: 0,
              class: "opacity-0 group-hover:opacity-100 transition-opacity shrink-0",
              onClick: Z((l) => me(s), ["stop"])
            }, [
              n(e(H), { class: "h-3.5 w-3.5 text-destructive hover:text-destructive/80" })
            ], 8, Se))
          ], 10, Be))), 128))
        ]),
        o("div", Ue, [
          e(g) ? e(V) ? (i(), v("div", Ee, [
            n(e(R), { class: "mr-2 h-5 w-5 animate-spin" }),
            t[15] || (t[15] = f(" 加载中... ", -1))
          ])) : e(r) ? (i(), v(S, { key: 2 }, [
            o("div", Ie, [
              n(e(I), { class: "h-5 w-5 text-primary" }),
              o("div", He, [
                o("div", Ke, [
                  o("span", qe, p(e(r).name), 1),
                  B(e(r).id) ? (i(), D(e(F), {
                    key: 0,
                    class: "h-3.5 w-3.5 text-primary"
                  })) : x("", !0)
                ]),
                o("div", Ge, p(e(r).description || "无描述") + " · " + p(e(b)) + " 个作品 ", 1)
              ])
            ]),
            !e(r).works || e(r).works.length === 0 ? (i(), D(e(W), {
              key: 0,
              icon: e(F),
              title: "播放列表为空",
              description: "在作品详情页可将作品加入此播放列表",
              class: "flex-1"
            }, {
              default: u(() => [
                n(e(w), {
                  variant: "gold",
                  onClick: t[2] || (t[2] = (s) => e(z).push("/asmr"))
                }, {
                  default: u(() => [...t[16] || (t[16] = [
                    f("去浏览", -1)
                  ])]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["icon"])) : (i(), v("div", Je, [
              (i(!0), v(S, null, Q(e(r).works, (s) => (i(), v("div", {
                key: s.id,
                class: "group flex gap-3 rounded-lg border border-border bg-card/40 p-3 cursor-pointer hover:bg-accent/30",
                onClick: (l) => ge(s.id)
              }, [
                o("img", {
                  src: `/api/asmr/cover/${s.id}`,
                  class: "h-16 w-16 rounded-md object-cover border border-border shrink-0"
                }, null, 8, Qe),
                o("div", Xe, [
                  o("div", Ye, p(s.title), 1),
                  o("div", Ze, p(s.name || "—"), 1),
                  o("div", et, [
                    s.release ? (i(), v("span", tt, p(s.release), 1)) : x("", !0),
                    s.dl_count ? (i(), v("span", st, "· " + p(s.dl_count) + " DL", 1)) : x("", !0),
                    s.rate_average_2dp ? (i(), v("span", at, "· ★ " + p(s.rate_average_2dp), 1)) : x("", !0)
                  ])
                ]),
                o("span", {
                  class: "opacity-0 group-hover:opacity-100 transition-opacity shrink-0 self-center",
                  onClick: Z((l) => pe(s.id), ["stop"])
                }, [
                  n(e(H), { class: "h-4 w-4 text-destructive hover:text-destructive/80" })
                ], 8, lt)
              ], 8, Oe))), 128)),
              e(C) > 1 ? (i(), v("div", ot, [
                n(e(w), {
                  variant: "outline",
                  size: "sm",
                  disabled: e(_) <= 1,
                  onClick: t[3] || (t[3] = (s) => G(e(_) - 1))
                }, {
                  default: u(() => [...t[17] || (t[17] = [
                    f(" 上一页 ", -1)
                  ])]),
                  _: 1
                }, 8, ["disabled"]),
                o("span", nt, p(e(_)) + " / " + p(e(C)), 1),
                n(e(w), {
                  variant: "outline",
                  size: "sm",
                  disabled: e(_) >= e(C),
                  onClick: t[4] || (t[4] = (s) => G(e(_) + 1))
                }, {
                  default: u(() => [...t[18] || (t[18] = [
                    f(" 下一页 ", -1)
                  ])]),
                  _: 1
                }, 8, ["disabled"])
              ])) : x("", !0)
            ]))
          ], 64)) : x("", !0) : (i(), v("div", We, [
            n(e(K), { class: "mr-2 h-5 w-5" }),
            t[14] || (t[14] = f(" 请从左侧选择一个播放列表 ", -1))
          ]))
        ])
      ]),
      n(e(le), {
        open: e(P),
        "onUpdate:open": t[8] || (t[8] = (s) => U(P) ? P.value = s : null)
      }, {
        default: u(() => [
          n(e(oe), { class: "sm:max-w-md" }, {
            default: u(() => [
              n(e(ne), null, {
                default: u(() => [
                  n(e(ie), null, {
                    default: u(() => [...t[19] || (t[19] = [
                      f("新建播放列表", -1)
                    ])]),
                    _: 1
                  }),
                  n(e(ue), null, {
                    default: u(() => [...t[20] || (t[20] = [
                      f("创建一个新的播放列表来整理你喜欢的作品", -1)
                    ])]),
                    _: 1
                  })
                ]),
                _: 1
              }),
              o("div", it, [
                o("div", rt, [
                  n(e(E), { for: "pl-name" }, {
                    default: u(() => [...t[21] || (t[21] = [
                      f("名称", -1)
                    ])]),
                    _: 1
                  }),
                  n(e(ae), {
                    id: "pl-name",
                    modelValue: e(h),
                    "onUpdate:modelValue": t[5] || (t[5] = (s) => U(h) ? h.value = s : null),
                    placeholder: "播放列表名称",
                    onKeyup: Pe(J, ["enter"])
                  }, null, 8, ["modelValue"])
                ]),
                o("div", ut, [
                  n(e(E), { for: "pl-desc" }, {
                    default: u(() => [...t[22] || (t[22] = [
                      f("描述（可选）", -1)
                    ])]),
                    _: 1
                  }),
                  _e(o("textarea", {
                    id: "pl-desc",
                    "onUpdate:modelValue": t[6] || (t[6] = (s) => U(L) ? L.value = s : null),
                    placeholder: "简单描述...",
                    rows: "2",
                    class: "flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  }, null, 512), [
                    [De, e(L)]
                  ])
                ])
              ]),
              n(e(re), null, {
                default: u(() => [
                  n(e(w), {
                    variant: "ghost",
                    onClick: t[7] || (t[7] = (s) => P.value = !1)
                  }, {
                    default: u(() => [...t[23] || (t[23] = [
                      f("取消", -1)
                    ])]),
                    _: 1
                  }),
                  n(e(w), {
                    variant: "gold",
                    disabled: e(j) || !e(h).trim(),
                    onClick: J
                  }, {
                    default: u(() => [
                      e(j) ? (i(), D(e(R), {
                        key: 0,
                        class: "mr-2 h-4 w-4 animate-spin"
                      })) : x("", !0),
                      t[24] || (t[24] = f(" 创建 ", -1))
                    ]),
                    _: 1
                  }, 8, ["disabled"])
                ]),
                _: 1
              })
            ]),
            _: 1
          })
        ]),
        _: 1
      }, 8, ["open"])
    ]));
  }
};
export {
  mt as default
};
