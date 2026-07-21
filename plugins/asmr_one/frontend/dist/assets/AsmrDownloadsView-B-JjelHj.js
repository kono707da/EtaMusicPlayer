import { c as i, a as o, b as d, w as p, u as s, f as w, F as T, r as A, i as re, L as ie, o as a, d as f, n as M, M as de, t as l, e as m, p as ue, N as ce, k as fe, O as pe, P as me, Q as ve } from "./api-BVwVWTpM.js";
import { a as ge } from "./runtime-dom.esm-bundler-KgcpFXTz.js";
const xe = { class: "flex h-full flex-col gap-4" }, _e = { class: "flex items-center justify-between" }, we = { class: "flex items-center gap-3" }, ke = { class: "flex-1 min-h-0 overflow-auto" }, he = {
  key: 1,
  class: "flex flex-col gap-2 pb-4"
}, be = ["onClick"], ye = { class: "flex-1 min-w-0" }, Ce = { class: "flex items-center gap-2" }, De = { class: "text-sm font-medium text-foreground truncate" }, ze = { class: "text-xs text-muted-foreground mt-0.5" }, Te = {
  key: 0,
  class: "h-1 bg-secondary"
}, Be = {
  key: 1,
  class: "border-t border-border p-4 bg-secondary/20"
}, Ie = {
  key: 0,
  class: "flex justify-center py-4"
}, Le = {
  key: 0,
  class: "mb-3 text-sm"
}, Ne = { class: "text-foreground truncate" }, Pe = { class: "text-xs text-muted-foreground mt-0.5" }, Re = {
  key: 1,
  class: "mb-3 rounded-md bg-destructive/10 border border-destructive/30 p-2.5"
}, $e = { class: "text-xs text-destructive/90 whitespace-pre-wrap font-mono" }, Ae = {
  key: 2,
  class: "text-sm"
}, Me = { class: "max-h-60 overflow-auto rounded-md border border-border" }, Ve = { class: "w-full text-xs" }, Ee = { class: "p-2 break-all" }, Se = { class: "p-2" }, Ue = { class: "p-2 text-right tabular-nums" }, Qe = {
  __name: "AsmrDownloadsView",
  setup(je) {
    const { ref: v, computed: V, onMounted: E, onUnmounted: S } = window.__etamusic.vue, { useRouter: U } = window.__etamusic.vueRouter, { Button: g, Badge: B, Empty: j, useToast: F, CoverPickerDialog: O } = window.__etamusic.ui, {
      ArrowLeft: Q,
      RefreshCw: W,
      Loader2: I,
      CheckCircle2: X,
      AlertCircle: q,
      Clock: L,
      XCircle: G,
      Trash2: H,
      Ban: N,
      Download: J,
      ImageIcon: K
    } = window.__etamusic.icons, P = U(), _ = F(), k = v([]), h = v(!1), b = v(null), u = v(null), D = v(!1);
    let z = null;
    const y = v(!1), R = v(null), $ = v(null), Y = V(
      () => k.value.some((n) => n.status === "running" || n.status === "pending")
    );
    async function x() {
      var n, t;
      h.value = !0;
      try {
        const e = await ie();
        k.value = e.tasks;
      } catch (e) {
        _.error("加载失败", ((t = (n = e == null ? void 0 : e.response) == null ? void 0 : n.data) == null ? void 0 : t.detail) || e.message, e);
      } finally {
        h.value = !1;
      }
    }
    async function Z() {
      Y.value && await x();
    }
    async function ee(n) {
      if (b.value === n.id) {
        b.value = null, u.value = null;
        return;
      }
      b.value = n.id, D.value = !0;
      try {
        u.value = await pe(n.id);
      } finally {
        D.value = !1;
      }
    }
    async function te(n) {
      var t, e;
      try {
        await me(n.id), _.success("已请求取消"), await x();
      } catch (r) {
        _.error("取消失败", ((e = (t = r == null ? void 0 : r.response) == null ? void 0 : t.data) == null ? void 0 : e.detail) || r.message, r);
      }
    }
    async function se(n) {
      var t, e;
      try {
        await ve(n.id), _.success("已删除"), await x();
      } catch (r) {
        _.error("删除失败", ((e = (t = r == null ? void 0 : r.response) == null ? void 0 : t.data) == null ? void 0 : e.detail) || r.message, r);
      }
    }
    function oe(n) {
      R.value = n.id, $.value = n.work_id, y.value = !0;
    }
    async function ne() {
      await x();
    }
    function C(n) {
      switch (n) {
        case "pending":
          return { icon: L, color: "text-muted-foreground", label: "等待中" };
        case "running":
          return { icon: I, color: "text-blue-400", label: "下载中", spin: !0 };
        case "completed":
          return { icon: X, color: "text-emerald-400", label: "已完成" };
        case "partial":
          return { icon: q, color: "text-amber-400", label: "部分完成" };
        case "failed":
          return { icon: G, color: "text-destructive", label: "失败" };
        case "canceled":
          return { icon: N, color: "text-muted-foreground", label: "已取消" };
        default:
          return { icon: L, color: "text-muted-foreground", label: n };
      }
    }
    function ae(n) {
      const t = n.total_files || 0;
      if (t === 0) return 0;
      const e = (n.completed_files || 0) + (n.skipped_files || 0);
      return Math.round(e / t * 100);
    }
    function le(n) {
      if (!n) return "--";
      try {
        return new Date(n).toLocaleString("zh-CN", { hour12: !1 });
      } catch {
        return n;
      }
    }
    return E(() => {
      x(), z = setInterval(Z, 3e3);
    }), S(() => {
      z && clearInterval(z);
    }), (n, t) => (a(), i("div", xe, [
      o("div", _e, [
        o("div", we, [
          d(s(g), {
            variant: "ghost",
            size: "sm",
            onClick: t[0] || (t[0] = (e) => s(P).push("/asmr"))
          }, {
            default: p(() => [
              d(s(Q), { class: "h-4 w-4" }),
              t[4] || (t[4] = f(" 返回搜索 ", -1))
            ]),
            _: 1
          }),
          t[5] || (t[5] = o("h2", { class: "text-lg font-semibold" }, "下载任务", -1))
        ]),
        d(s(g), {
          variant: "ghost",
          size: "sm",
          disabled: s(h),
          onClick: x
        }, {
          default: p(() => [
            d(s(W), {
              class: M(["h-4 w-4", { "animate-spin": s(h) }])
            }, null, 8, ["class"]),
            t[6] || (t[6] = f(" 刷新 ", -1))
          ]),
          _: 1
        }, 8, ["disabled"])
      ]),
      o("div", ke, [
        s(k).length === 0 ? (a(), w(s(j), {
          key: 0,
          icon: s(J),
          title: "还没有下载任务",
          description: "去搜索作品并创建下载任务",
          class: "h-full"
        }, {
          default: p(() => [
            d(s(g), {
              variant: "gold",
              onClick: t[1] || (t[1] = (e) => s(P).push("/asmr"))
            }, {
              default: p(() => [...t[7] || (t[7] = [
                f("去搜索", -1)
              ])]),
              _: 1
            })
          ]),
          _: 1
        }, 8, ["icon"])) : (a(), i("div", he, [
          (a(!0), i(T, null, A(s(k), (e) => {
            var r;
            return a(), i("div", {
              key: e.id,
              class: "rounded-lg border border-border bg-card/40 overflow-hidden"
            }, [
              o("div", {
                class: "flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-accent/30",
                onClick: (c) => ee(e)
              }, [
                (a(), w(de(C(e.status).icon), {
                  class: M(["h-4 w-4 shrink-0", [C(e.status).color, { "animate-spin": C(e.status).spin }]])
                }, null, 8, ["class"])),
                o("div", ye, [
                  o("div", Ce, [
                    o("span", De, "#" + l(e.id) + " " + l(e.work_title), 1),
                    d(s(B), {
                      variant: "outline",
                      class: "text-xs shrink-0"
                    }, {
                      default: p(() => [
                        f(l(C(e.status).label), 1)
                      ]),
                      _: 2
                    }, 1024)
                  ]),
                  o("div", ze, [
                    f(l(e.completed_files) + " 完成 / " + l(e.skipped_files) + " 跳过 / " + l(e.failed_files) + " 失败 · 共 " + l(e.total_files) + " 个文件 ", 1),
                    t[8] || (t[8] = o("span", { class: "ml-2" }, "·", -1)),
                    f(" " + l(le(e.created_at)), 1)
                  ])
                ]),
                o("div", {
                  class: "flex items-center gap-1 shrink-0",
                  onClick: t[2] || (t[2] = ge(() => {
                  }, ["stop"]))
                }, [
                  e.status === "running" || e.status === "pending" ? (a(), w(s(g), {
                    key: 0,
                    variant: "ghost",
                    size: "sm",
                    onClick: (c) => te(e)
                  }, {
                    default: p(() => [
                      d(s(N), { class: "h-3.5 w-3.5" }),
                      t[9] || (t[9] = f(" 取消 ", -1))
                    ]),
                    _: 1
                  }, 8, ["onClick"])) : m("", !0),
                  ["completed", "partial"].includes(e.status) ? (a(), w(s(g), {
                    key: 1,
                    variant: "ghost",
                    size: "sm",
                    onClick: (c) => oe(e)
                  }, {
                    default: p(() => [
                      d(s(K), { class: "h-3.5 w-3.5" }),
                      f(" " + l(e.cover_applied ? "换封面" : "设封面"), 1)
                    ]),
                    _: 2
                  }, 1032, ["onClick"])) : m("", !0),
                  ["running", "pending"].includes(e.status) ? m("", !0) : (a(), w(s(g), {
                    key: 2,
                    variant: "ghost",
                    size: "sm",
                    onClick: (c) => se(e)
                  }, {
                    default: p(() => [
                      d(s(H), { class: "h-3.5 w-3.5" }),
                      t[10] || (t[10] = f(" 删除 ", -1))
                    ]),
                    _: 1
                  }, 8, ["onClick"]))
                ])
              ], 8, be),
              e.status === "running" || e.status === "pending" ? (a(), i("div", Te, [
                o("div", {
                  class: "h-full bg-primary transition-all",
                  style: ue({ width: ae(e) + "%" })
                }, null, 4)
              ])) : m("", !0),
              s(b) === e.id ? (a(), i("div", Be, [
                s(D) ? (a(), i("div", Ie, [
                  d(s(I), { class: "h-4 w-4 animate-spin text-muted-foreground" })
                ])) : s(u) ? (a(), i(T, { key: 1 }, [
                  s(u).current_file ? (a(), i("div", Le, [
                    t[11] || (t[11] = o("div", { class: "text-xs text-muted-foreground mb-1" }, "当前文件", -1)),
                    o("div", Ne, l(s(u).current_file), 1),
                    o("div", Pe, l(s(u).current_file_done) + " / " + l(s(u).current_file_size) + " bytes ", 1)
                  ])) : m("", !0),
                  s(u).error_message ? (a(), i("div", Re, [
                    t[12] || (t[12] = o("div", { class: "text-xs text-destructive font-medium mb-1" }, "错误信息", -1)),
                    o("pre", $e, l(s(u).error_message), 1)
                  ])) : m("", !0),
                  (r = s(u).files) != null && r.length ? (a(), i("div", Ae, [
                    t[14] || (t[14] = o("div", { class: "text-xs text-muted-foreground mb-2" }, "文件详情", -1)),
                    o("div", Me, [
                      o("table", Ve, [
                        t[13] || (t[13] = o("thead", { class: "bg-secondary/50 sticky top-0" }, [
                          o("tr", null, [
                            o("th", { class: "text-left p-2 font-medium" }, "路径"),
                            o("th", { class: "text-left p-2 font-medium w-20" }, "状态"),
                            o("th", { class: "text-right p-2 font-medium w-28" }, "大小")
                          ])
                        ], -1)),
                        o("tbody", null, [
                          (a(!0), i(T, null, A(s(u).files, (c) => (a(), i("tr", {
                            key: c.path,
                            class: "border-t border-border"
                          }, [
                            o("td", Ee, l(c.path), 1),
                            o("td", Se, [
                              d(s(B), {
                                variant: c.status === "completed" ? "default" : c.status === "failed" ? "destructive" : "outline",
                                class: "text-[10px]"
                              }, {
                                default: p(() => [
                                  f(l(c.status), 1)
                                ]),
                                _: 2
                              }, 1032, ["variant"])
                            ]),
                            o("td", Ue, l(c.done) + "/" + l(c.size), 1)
                          ]))), 128))
                        ])
                      ])
                    ])
                  ])) : m("", !0)
                ], 64)) : m("", !0)
              ])) : m("", !0)
            ]);
          }), 128))
        ]))
      ]),
      d(s(O), {
        open: s(y),
        "onUpdate:open": t[3] || (t[3] = (e) => re(y) ? y.value = e : null),
        "task-id": s(R),
        "work-id": s($),
        "cover-url": s(fe),
        "apply-cover": s(ce),
        onApplied: ne
      }, null, 8, ["open", "task-id", "work-id", "cover-url", "apply-cover"])
    ]));
  }
};
export {
  Qe as default
};
