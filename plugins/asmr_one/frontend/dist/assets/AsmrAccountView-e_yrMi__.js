import { c as p, a as s, b as l, u as e, t as w, d as n, f as j, w as u, e as _, n as z, i as C, F as G, o as m } from "./api-BVwVWTpM.js";
import { u as J } from "./store-KZ0YZNeM.js";
import { w as I } from "./runtime-dom.esm-bundler-KgcpFXTz.js";
const P = { class: "flex h-full flex-col" }, Q = { class: "flex items-center gap-3 mb-4" }, W = { class: "flex-1 min-h-0 flex items-start justify-center pt-4" }, X = {
  key: 0,
  class: "w-full max-w-md rounded-lg border border-border bg-card/40 p-6 flex flex-col gap-5 shadow-sm"
}, Y = { class: "flex items-center gap-3" }, Z = { class: "h-14 w-14 rounded-full bg-primary/20 flex items-center justify-center" }, ee = { class: "flex-1" }, te = { class: "text-base font-medium text-foreground" }, se = { class: "text-xs text-muted-foreground mt-0.5" }, le = {
  key: 0,
  class: "text-sm text-muted-foreground"
}, oe = { class: "flex gap-2 pt-1" }, ae = {
  key: 1,
  class: "w-full max-w-md rounded-lg border border-border bg-card/40 p-6 flex flex-col gap-5 shadow-sm"
}, ne = { class: "text-center" }, re = { class: "inline-flex h-12 w-12 rounded-full bg-primary/15 items-center justify-center mb-3" }, ue = { class: "text-lg font-medium text-foreground" }, de = { class: "flex items-center justify-center gap-2" }, ie = { class: "flex flex-col gap-3" }, me = { class: "flex flex-col gap-1.5" }, ce = { class: "flex flex-col gap-1.5" }, fe = { class: "flex flex-col gap-1.5" }, xe = { class: "flex flex-col gap-1.5" }, _e = {
  __name: "AsmrAccountView",
  setup(pe) {
    const { ref: f, onMounted: M } = window.__etamusic.vue, { useRouter: N } = window.__etamusic.vueRouter, { Button: y, Input: b, Label: h, Badge: D, useToast: F } = window.__etamusic.ui, { User: R, LogOut: K, Loader2: E, Heart: T, Star: $ } = window.__etamusic.icons, B = N(), x = F(), o = J(), a = f(!1), c = f(""), d = f(""), v = f(""), g = f(""), V = f(!1);
    async function U() {
      var A, t;
      if (!c.value || !d.value) {
        x.warning("请输入用户名和密码");
        return;
      }
      if (a.value && d.value !== v.value) {
        x.warning("两次密码不一致");
        return;
      }
      V.value = !0;
      try {
        a.value ? (await o.register(c.value, d.value, g.value || null), x.success("注册成功，已自动登录")) : (await o.login(c.value, d.value), x.success("登录成功")), c.value = "", d.value = "", v.value = "", g.value = "";
      } catch (i) {
        const k = ((t = (A = i == null ? void 0 : i.response) == null ? void 0 : A.data) == null ? void 0 : t.detail) || i.message;
        x.error(a.value ? "注册失败" : "登录失败", k, i);
      } finally {
        V.value = !1;
      }
    }
    async function H() {
      await o.logout(), x.success("已退出登录");
    }
    function O() {
      B.push("/asmr/reviews");
    }
    function q() {
      B.push("/asmr/favorites");
    }
    return M(() => {
      o.loaded || o.load();
    }), (A, t) => {
      var i, k, S, L;
      return m(), p("div", P, [
        s("div", Q, [
          l(e(R), { class: "h-5 w-5 text-primary" }),
          t[6] || (t[6] = s("h2", { class: "text-lg font-semibold" }, "ASMR 账户", -1))
        ]),
        s("div", W, [
          e(o).isLoggedIn ? (m(), p("div", X, [
            s("div", Y, [
              s("div", Z, [
                l(e(R), { class: "h-7 w-7 text-primary" })
              ]),
              s("div", ee, [
                s("div", te, w(((i = e(o).user) == null ? void 0 : i.name) || "—"), 1),
                s("div", se, [
                  n(" ID: " + w(((k = e(o).user) == null ? void 0 : k.id) || "—") + " ", 1),
                  ((S = e(o).user) == null ? void 0 : S.role) === 1 ? (m(), j(e(D), {
                    key: 0,
                    variant: "gold",
                    class: "ml-2 text-[10px]"
                  }, {
                    default: u(() => [...t[7] || (t[7] = [
                      n("管理员", -1)
                    ])]),
                    _: 1
                  })) : _("", !0)
                ])
              ])
            ]),
            (L = e(o).user) != null && L.email ? (m(), p("div", le, " 邮箱：" + w(e(o).user.email), 1)) : _("", !0),
            s("div", oe, [
              l(e(y), {
                variant: "gold",
                size: "sm",
                onClick: q
              }, {
                default: u(() => [
                  l(e(T), { class: "h-4 w-4" }),
                  t[8] || (t[8] = n(" 我的收藏 ", -1))
                ]),
                _: 1
              }),
              l(e(y), {
                variant: "outline",
                size: "sm",
                onClick: O
              }, {
                default: u(() => [
                  l(e($), { class: "h-4 w-4" }),
                  t[9] || (t[9] = n(" 我的评价 ", -1))
                ]),
                _: 1
              }),
              l(e(y), {
                variant: "ghost",
                size: "sm",
                class: "ml-auto text-destructive",
                onClick: H
              }, {
                default: u(() => [
                  l(e(K), { class: "h-4 w-4" }),
                  t[10] || (t[10] = n(" 退出登录 ", -1))
                ]),
                _: 1
              })
            ])
          ])) : (m(), p("div", ae, [
            s("div", ne, [
              s("div", re, [
                l(e(R), { class: "h-6 w-6 text-primary" })
              ]),
              s("h3", ue, w(e(a) ? "注册 ASMR 账户" : "登录 ASMR 账户"), 1),
              t[11] || (t[11] = s("p", { class: "text-xs text-muted-foreground mt-1" }, " 登录后可使用收藏、评价、个性化推荐等功能 ", -1))
            ]),
            s("div", de, [
              s("button", {
                class: z(["text-sm px-4 py-1.5 rounded-md transition-colors", e(a) ? "text-muted-foreground hover:bg-accent" : "bg-primary text-primary-foreground"]),
                onClick: t[0] || (t[0] = (r) => a.value = !1)
              }, " 登录 ", 2),
              e(o).regEnabled ? (m(), p("button", {
                key: 0,
                class: z(["text-sm px-4 py-1.5 rounded-md transition-colors", e(a) ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"]),
                onClick: t[1] || (t[1] = (r) => a.value = !0)
              }, " 注册 ", 2)) : _("", !0)
            ]),
            s("div", ie, [
              s("div", me, [
                l(e(h), null, {
                  default: u(() => [...t[12] || (t[12] = [
                    n("用户名", -1)
                  ])]),
                  _: 1
                }),
                l(e(b), {
                  modelValue: e(c),
                  "onUpdate:modelValue": t[2] || (t[2] = (r) => C(c) ? c.value = r : null),
                  placeholder: "用户名",
                  class: "h-9",
                  onKeyup: I(U, ["enter"])
                }, null, 8, ["modelValue"])
              ]),
              s("div", ce, [
                l(e(h), null, {
                  default: u(() => [...t[13] || (t[13] = [
                    n("密码", -1)
                  ])]),
                  _: 1
                }),
                l(e(b), {
                  modelValue: e(d),
                  "onUpdate:modelValue": t[3] || (t[3] = (r) => C(d) ? d.value = r : null),
                  type: "password",
                  placeholder: "密码",
                  class: "h-9",
                  onKeyup: I(U, ["enter"])
                }, null, 8, ["modelValue"])
              ]),
              e(a) ? (m(), p(G, { key: 0 }, [
                s("div", fe, [
                  l(e(h), null, {
                    default: u(() => [...t[14] || (t[14] = [
                      n("确认密码", -1)
                    ])]),
                    _: 1
                  }),
                  l(e(b), {
                    modelValue: e(v),
                    "onUpdate:modelValue": t[4] || (t[4] = (r) => C(v) ? v.value = r : null),
                    type: "password",
                    placeholder: "再次输入密码",
                    class: "h-9"
                  }, null, 8, ["modelValue"])
                ]),
                s("div", xe, [
                  l(e(h), null, {
                    default: u(() => [...t[15] || (t[15] = [
                      n("推荐人 UUID（可选）", -1)
                    ])]),
                    _: 1
                  }),
                  l(e(b), {
                    modelValue: e(g),
                    "onUpdate:modelValue": t[5] || (t[5] = (r) => C(g) ? g.value = r : null),
                    placeholder: "可选",
                    class: "h-9"
                  }, null, 8, ["modelValue"])
                ])
              ], 64)) : _("", !0),
              l(e(y), {
                variant: "gold",
                disabled: e(V),
                class: "mt-1",
                onClick: U
              }, {
                default: u(() => [
                  e(V) ? (m(), j(e(E), {
                    key: 0,
                    class: "h-4 w-4 animate-spin"
                  })) : _("", !0),
                  n(" " + w(e(a) ? "注册并登录" : "登录"), 1)
                ]),
                _: 1
              }, 8, ["disabled"])
            ]),
            t[16] || (t[16] = s("p", { class: "text-xs text-muted-foreground text-center" }, " 账户信息存储在后端数据库中，用于访问 asmr.one 的收藏/评价/推荐等功能。 ", -1))
          ]))
        ])
      ]);
    };
  }
};
export {
  _e as default
};
