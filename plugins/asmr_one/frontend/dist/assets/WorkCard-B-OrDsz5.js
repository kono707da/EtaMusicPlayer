import { o as d, c as f, a as t, u as a, k as x, f as w, w as n, d as c, e as k, b as v, t as o } from "./api-BVwVWTpM.js";
import { _ as g } from "./_plugin-vue_export-helper-CHgC5LLL.js";
const h = { class: "aspect-square relative overflow-hidden bg-muted" }, b = ["src", "alt"], _ = { class: "absolute top-2 right-2 flex flex-col gap-1 items-end" }, p = { class: "p-2.5" }, y = { class: "line-clamp-2 text-sm font-medium text-foreground min-h-[2.5rem]" }, B = { class: "mt-1.5 flex items-center justify-between text-xs text-muted-foreground" }, C = { class: "truncate max-w-[60%]" }, N = { class: "mt-1 text-[10px] text-muted-foreground" }, V = {
  __name: "WorkCard",
  props: {
    work: { type: Object, required: !0 }
  },
  emits: ["click"],
  setup(e, { emit: l }) {
    const { Badge: i } = window.__etamusic.ui, u = l;
    function m(r) {
      return r ? r >= 1e4 ? (r / 1e4).toFixed(1) + "w" : r >= 1e3 ? (r / 1e3).toFixed(1) + "k" : String(r) : "0";
    }
    return (r, s) => (d(), f("div", {
      class: "group cursor-pointer rounded-lg border border-border bg-card/40 overflow-hidden transition-all hover:border-primary/60 hover:shadow-lg",
      onClick: s[0] || (s[0] = (j) => u("click", e.work.id))
    }, [
      t("div", h, [
        t("img", {
          src: a(x)(e.work.id),
          alt: e.work.title,
          loading: "lazy",
          class: "absolute inset-0 h-full w-full object-cover transition-transform group-hover:scale-105"
        }, null, 8, b),
        t("div", _, [
          e.work.nsfw ? (d(), w(a(i), {
            key: 0,
            variant: "destructive",
            class: "text-[10px]"
          }, {
            default: n(() => [...s[1] || (s[1] = [
              c("R18", -1)
            ])]),
            _: 1
          })) : k("", !0),
          v(a(i), {
            variant: "secondary",
            class: "text-[10px]"
          }, {
            default: n(() => [
              c(o(m(e.work.dl_count)) + " DL", 1)
            ]),
            _: 1
          })
        ])
      ]),
      t("div", p, [
        t("div", y, o(e.work.title), 1),
        t("div", B, [
          t("span", C, o(e.work.name || "—"), 1),
          t("span", null, "★ " + o(e.work.rate_average_2dp || "—"), 1)
        ]),
        t("div", N, o(e.work.release), 1)
      ])
    ]));
  }
}, D = /* @__PURE__ */ g(V, [["__scopeId", "data-v-422b3e70"]]);
export {
  D as W
};
