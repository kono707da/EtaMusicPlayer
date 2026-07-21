import { c as r, a as n, b as a, w as s, u as e, i as _, t as i, d as g, g as Y, o as u, e as d, f as y, F as M, r as N, p as Z, h as ee } from "./api-BBDGHqfl.js";
import { w as le } from "./runtime-dom.esm-bundler-CkFZlXPX.js";
const te = { class: "max-w-3xl mx-auto p-6 space-y-6" }, ae = { class: "flex items-center justify-between" }, se = { class: "flex gap-2" }, ue = { class: "space-y-4" }, oe = { class: "space-y-2" }, ne = { class: "flex gap-2" }, de = {
  key: 0,
  class: "text-red-500 text-sm"
}, re = {
  key: 0,
  class: "border rounded-lg p-4 space-y-4"
}, ie = { class: "flex gap-4" }, pe = ["src"], me = { class: "flex-1 min-w-0" }, ve = { class: "text-lg font-semibold truncate" }, ce = {
  key: 0,
  class: "text-sm text-muted-foreground mt-1"
}, fe = {
  key: 1,
  class: "text-sm text-muted-foreground"
}, _e = ["href"], ge = {
  key: 0,
  class: "space-y-2"
}, ye = { class: "grid grid-cols-2 gap-4" }, be = { class: "space-y-2" }, we = { class: "space-y-2" }, xe = { class: "grid grid-cols-2 gap-4" }, ke = { class: "space-y-2" }, Ve = { class: "space-y-2" }, he = {
  key: 1,
  class: "text-center text-muted-foreground py-12 border rounded-lg border-dashed"
}, Ue = {
  __name: "BiliDownloadView",
  setup(Be) {
    const { ref: p, computed: Se } = window.__etamusic.vue, { useRouter: j } = window.__etamusic.vueRouter, {
      Button: w,
      Input: A,
      Label: f,
      Select: x,
      SelectContent: k,
      SelectItem: V,
      SelectTrigger: h,
      SelectValue: B,
      useToast: K
    } = window.__etamusic.ui, { Download: O, Loader2: E, Link: W, Music: $, Settings: H, List: Q } = window.__etamusic.icons, R = j(), T = K(), v = p(""), S = p(!1), C = p(!1), o = p(null), D = p(""), U = p([]), b = p(0), P = p("30280"), I = p("mp3"), c = p(""), L = p("B站音频"), q = [
      { value: "30216", label: "64kbps" },
      { value: "30232", label: "132kbps" },
      { value: "30280", label: "192kbps（推荐）" },
      { value: "30251", label: "Hi-Res 无损" }
    ], G = [
      { value: "mp3", label: "MP3" },
      { value: "m4a", label: "M4A (AAC)" }
    ];
    async function F() {
      var m, l;
      if (!v.value.trim()) {
        T.error("请输入B站视频链接");
        return;
      }
      S.value = !0, D.value = "", o.value = null;
      try {
        const t = await Z(v.value.trim());
        o.value = t, t.pages && t.pages.length > 1 && (b.value = 0);
      } catch (t) {
        D.value = ((l = (m = t == null ? void 0 : t.response) == null ? void 0 : m.data) == null ? void 0 : l.detail) || t.message || "解析失败";
      } finally {
        S.value = !1;
      }
    }
    async function J() {
      var m, l;
      if (o.value) {
        C.value = !0;
        try {
          const t = {
            url: v.value.trim(),
            page_index: b.value,
            audio_quality: parseInt(P.value),
            output_format: I.value,
            target_watch_dir_id: c.value ? parseInt(c.value) : null,
            target_subdir: L.value || "B站音频"
          }, z = await ee(t);
          T.success("下载任务已创建"), R.push("/bili/tasks");
        } catch (t) {
          T.error("创建下载失败", ((l = (m = t == null ? void 0 : t.response) == null ? void 0 : m.data) == null ? void 0 : l.detail) || t.message, t);
        } finally {
          C.value = !1;
        }
      }
    }
    async function X() {
      try {
        const m = await Y();
        U.value = m || [], U.value.length > 0 && !c.value && (c.value = String(U.value[0].id));
      } catch {
      }
    }
    return X(), (m, l) => (u(), r("div", te, [
      n("div", ae, [
        l[11] || (l[11] = n("h1", { class: "text-2xl font-bold" }, "B站音频下载", -1)),
        n("div", se, [
          a(e(w), {
            variant: "outline",
            size: "sm",
            onClick: l[0] || (l[0] = (t) => e(R).push("/bili/tasks"))
          }, {
            default: s(() => [
              a(e(Q), { class: "w-4 h-4 mr-1" }),
              l[9] || (l[9] = d(" 下载任务 ", -1))
            ]),
            _: 1
          }),
          a(e(w), {
            variant: "outline",
            size: "sm",
            onClick: l[1] || (l[1] = (t) => e(R).push("/bili/settings"))
          }, {
            default: s(() => [
              a(e(H), { class: "w-4 h-4 mr-1" }),
              l[10] || (l[10] = d(" 设置 ", -1))
            ]),
            _: 1
          })
        ])
      ]),
      n("div", ue, [
        n("div", oe, [
          a(e(f), { class: "text-base font-medium" }, {
            default: s(() => [...l[12] || (l[12] = [
              d("视频链接", -1)
            ])]),
            _: 1
          }),
          n("div", ne, [
            a(e(A), {
              modelValue: e(v),
              "onUpdate:modelValue": l[2] || (l[2] = (t) => _(v) ? v.value = t : null),
              placeholder: "粘贴B站视频链接（BV号或完整URL）",
              onKeyup: le(F, ["enter"]),
              class: "flex-1"
            }, null, 8, ["modelValue"]),
            a(e(w), {
              onClick: F,
              disabled: e(S) || !e(v).trim()
            }, {
              default: s(() => [
                e(S) ? (u(), y(e(E), {
                  key: 0,
                  class: "w-4 h-4 mr-2 animate-spin"
                })) : (u(), y(e(W), {
                  key: 1,
                  class: "w-4 h-4 mr-2"
                })),
                l[13] || (l[13] = d(" 解析 ", -1))
              ]),
              _: 1
            }, 8, ["disabled"])
          ]),
          e(D) ? (u(), r("p", de, i(e(D)), 1)) : g("", !0)
        ]),
        e(o) ? (u(), r("div", re, [
          n("div", ie, [
            e(o).cover_url ? (u(), r("img", {
              key: 0,
              src: e(o).cover_url,
              class: "w-40 h-24 object-cover rounded border bg-muted",
              onError: l[3] || (l[3] = (t) => t.target.style.display = "none")
            }, null, 40, pe)) : g("", !0),
            n("div", me, [
              n("h2", ve, i(e(o).title), 1),
              e(o).upper_name ? (u(), r("p", ce, " UP主: " + i(e(o).upper_name), 1)) : g("", !0),
              e(o).duration ? (u(), r("p", fe, " 时长: " + i(Math.floor(e(o).duration / 60)) + ":" + i(String(e(o).duration % 60).padStart(2, "0")), 1)) : g("", !0),
              e(o).source_url ? (u(), r("a", {
                key: 2,
                href: e(o).source_url,
                target: "_blank",
                class: "text-xs text-blue-500 hover:underline"
              }, i(e(o).source_url), 9, _e)) : g("", !0)
            ])
          ]),
          e(o).pages && e(o).pages.length > 1 ? (u(), r("div", ge, [
            a(e(f), null, {
              default: s(() => [...l[14] || (l[14] = [
                d("选择分P", -1)
              ])]),
              _: 1
            }),
            a(e(x), {
              modelValue: e(b),
              "onUpdate:modelValue": l[4] || (l[4] = (t) => _(b) ? b.value = t : null)
            }, {
              default: s(() => [
                a(e(h), null, {
                  default: s(() => [
                    a(e(B), { placeholder: "选择分P" })
                  ]),
                  _: 1
                }),
                a(e(k), null, {
                  default: s(() => [
                    (u(!0), r(M, null, N(e(o).pages, (t, z) => (u(), y(e(V), {
                      key: z,
                      value: String(z)
                    }, {
                      default: s(() => [
                        d(" P" + i(t.page) + ": " + i(t.part) + " (" + i(Math.floor(t.duration / 60)) + ":" + i(String(t.duration % 60).padStart(2, "0")) + ") ", 1)
                      ]),
                      _: 2
                    }, 1032, ["value"]))), 128))
                  ]),
                  _: 1
                })
              ]),
              _: 1
            }, 8, ["modelValue"])
          ])) : g("", !0),
          n("div", ye, [
            n("div", be, [
              a(e(f), null, {
                default: s(() => [...l[15] || (l[15] = [
                  d("音质", -1)
                ])]),
                _: 1
              }),
              a(e(x), {
                modelValue: e(P),
                "onUpdate:modelValue": l[5] || (l[5] = (t) => _(P) ? P.value = t : null)
              }, {
                default: s(() => [
                  a(e(h), null, {
                    default: s(() => [
                      a(e(B))
                    ]),
                    _: 1
                  }),
                  a(e(k), null, {
                    default: s(() => [
                      (u(), r(M, null, N(q, (t) => a(e(V), {
                        key: t.value,
                        value: t.value
                      }, {
                        default: s(() => [
                          d(i(t.label), 1)
                        ]),
                        _: 2
                      }, 1032, ["value"])), 64))
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }, 8, ["modelValue"])
            ]),
            n("div", we, [
              a(e(f), null, {
                default: s(() => [...l[16] || (l[16] = [
                  d("输出格式", -1)
                ])]),
                _: 1
              }),
              a(e(x), {
                modelValue: e(I),
                "onUpdate:modelValue": l[6] || (l[6] = (t) => _(I) ? I.value = t : null)
              }, {
                default: s(() => [
                  a(e(h), null, {
                    default: s(() => [
                      a(e(B))
                    ]),
                    _: 1
                  }),
                  a(e(k), null, {
                    default: s(() => [
                      (u(), r(M, null, N(G, (t) => a(e(V), {
                        key: t.value,
                        value: t.value
                      }, {
                        default: s(() => [
                          d(i(t.label), 1)
                        ]),
                        _: 2
                      }, 1032, ["value"])), 64))
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }, 8, ["modelValue"])
            ])
          ]),
          n("div", xe, [
            n("div", ke, [
              a(e(f), null, {
                default: s(() => [...l[17] || (l[17] = [
                  d("保存目录", -1)
                ])]),
                _: 1
              }),
              a(e(x), {
                modelValue: e(c),
                "onUpdate:modelValue": l[7] || (l[7] = (t) => _(c) ? c.value = t : null)
              }, {
                default: s(() => [
                  a(e(h), null, {
                    default: s(() => [
                      a(e(B), { placeholder: "选择监控目录" })
                    ]),
                    _: 1
                  }),
                  a(e(k), null, {
                    default: s(() => [
                      (u(!0), r(M, null, N(e(U), (t) => (u(), y(e(V), {
                        key: t.id,
                        value: String(t.id)
                      }, {
                        default: s(() => [
                          d(i(t.path), 1)
                        ]),
                        _: 2
                      }, 1032, ["value"]))), 128))
                    ]),
                    _: 1
                  })
                ]),
                _: 1
              }, 8, ["modelValue"])
            ]),
            n("div", Ve, [
              a(e(f), null, {
                default: s(() => [...l[18] || (l[18] = [
                  d("子目录", -1)
                ])]),
                _: 1
              }),
              a(e(A), {
                modelValue: e(L),
                "onUpdate:modelValue": l[8] || (l[8] = (t) => _(L) ? L.value = t : null),
                placeholder: "B站音频"
              }, null, 8, ["modelValue"])
            ])
          ]),
          a(e(w), {
            onClick: J,
            disabled: e(C),
            class: "w-full",
            size: "lg"
          }, {
            default: s(() => [
              e(C) ? (u(), y(e(E), {
                key: 1,
                class: "w-5 h-5 mr-2 animate-spin"
              })) : (u(), y(e(O), {
                key: 0,
                class: "w-5 h-5 mr-2"
              })),
              l[19] || (l[19] = d(" 下载音频 ", -1))
            ]),
            _: 1
          }, 8, ["disabled"])
        ])) : (u(), r("div", he, [
          a(e($), { class: "w-16 h-16 mx-auto mb-4 opacity-20" }),
          l[20] || (l[20] = n("p", { class: "text-lg" }, "粘贴B站视频链接，提取音频并入库", -1)),
          l[21] || (l[21] = n("p", { class: "text-sm mt-2" }, "支持 BV号、av号、完整链接", -1))
        ]))
      ])
    ]));
  }
};
export {
  Ue as default
};
