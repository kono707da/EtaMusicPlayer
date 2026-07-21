import { c as u, a as n, b as o, w as i, u as t, i as B, e as m, F as $, r as z, q as ae, o as r, n as H, t as d, f as V, d as K, s as le, v as se, x as oe, y as ne } from "./api-BBDGHqfl.js";
import { w as ie } from "./runtime-dom.esm-bundler-CkFZlXPX.js";
const re = { class: "max-w-4xl mx-auto p-6 space-y-6" }, de = { class: "flex items-center justify-between" }, ce = { class: "border rounded-lg p-4 space-y-3" }, ue = { class: "flex gap-2" }, me = {
  key: 0,
  class: "flex items-center gap-2 text-muted-foreground py-8 justify-center"
}, pe = {
  key: 1,
  class: "text-center text-muted-foreground py-12 border rounded-lg border-dashed"
}, fe = {
  key: 2,
  class: "space-y-3"
}, _e = { class: "flex items-start justify-between gap-3" }, ve = { class: "flex-1 min-w-0" }, we = { class: "flex items-center gap-2 mb-1" }, ye = { class: "font-medium truncate" }, he = { class: "text-sm text-muted-foreground" }, ge = { class: "flex items-center gap-1 shrink-0" }, xe = { class: "flex items-center gap-4 text-xs text-muted-foreground" }, ke = { key: 0 }, Ce = {
  key: 0,
  class: "text-xs text-muted-foreground bg-muted/50 rounded px-2 py-1"
}, ze = {
  __name: "BiliSubscriptionView",
  setup(be) {
    const { ref: f, reactive: L, onMounted: O } = window.__etamusic.vue, {
      Button: w,
      Input: P,
      Label: E,
      Select: M,
      SelectContent: T,
      SelectItem: U,
      SelectTrigger: A,
      SelectValue: D,
      useToast: Q
    } = window.__etamusic.ui, { BookmarkIcon: N, Loader2: S, RefreshCw: R, Trash2: X, CheckCircle: Ve, XCircle: Se } = window.__etamusic.icons, c = Q(), k = f([]), y = f(!1), _ = f(!1), p = f(""), C = f("30280"), b = f("mp3"), h = L({}), v = L({}), G = [
      { value: "30216", label: "64kbps" },
      { value: "30232", label: "132kbps" },
      { value: "30280", label: "192kbps（推荐）" },
      { value: "30251", label: "Hi-Res 无损" }
    ], J = [
      { value: "mp3", label: "MP3" },
      { value: "m4a", label: "M4A (AAC)" }
    ], W = { 30216: "64kbps", 30232: "132kbps", 30280: "192kbps", 30250: "Dolby", 30251: "Hi-Res" }, Y = (l) => W[l] || `${l}kbps`, j = {
      active: { label: "正常", color: "text-green-500" },
      error: { label: "错误", color: "text-red-500" },
      paused: { label: "已暂停", color: "text-muted-foreground" }
    };
    function Z(l) {
      if (!l) return "-";
      try {
        return new Date(l).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
      } catch {
        return l;
      }
    }
    async function g() {
      var l, a;
      y.value = !0;
      try {
        const e = await ae();
        k.value = e.items || [];
      } catch (e) {
        c.error("获取订阅列表失败", ((a = (l = e == null ? void 0 : e.response) == null ? void 0 : l.data) == null ? void 0 : a.detail) || e.message, e);
      } finally {
        y.value = !1;
      }
    }
    async function q() {
      var l, a;
      if (!(!p.value.trim() || _.value)) {
        _.value = !0;
        try {
          await le({
            url: p.value.trim(),
            auto_download: !0,
            audio_quality: parseInt(C.value),
            output_format: b.value
          }), p.value = "", c.success("订阅添加成功"), await g();
        } catch (e) {
          c.error("添加订阅失败", ((a = (l = e == null ? void 0 : e.response) == null ? void 0 : l.data) == null ? void 0 : a.detail) || e.message, e);
        } finally {
          _.value = !1;
        }
      }
    }
    async function I(l) {
      var a, e;
      h[l] = !0, v[l] = "";
      try {
        const s = await se(l);
        s.error ? (v[l] = `检查失败: ${s.error}`, c.error("检查更新失败", s.error)) : (v[l] = `发现 ${s.total_archives || 0} 个视频，新增下载 ${s.new_downloads || 0} 个`, c.success("检查完成", `新增下载 ${s.new_downloads || 0} 个`)), await g();
      } catch (s) {
        const x = ((e = (a = s == null ? void 0 : s.response) == null ? void 0 : a.data) == null ? void 0 : e.detail) || s.message;
        v[l] = `检查失败: ${x}`, c.error("检查更新失败", x, s);
      } finally {
        h[l] = !1;
      }
    }
    async function ee(l) {
      var a, e;
      try {
        await oe(l.id, { auto_download: !l.auto_download }), l.auto_download = !l.auto_download, c.success(l.auto_download ? "已开启自动下载" : "已关闭自动下载");
      } catch (s) {
        c.error("更新订阅失败", ((e = (a = s == null ? void 0 : s.response) == null ? void 0 : a.data) == null ? void 0 : e.detail) || s.message, s);
      }
    }
    async function te(l) {
      var a, e;
      try {
        await ne(l), c.success("订阅已删除"), await g();
      } catch (s) {
        c.error("删除订阅失败", ((e = (a = s == null ? void 0 : s.response) == null ? void 0 : a.data) == null ? void 0 : e.detail) || s.message, s);
      }
    }
    return O(g), (l, a) => (r(), u("div", re, [
      n("div", de, [
        a[4] || (a[4] = n("h1", { class: "text-2xl font-bold" }, "订阅管理", -1)),
        o(t(w), {
          variant: "outline",
          size: "sm",
          onClick: g,
          disabled: t(y)
        }, {
          default: i(() => [
            o(t(R), {
              class: H(["w-4 h-4 mr-1", { "animate-spin": t(y) }])
            }, null, 8, ["class"]),
            a[3] || (a[3] = m(" 刷新 ", -1))
          ]),
          _: 1
        }, 8, ["disabled"])
      ]),
      n("div", ce, [
        o(t(E), { class: "text-sm font-medium" }, {
          default: i(() => [...a[5] || (a[5] = [
            m("添加订阅", -1)
          ])]),
          _: 1
        }),
        n("div", ue, [
          o(t(P), {
            modelValue: t(p),
            "onUpdate:modelValue": a[0] || (a[0] = (e) => B(p) ? p.value = e : null),
            placeholder: "输入B站合集链接，如 https://space.bilibili.com/27492426/lists/506549",
            class: "flex-1",
            onKeyup: ie(q, ["enter"])
          }, null, 8, ["modelValue"]),
          o(t(M), {
            modelValue: t(C),
            "onUpdate:modelValue": a[1] || (a[1] = (e) => B(C) ? C.value = e : null)
          }, {
            default: i(() => [
              o(t(A), { class: "w-[160px]" }, {
                default: i(() => [
                  o(t(D), { placeholder: "音质" })
                ]),
                _: 1
              }),
              o(t(T), null, {
                default: i(() => [
                  (r(), u($, null, z(G, (e) => o(t(U), {
                    key: e.value,
                    value: e.value
                  }, {
                    default: i(() => [
                      m(d(e.label), 1)
                    ]),
                    _: 2
                  }, 1032, ["value"])), 64))
                ]),
                _: 1
              })
            ]),
            _: 1
          }, 8, ["modelValue"]),
          o(t(M), {
            modelValue: t(b),
            "onUpdate:modelValue": a[2] || (a[2] = (e) => B(b) ? b.value = e : null)
          }, {
            default: i(() => [
              o(t(A), { class: "w-[120px]" }, {
                default: i(() => [
                  o(t(D), { placeholder: "格式" })
                ]),
                _: 1
              }),
              o(t(T), null, {
                default: i(() => [
                  (r(), u($, null, z(J, (e) => o(t(U), {
                    key: e.value,
                    value: e.value
                  }, {
                    default: i(() => [
                      m(d(e.label), 1)
                    ]),
                    _: 2
                  }, 1032, ["value"])), 64))
                ]),
                _: 1
              })
            ]),
            _: 1
          }, 8, ["modelValue"]),
          o(t(w), {
            onClick: q,
            disabled: !t(p).trim() || t(_)
          }, {
            default: i(() => [
              t(_) ? (r(), V(t(S), {
                key: 0,
                class: "w-4 h-4 mr-2 animate-spin"
              })) : (r(), V(t(N), {
                key: 1,
                class: "w-4 h-4 mr-2"
              })),
              m(" " + d(t(_) ? "添加中..." : "添加"), 1)
            ]),
            _: 1
          }, 8, ["disabled"])
        ])
      ]),
      t(y) && t(k).length === 0 ? (r(), u("div", me, [
        o(t(S), { class: "w-5 h-5 animate-spin" }),
        a[6] || (a[6] = m(" 加载中... ", -1))
      ])) : t(k).length === 0 ? (r(), u("div", pe, [
        o(t(N), { class: "w-12 h-12 mx-auto mb-3 opacity-30" }),
        a[7] || (a[7] = n("p", null, "暂无订阅，请添加B站合集链接", -1))
      ])) : (r(), u("div", fe, [
        (r(!0), u($, null, z(t(k), (e) => {
          var s, x;
          return r(), u("div", {
            key: e.id,
            class: "border rounded-lg p-4 hover:bg-accent/50 transition-colors space-y-2"
          }, [
            n("div", _e, [
              n("div", ve, [
                n("div", we, [
                  n("span", ye, d(e.title || "未命名合集"), 1),
                  n("span", {
                    class: H([(s = j[e.status]) == null ? void 0 : s.color, "text-xs font-medium"])
                  }, d(((x = j[e.status]) == null ? void 0 : x.label) || e.status), 3)
                ]),
                n("p", he, d(e.upper_name || "未知UP主"), 1)
              ]),
              n("div", ge, [
                o(t(w), {
                  variant: "outline",
                  size: "sm",
                  onClick: (F) => I(e.id),
                  disabled: t(h)[e.id]
                }, {
                  default: i(() => [
                    t(h)[e.id] ? (r(), V(t(S), {
                      key: 0,
                      class: "w-3 h-3 mr-1 animate-spin"
                    })) : (r(), V(t(R), {
                      key: 1,
                      class: "w-3 h-3 mr-1"
                    })),
                    m(" " + d(t(h)[e.id] ? "检查中..." : "检查更新"), 1)
                  ]),
                  _: 2
                }, 1032, ["onClick", "disabled"]),
                o(t(w), {
                  variant: e.auto_download ? "default" : "outline",
                  size: "sm",
                  onClick: (F) => ee(e)
                }, {
                  default: i(() => [
                    m(d(e.auto_download ? "自动下载" : "手动"), 1)
                  ]),
                  _: 2
                }, 1032, ["variant", "onClick"]),
                o(t(w), {
                  variant: "ghost",
                  size: "icon",
                  onClick: (F) => te(e.id),
                  title: "删除"
                }, {
                  default: i(() => [
                    o(t(X), { class: "w-4 h-4 text-red-500" })
                  ]),
                  _: 1
                }, 8, ["onClick"])
              ])
            ]),
            n("div", xe, [
              n("span", null, "视频: " + d(e.downloaded_count ?? 0) + "/" + d(e.video_count ?? 0), 1),
              n("span", null, "音质: " + d(Y(e.audio_quality)), 1),
              n("span", null, "格式: " + d((e.output_format || "mp3").toUpperCase()), 1),
              e.last_checked_at ? (r(), u("span", ke, "上次检查: " + d(Z(e.last_checked_at)), 1)) : K("", !0)
            ]),
            t(v)[e.id] ? (r(), u("div", Ce, d(t(v)[e.id]), 1)) : K("", !0)
          ]);
        }), 128))
      ]))
    ]));
  }
};
export {
  ze as default
};
