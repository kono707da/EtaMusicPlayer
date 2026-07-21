import { c as o, a as r, b as a, u as e, d as m, e as u, t as D, f, w as d, F as X, r as Y, i as Z, o as s, n as ee, g as te, h as se, p as oe } from "./api-D4goXXVb.js";
import { u as re } from "./store-C7cC6z1j.js";
import { w as ne } from "./runtime-dom.esm-bundler-fg28wYCK.js";
const le = { class: "flex h-full flex-col" }, ie = { class: "flex items-center gap-3 mb-4" }, ae = { class: "flex-1 min-h-0 overflow-auto" }, de = {
  key: 0,
  class: "flex flex-col gap-4 max-w-2xl"
}, ce = { class: "rounded-lg border border-border bg-card/40 p-4 flex items-center gap-4" }, ue = ["src"], fe = {
  key: 1,
  class: "h-14 w-14 rounded-full bg-primary/20 flex items-center justify-center"
}, me = { class: "flex-1 min-w-0" }, _e = { class: "font-medium truncate" }, xe = { class: "text-sm text-muted-foreground" }, ge = {
  key: 0,
  class: "rounded-lg border border-border bg-card/40"
}, ve = ["onClick"], pe = ["src"], ye = {
  key: 1,
  class: "h-10 w-10 rounded-full bg-muted flex items-center justify-center"
}, he = { class: "flex-1 min-w-0" }, ke = { class: "font-medium truncate" }, be = { class: "text-xs text-muted-foreground" }, we = {
  key: 1,
  class: "flex items-start justify-center pt-4"
}, Ce = { class: "w-full max-w-md rounded-lg border border-border bg-card/40 p-6 flex flex-col gap-5 shadow-sm" }, De = { class: "text-center" }, je = { class: "flex flex-col items-center gap-3" }, Ae = { class: "relative w-64 h-64 border border-border rounded-lg overflow-hidden bg-white flex items-center justify-center" }, Ie = ["src"], Ue = {
  key: 2,
  class: "absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 text-white"
}, Se = {
  key: 3,
  class: "absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 text-white"
}, ze = { class: "text-sm text-center min-h-[20px]" }, Le = {
  key: 0,
  class: "text-muted-foreground"
}, Te = {
  key: 1,
  class: "text-primary"
}, Be = {
  key: 2,
  class: "text-primary"
}, Ne = {
  key: 3,
  class: "text-destructive"
}, Ve = {
  key: 4,
  class: "text-destructive"
}, Qe = { class: "flex flex-col items-center gap-3 py-2" }, qe = { class: "relative w-64 h-64 border border-border rounded-lg overflow-hidden bg-white flex items-center justify-center" }, $e = ["src"], Me = {
  key: 2,
  class: "absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 text-white"
}, Pe = {
  key: 3,
  class: "absolute inset-0 bg-black/60 flex flex-col items-center justify-center gap-2 text-white"
}, Fe = { class: "text-sm text-center min-h-[20px]" }, Re = {
  key: 0,
  class: "text-muted-foreground"
}, Ee = {
  key: 1,
  class: "text-primary"
}, He = {
  key: 2,
  class: "text-primary"
}, Ke = {
  key: 3,
  class: "text-destructive"
}, Ge = {
  key: 4,
  class: "text-destructive"
}, Ye = {
  __name: "NeteaseAccountView",
  setup(Je) {
    const { ref: g, onMounted: V, onUnmounted: Q } = window.__etamusic.vue, { Music: A, User: I, QrCode: q, RefreshCw: h, Loader2: U, CheckCircle2: S, Trash2: $ } = window.__etamusic.icons, {
      Button: v,
      Badge: z,
      Dialog: M,
      DialogContent: P,
      DialogHeader: F,
      DialogTitle: R,
      DialogDescription: E,
      useToast: H
    } = window.__etamusic.ui, _ = H(), l = re(), j = g(!1), y = g(!1), x = g(""), k = g(""), i = g(0), b = g(!1);
    let w = null;
    function K() {
      y.value = !0, C();
    }
    async function C() {
      p(), x.value = "", i.value = 0, b.value = !0;
      try {
        const n = await te();
        if (!n.unikey) {
          _.error("获取二维码 key 失败", "后端未返回 unikey");
          return;
        }
        k.value = n.unikey, x.value = se(n.unikey), i.value = 801, G();
      } catch (n) {
        _.error("二维码登录启动失败", n.message || String(n)), i.value = 0;
      } finally {
        b.value = !1;
      }
    }
    function G() {
      p(), w = setInterval(async () => {
        if (!k.value) {
          p();
          return;
        }
        try {
          const n = await oe(k.value);
          i.value = n.code || 0, n.code === 803 ? (p(), _.success("网易云登录成功"), await l.onLoginSuccess(), y.value = !1, x.value = "", k.value = "") : (n.code === 800 || n.code === 8821) && p();
        } catch (n) {
          console.error("轮询扫码状态失败:", n);
        }
      }, 2e3);
    }
    function p() {
      w && (clearInterval(w), w = null);
    }
    async function J(n) {
      if (n !== l.currentUid)
        try {
          await l.switchTo(n), _.success("已切换账号");
        } catch (t) {
          _.error("切换账号失败", t.message || String(t));
        }
    }
    async function O(n) {
      if (confirm(`确定要删除账号「${n.nickname}」吗？
删除后需要重新扫码登录。`))
        try {
          await l.remove(n.ncm_uid), _.success("已删除账号");
        } catch (t) {
          _.error("删除账号失败", t.message || String(t));
        }
    }
    return V(() => {
      l.loaded || l.load();
    }), Q(() => {
      p();
    }), (n, t) => {
      var L, T, B, N;
      return s(), o("div", le, [
        r("div", ie, [
          a(e(A), { class: "h-5 w-5 text-primary" }),
          t[3] || (t[3] = r("h2", { class: "text-lg font-semibold" }, "网易云账号", -1)),
          e(l).isLoggedIn ? (s(), m(e(v), {
            key: 0,
            variant: "ghost",
            size: "sm",
            onClick: t[0] || (t[0] = (c) => {
              j.value = !0, e(l).refresh().finally(() => j.value = !1);
            })
          }, {
            default: d(() => [
              e(j) ? (s(), m(e(h), {
                key: 0,
                class: "h-4 w-4 animate-spin"
              })) : (s(), m(e(h), {
                key: 1,
                class: "h-4 w-4"
              })),
              t[2] || (t[2] = f(" 刷新 ", -1))
            ]),
            _: 1
          })) : u("", !0)
        ]),
        r("div", ae, [
          e(l).isLoggedIn ? (s(), o("div", de, [
            r("div", ce, [
              (L = e(l).currentAccount) != null && L.avatar_url ? (s(), o("img", {
                key: 0,
                src: e(l).currentAccount.avatar_url,
                class: "h-14 w-14 rounded-full border border-border",
                referrerpolicy: "no-referrer"
              }, null, 8, ue)) : (s(), o("div", fe, [
                a(e(I), { class: "h-7 w-7 text-primary" })
              ])),
              r("div", me, [
                r("div", _e, D(((T = e(l).currentAccount) == null ? void 0 : T.nickname) || "未知"), 1),
                r("div", xe, [
                  f(" UID: " + D((B = e(l).currentAccount) == null ? void 0 : B.ncm_uid) + " ", 1),
                  ((N = e(l).currentAccount) == null ? void 0 : N.vip_type) > 0 ? (s(), m(e(z), {
                    key: 0,
                    variant: "gold",
                    class: "ml-2"
                  }, {
                    default: d(() => [...t[4] || (t[4] = [
                      f("VIP", -1)
                    ])]),
                    _: 1
                  })) : u("", !0)
                ])
              ]),
              a(e(v), {
                variant: "outline",
                size: "sm",
                onClick: K
              }, {
                default: d(() => [
                  a(e(q), { class: "h-4 w-4" }),
                  t[5] || (t[5] = f(" 添加账号 ", -1))
                ]),
                _: 1
              })
            ]),
            e(l).accounts.length > 1 ? (s(), o("div", ge, [
              t[7] || (t[7] = r("div", { class: "px-4 py-2 text-sm text-muted-foreground border-b border-border" }, "所有账号（点击切换）", -1)),
              (s(!0), o(X, null, Y(e(l).accounts, (c) => (s(), o("div", {
                key: c.ncm_uid,
                class: ee(["px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-accent/50 transition-colors border-b border-border last:border-b-0", { "bg-primary/10": c.ncm_uid === e(l).currentUid }]),
                onClick: (W) => J(c.ncm_uid)
              }, [
                c.avatar_url ? (s(), o("img", {
                  key: 0,
                  src: c.avatar_url,
                  class: "h-10 w-10 rounded-full",
                  referrerpolicy: "no-referrer"
                }, null, 8, pe)) : (s(), o("div", ye, [
                  a(e(I), { class: "h-5 w-5 text-muted-foreground" })
                ])),
                r("div", he, [
                  r("div", ke, D(c.nickname || "未知"), 1),
                  r("div", be, "UID: " + D(c.ncm_uid), 1)
                ]),
                c.ncm_uid === e(l).currentUid ? (s(), m(e(z), {
                  key: 2,
                  variant: "gold"
                }, {
                  default: d(() => [...t[6] || (t[6] = [
                    f("当前", -1)
                  ])]),
                  _: 1
                })) : u("", !0),
                a(e(v), {
                  variant: "ghost",
                  size: "sm",
                  class: "text-destructive hover:text-destructive",
                  onClick: ne((W) => O(c), ["stop"])
                }, {
                  default: d(() => [
                    a(e($), { class: "h-4 w-4" })
                  ]),
                  _: 1
                }, 8, ["onClick"])
              ], 10, ve))), 128))
            ])) : u("", !0)
          ])) : (s(), o("div", we, [
            r("div", Ce, [
              r("div", De, [
                a(e(A), { class: "h-10 w-10 text-primary mx-auto mb-2" }),
                t[8] || (t[8] = r("h3", { class: "text-lg font-semibold" }, "扫码登录网易云音乐", -1)),
                t[9] || (t[9] = r("p", { class: "text-sm text-muted-foreground mt-1" }, "使用网易云 App 扫描下方二维码", -1))
              ]),
              r("div", je, [
                r("div", Ae, [
                  e(x) ? (s(), o("img", {
                    key: 0,
                    src: e(x),
                    class: "w-full h-full object-contain",
                    alt: "登录二维码"
                  }, null, 8, Ie)) : (s(), m(e(U), {
                    key: 1,
                    class: "h-8 w-8 animate-spin text-muted-foreground"
                  })),
                  e(i) === 800 ? (s(), o("div", Ue, [
                    t[11] || (t[11] = r("p", { class: "text-sm" }, "二维码已过期", -1)),
                    a(e(v), {
                      variant: "gold",
                      size: "sm",
                      onClick: C
                    }, {
                      default: d(() => [...t[10] || (t[10] = [
                        f("重新生成", -1)
                      ])]),
                      _: 1
                    })
                  ])) : u("", !0),
                  e(i) === 802 ? (s(), o("div", Se, [
                    a(e(S), { class: "h-8 w-8" }),
                    t[12] || (t[12] = r("p", { class: "text-sm" }, "已扫码，请在手机上确认", -1))
                  ])) : u("", !0)
                ]),
                r("div", ze, [
                  e(i) === 801 ? (s(), o("span", Le, "等待扫码...")) : e(i) === 802 ? (s(), o("span", Te, "已扫码，等待确认")) : e(i) === 803 ? (s(), o("span", Be, "登录成功！")) : e(i) === 800 ? (s(), o("span", Ne, "二维码已过期")) : e(i) === 8821 ? (s(), o("span", Ve, "风控拒绝，请稍后重试")) : u("", !0)
                ])
              ]),
              a(e(v), {
                variant: "ghost",
                size: "sm",
                onClick: C,
                disabled: e(b)
              }, {
                default: d(() => [
                  e(b) ? (s(), m(e(h), {
                    key: 0,
                    class: "h-4 w-4 animate-spin"
                  })) : (s(), m(e(h), {
                    key: 1,
                    class: "h-4 w-4"
                  })),
                  t[13] || (t[13] = f(" 刷新二维码 ", -1))
                ]),
                _: 1
              }, 8, ["disabled"])
            ])
          ])),
          a(e(M), {
            open: e(y),
            "onUpdate:open": t[1] || (t[1] = (c) => Z(y) ? y.value = c : null)
          }, {
            default: d(() => [
              a(e(P), { class: "max-w-md" }, {
                default: d(() => [
                  a(e(F), null, {
                    default: d(() => [
                      a(e(R), null, {
                        default: d(() => [...t[14] || (t[14] = [
                          f("添加网易云账号", -1)
                        ])]),
                        _: 1
                      }),
                      a(e(E), null, {
                        default: d(() => [...t[15] || (t[15] = [
                          f("扫描二维码登录新账号，登录后可免扫码切换", -1)
                        ])]),
                        _: 1
                      })
                    ]),
                    _: 1
                  }),
                  r("div", Qe, [
                    r("div", qe, [
                      e(x) ? (s(), o("img", {
                        key: 0,
                        src: e(x),
                        class: "w-full h-full object-contain",
                        alt: "登录二维码"
                      }, null, 8, $e)) : (s(), m(e(U), {
                        key: 1,
                        class: "h-8 w-8 animate-spin text-muted-foreground"
                      })),
                      e(i) === 800 ? (s(), o("div", Me, [
                        t[17] || (t[17] = r("p", { class: "text-sm" }, "二维码已过期", -1)),
                        a(e(v), {
                          variant: "gold",
                          size: "sm",
                          onClick: C
                        }, {
                          default: d(() => [...t[16] || (t[16] = [
                            f("重新生成", -1)
                          ])]),
                          _: 1
                        })
                      ])) : u("", !0),
                      e(i) === 802 ? (s(), o("div", Pe, [
                        a(e(S), { class: "h-8 w-8" }),
                        t[18] || (t[18] = r("p", { class: "text-sm" }, "已扫码，请在手机上确认", -1))
                      ])) : u("", !0)
                    ]),
                    r("div", Fe, [
                      e(i) === 801 ? (s(), o("span", Re, "等待扫码...")) : e(i) === 802 ? (s(), o("span", Ee, "已扫码，等待确认")) : e(i) === 803 ? (s(), o("span", He, "登录成功！")) : e(i) === 800 ? (s(), o("span", Ke, "二维码已过期")) : e(i) === 8821 ? (s(), o("span", Ge, "风控拒绝，请稍后重试")) : u("", !0)
                    ])
                  ])
                ]),
                _: 1
              })
            ]),
            _: 1
          }, 8, ["open"])
        ])
      ]);
    };
  }
};
export {
  Ye as default
};
