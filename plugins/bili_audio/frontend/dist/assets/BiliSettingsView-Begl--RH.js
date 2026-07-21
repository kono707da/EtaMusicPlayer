import { c as y, a as l, u as t, b as o, e as u, w as i, B as S, o as n, f as v, C as z } from "./api-BBDGHqfl.js";
const C = { class: "max-w-2xl mx-auto p-6 space-y-6" }, T = {
  key: 0,
  class: "flex items-center gap-2 text-muted-foreground"
}, A = {
  key: 1,
  class: "space-y-4"
}, E = { class: "space-y-2" }, M = { class: "space-y-2" }, N = { class: "space-y-2" }, I = {
  __name: "BiliSettingsView",
  setup(U) {
    const { ref: p, onMounted: w } = window.__etamusic.vue, { Button: k, Input: m, Label: _, useToast: b } = window.__etamusic.ui, { Save: g, Loader2: f } = window.__etamusic.icons, c = b(), a = p({
      proxy_url: "",
      sessdata: "",
      cache_pool_size_mb: "500"
    }), x = p(!1), r = p(!1);
    async function V() {
      var d, e;
      x.value = !0;
      try {
        const s = await S();
        a.value = {
          proxy_url: s.proxy_url ?? "",
          sessdata: s.sessdata ?? "",
          cache_pool_size_mb: s.cache_pool_size_mb ?? "500"
        };
      } catch (s) {
        c.error("加载失败", ((e = (d = s == null ? void 0 : s.response) == null ? void 0 : d.data) == null ? void 0 : e.detail) || s.message, s);
      } finally {
        x.value = !1;
      }
    }
    async function B() {
      var d, e;
      r.value = !0;
      try {
        const s = [
          { key: "proxy_url", value: a.value.proxy_url },
          { key: "sessdata", value: a.value.sessdata },
          { key: "cache_pool_size_mb", value: a.value.cache_pool_size_mb }
        ];
        await z(s), c.success("设置已保存");
      } catch (s) {
        c.error("保存失败", ((e = (d = s == null ? void 0 : s.response) == null ? void 0 : d.data) == null ? void 0 : e.detail) || s.message, s);
      } finally {
        r.value = !1;
      }
    }
    return w(V), (d, e) => (n(), y("div", C, [
      e[11] || (e[11] = l("h1", { class: "text-2xl font-bold" }, "B站音频设置", -1)),
      t(x) ? (n(), y("div", T, [
        o(t(f), { class: "w-4 h-4 animate-spin" }),
        e[3] || (e[3] = u(" 加载中... ", -1))
      ])) : (n(), y("div", A, [
        l("div", E, [
          o(t(_), null, {
            default: i(() => [...e[4] || (e[4] = [
              u("代理地址", -1)
            ])]),
            _: 1
          }),
          o(t(m), {
            modelValue: t(a).proxy_url,
            "onUpdate:modelValue": e[0] || (e[0] = (s) => t(a).proxy_url = s),
            placeholder: "http://127.0.0.1:7897（留空则不使用代理）"
          }, null, 8, ["modelValue"]),
          e[5] || (e[5] = l("p", { class: "text-xs text-muted-foreground" }, "访问B站API时使用的HTTP代理", -1))
        ]),
        l("div", M, [
          o(t(_), null, {
            default: i(() => [...e[6] || (e[6] = [
              u("SESSDATA Cookie", -1)
            ])]),
            _: 1
          }),
          o(t(m), {
            modelValue: t(a).sessdata,
            "onUpdate:modelValue": e[1] || (e[1] = (s) => t(a).sessdata = s),
            type: "password",
            placeholder: "B站登录Cookie（可选）"
          }, null, 8, ["modelValue"]),
          e[7] || (e[7] = l("p", { class: "text-xs text-muted-foreground" }, " 部分视频需要登录才能获取音频流。从浏览器Cookie中复制SESSDATA值。 ", -1))
        ]),
        l("div", N, [
          o(t(_), null, {
            default: i(() => [...e[8] || (e[8] = [
              u("缓存池大小（MB）", -1)
            ])]),
            _: 1
          }),
          o(t(m), {
            modelValue: t(a).cache_pool_size_mb,
            "onUpdate:modelValue": e[2] || (e[2] = (s) => t(a).cache_pool_size_mb = s),
            type: "number",
            placeholder: "500"
          }, null, 8, ["modelValue"]),
          e[9] || (e[9] = l("p", { class: "text-xs text-muted-foreground" }, " 远程节点下载时，访问端缓存的临时文件最大大小（MB）。超过此大小会暂停下载并上传已有文件。 ", -1))
        ]),
        o(t(k), {
          onClick: B,
          disabled: t(r)
        }, {
          default: i(() => [
            t(r) ? (n(), v(t(f), {
              key: 1,
              class: "w-4 h-4 mr-2 animate-spin"
            })) : (n(), v(t(g), {
              key: 0,
              class: "w-4 h-4 mr-2"
            })),
            e[10] || (e[10] = u(" 保存设置 ", -1))
          ]),
          _: 1
        }, 8, ["disabled"])
      ]))
    ]));
  }
};
export {
  I as default
};
