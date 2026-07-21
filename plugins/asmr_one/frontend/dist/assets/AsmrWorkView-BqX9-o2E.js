import { m as Ye, o, c as r, a as l, u as e, f as g, b as f, n as ne, e as w, t as c, p as kt, F as S, r as R, q as _t, v as bt, x as Ct, w as y, d as m, i as Me, y as St, z as Pt, A as jt, B as Dt, k as Xe, C as $t, D as Ft, E as Tt, G as Bt, H as Rt, I as zt, J as Nt, K as Ut } from "./api-BVwVWTpM.js";
import { a as Qe, v as Lt } from "./runtime-dom.esm-bundler-KgcpFXTz.js";
import { W as It } from "./WorkCard-B-OrDsz5.js";
import { c as Vt, d as At, e as Mt } from "./history-C9KjQtlt.js";
import { u as qt } from "./store-KZ0YZNeM.js";
const Wt = {
  key: 6,
  class: "text-xs text-muted-foreground tabular-nums"
}, Et = {
  key: 7,
  class: "text-xs text-muted-foreground tabular-nums"
}, Ht = { key: 0 }, Ot = {
  __name: "FileTree",
  props: {
    node: { type: Object, required: !0 },
    level: { type: Number, default: 0 },
    selectedPaths: { type: Set, default: () => /* @__PURE__ */ new Set() },
    pathPrefix: { type: String, default: "" }
  },
  emits: ["toggle", "preview"],
  setup(P, { emit: v }) {
    const { computed: _, ref: _e } = window.__etamusic.vue, {
      Folder: be,
      FolderOpen: Ce,
      FileAudio: z,
      FileText: J,
      FileImage: Se,
      ChevronRight: Pe,
      Check: ae,
      Square: re,
      Eye: ie,
      Play: de
    } = window.__etamusic.icons, k = P, E = v, N = _e(k.node.type === "folder" ? k.level < 1 : !1), C = _(() => k.node.type === "folder"), q = _(() => k.node.type === "audio");
    _(() => k.node.type === "file");
    const X = _(() => {
      const i = k.node.title || "", h = i.lastIndexOf(".");
      return h >= 0 ? i.slice(h + 1).toLowerCase() : "";
    }), Q = _(() => ["jpg", "jpeg", "png", "gif", "webp", "bmp", "svg"].includes(X.value)), je = _(() => ["txt", "md", "lyc", "srt", "vtt", "json", "lrc"].includes(X.value)), Y = _(() => ["mp4", "webm", "mkv", "avi", "mov"].includes(X.value)), $ = _(() => q.value || Q.value || je.value || Y.value), De = _(
      () => C.value && Array.isArray(k.node.children) && k.node.children.length > 0
    ), H = _(() => {
      const i = k.node.title || "";
      return k.pathPrefix ? `${k.pathPrefix}/${i}` : i;
    }), ue = _(() => {
      if (!C.value) return [H.value];
      const i = [], h = (F, x) => {
        const T = F.title || "", b = x ? `${x}/${T}` : T;
        if (F.type === "folder")
          for (const d of F.children || []) h(d, b);
        else
          i.push(b);
      };
      return h(k.node, k.pathPrefix), i;
    }), ce = _(() => {
      if (C.value) {
        const i = ue.value;
        return i.length > 0 && i.every((h) => k.selectedPaths.has(h));
      }
      return k.selectedPaths.has(H.value);
    });
    function fe() {
      C.value && (N.value = !N.value);
    }
    function me(i) {
      i.stopPropagation(), E("preview", {
        node: k.node,
        fullPath: H.value,
        type: q.value ? "audio" : Q.value ? "image" : Y.value ? "video" : je.value ? "text" : "other"
      });
    }
    function $e(i) {
      E("preview", i);
    }
    function ve(i) {
      i.stopPropagation();
      const h = ue.value;
      E("toggle", { paths: h, selected: !ce.value });
    }
    function qe(i) {
      E("toggle", i);
    }
    function Fe(i) {
      return i ? i >= 1024 * 1024 * 1024 ? (i / 1024 / 1024 / 1024).toFixed(2) + " GB" : i >= 1024 * 1024 ? (i / 1024 / 1024).toFixed(1) + " MB" : i >= 1024 ? (i / 1024).toFixed(1) + " KB" : i + " B" : "";
    }
    function Te(i) {
      if (!i) return "";
      const h = Math.floor(i / 60), F = Math.floor(i % 60);
      return `${h}:${String(F).padStart(2, "0")}`;
    }
    return (i, h) => {
      const F = Ye("FileTree", !0);
      return o(), r("div", null, [
        l("div", {
          class: "flex items-center gap-2 py-1.5 px-2 rounded hover:bg-accent/50 cursor-pointer",
          style: kt({ paddingLeft: `${P.level * 16 + 8}px` }),
          onClick: h[0] || (h[0] = (x) => e(C) ? fe() : ve(x))
        }, [
          l("button", {
            class: "flex h-4 w-4 items-center justify-center",
            onClick: Qe(ve, ["stop"])
          }, [
            e(ce) ? (o(), g(e(ae), {
              key: 0,
              class: "h-4 w-4 text-primary"
            })) : (o(), g(e(re), {
              key: 1,
              class: "h-3.5 w-3.5 text-muted-foreground"
            }))
          ]),
          e(C) ? (o(), r("button", {
            key: 0,
            class: "flex h-4 w-4 items-center justify-center",
            onClick: Qe(fe, ["stop"])
          }, [
            f(e(Pe), {
              class: ne(["h-3.5 w-3.5 transition-transform", { "rotate-90": e(N) }])
            }, null, 8, ["class"])
          ])) : w("", !0),
          e(C) && !e(N) ? (o(), g(e(be), {
            key: 1,
            class: "h-4 w-4 text-amber-400"
          })) : e(C) && e(N) ? (o(), g(e(Ce), {
            key: 2,
            class: "h-4 w-4 text-amber-400"
          })) : e(q) ? (o(), g(e(z), {
            key: 3,
            class: "h-4 w-4 text-emerald-400"
          })) : e(Q) ? (o(), g(e(Se), {
            key: 4,
            class: "h-4 w-4 text-sky-400"
          })) : (o(), g(e(J), {
            key: 5,
            class: "h-4 w-4 text-muted-foreground"
          })),
          l("span", {
            class: ne(["flex-1 truncate text-sm", e(C) ? "font-medium text-foreground" : "text-muted-foreground"])
          }, c(P.node.title), 3),
          e(q) && P.node.duration ? (o(), r("span", Wt, c(Te(P.node.duration)), 1)) : w("", !0),
          P.node.size ? (o(), r("span", Et, c(Fe(P.node.size)), 1)) : w("", !0),
          e($) ? (o(), r("button", {
            key: 8,
            class: "flex h-5 w-5 items-center justify-center rounded hover:bg-accent text-muted-foreground hover:text-primary shrink-0",
            title: "预览",
            onClick: me
          }, [
            e(q) || e(Y) ? (o(), g(e(de), {
              key: 0,
              class: "h-3.5 w-3.5"
            })) : (o(), g(e(ie), {
              key: 1,
              class: "h-3.5 w-3.5"
            }))
          ])) : w("", !0)
        ], 4),
        e(C) && e(N) && e(De) ? (o(), r("div", Ht, [
          (o(!0), r(S, null, R(P.node.children, (x, T) => (o(), g(F, {
            key: T,
            node: x,
            level: P.level + 1,
            "selected-paths": P.selectedPaths,
            "path-prefix": e(H),
            onToggle: qe,
            onPreview: $e
          }, null, 8, ["node", "level", "selected-paths", "path-prefix"]))), 128))
        ])) : w("", !0)
      ]);
    };
  }
}, Gt = { class: "flex flex-col gap-4" }, Kt = { class: "flex items-center gap-3 shrink-0" }, Jt = {
  key: 0,
  class: "flex items-center justify-center py-12 text-muted-foreground"
}, Xt = { class: "flex gap-5 rounded-lg border border-border bg-card/40 p-4" }, Qt = ["src", "alt"], Yt = { class: "flex-1 min-w-0 flex flex-col gap-2" }, Zt = { class: "flex items-start gap-2" }, es = { class: "text-xl font-semibold text-foreground flex-1" }, ts = { class: "text-sm text-muted-foreground" }, ss = { key: 1 }, ls = { class: "text-sm text-muted-foreground" }, os = { class: "flex flex-wrap gap-1.5 mt-1" }, ns = {
  key: 0,
  class: "text-xs text-muted-foreground mt-1"
}, as = { key: 0 }, rs = ["onClick"], is = { class: "grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4" }, ds = { class: "flex flex-col rounded-lg border border-border bg-card/40 overflow-hidden" }, us = { class: "flex items-center justify-between px-4 py-2.5 border-b border-border" }, cs = { class: "flex items-center gap-2 text-sm font-medium" }, fs = { class: "flex items-center gap-2 text-xs" }, ms = { class: "overflow-auto p-2 max-h-[480px]" }, vs = {
  key: 0,
  class: "flex items-center justify-center py-8 text-muted-foreground"
}, ps = { class: "flex flex-col rounded-lg border border-border bg-card/40 p-4 gap-3" }, gs = { class: "flex flex-col gap-1.5" }, xs = {
  key: 0,
  class: "text-xs text-amber-400"
}, ys = { class: "flex flex-col gap-1.5" }, hs = {
  key: 0,
  class: "text-xs text-amber-400"
}, ws = { class: "rounded-md bg-secondary/40 p-2.5 text-xs" }, ks = { class: "flex justify-between" }, _s = { class: "text-foreground font-medium" }, bs = { class: "flex justify-between mt-1" }, Cs = { class: "text-foreground font-medium" }, Ss = { class: "rounded-md bg-secondary/40 p-2.5 text-xs space-y-1" }, Ps = { class: "flex justify-between gap-2" }, js = ["title"], Ds = { class: "flex justify-between gap-2" }, $s = ["title"], Fs = { class: "flex justify-between gap-2" }, Ts = ["title"], Bs = { class: "rounded-md border border-border p-2.5 space-y-2" }, Rs = { class: "flex items-center justify-between" }, zs = {
  key: 0,
  class: "grid grid-cols-3 gap-2"
}, Ns = ["onClick"], Us = ["src", "alt"], Ls = { class: "absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[10px] py-0.5 text-center" }, Is = { class: "text-[11px] text-muted-foreground leading-relaxed" }, Vs = { class: "text-foreground" }, As = { class: "rounded-lg border border-border bg-card/40 p-4" }, Ms = { class: "flex items-center gap-2 mb-3" }, qs = {
  key: 0,
  class: "text-xs text-muted-foreground"
}, Ws = { class: "flex items-center gap-1 mb-3" }, Es = ["onClick"], Hs = { class: "ml-2 text-xs text-muted-foreground" }, Os = ["disabled"], Gs = { class: "flex items-center gap-2" }, Ks = {
  key: 1,
  class: "text-sm text-muted-foreground py-2"
}, Js = { class: "rounded-lg border border-border bg-card/40 p-4" }, Xs = { class: "flex items-center gap-2 mb-3" }, Qs = {
  key: 0,
  class: "flex items-center justify-center py-6 text-muted-foreground"
}, Ys = {
  key: 1,
  class: "text-sm text-muted-foreground py-4 text-center"
}, Zs = {
  key: 2,
  class: "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3"
}, el = { class: "truncate" }, tl = {
  key: 0,
  class: "ml-2"
}, sl = {
  key: 1,
  class: "ml-2"
}, ll = { class: "flex-1 overflow-auto min-h-0" }, ol = {
  key: 0,
  class: "flex flex-col items-center gap-4 py-4"
}, nl = { class: "w-32 h-32 rounded-lg bg-gradient-to-br from-emerald-500/20 to-primary/20 flex items-center justify-center" }, al = ["src"], rl = {
  key: 1,
  class: "flex justify-center"
}, il = ["src"], dl = {
  key: 2,
  class: "flex justify-center"
}, ul = ["src", "alt"], cl = { key: 3 }, fl = {
  key: 0,
  class: "flex items-center justify-center py-8 text-muted-foreground"
}, ml = {
  key: 1,
  class: "text-sm text-foreground whitespace-pre-wrap break-all p-3 bg-secondary/30 rounded-md font-mono"
}, vl = {
  key: 4,
  class: "flex items-center justify-center py-8 text-muted-foreground text-sm"
}, wl = {
  __name: "AsmrWorkView",
  setup(P) {
    const { ref: v, computed: _, onMounted: _e } = window.__etamusic.vue, { useRouter: be, useRoute: Ce } = window.__etamusic.vueRouter, {
      Button: z,
      Badge: J,
      Empty: Se,
      useToast: Pe,
      Select: ae,
      SelectTrigger: re,
      SelectValue: ie,
      SelectContent: de,
      SelectItem: k,
      Switch: E,
      Dialog: N,
      DialogContent: C,
      DialogHeader: q,
      DialogTitle: X,
      DialogDescription: Q,
      CoverPickerDialog: je
    } = window.__etamusic.ui, {
      ArrowLeft: Y,
      Loader2: $,
      Download: De,
      CheckSquare: H,
      Square: ue,
      ExternalLink: ce,
      HardDrive: fe,
      Star: me,
      Heart: $e,
      Sparkles: ve,
      X: qe,
      FileText: Fe,
      FileImage: Te,
      Play: i
    } = window.__etamusic.icons, h = be(), F = Ce(), x = Pe(), T = qt(), b = _(() => Number(F.params.id)), d = v(null), U = v({ tree: [], files: [], total: 0, total_size: 0 }), Be = v(!0), Re = v(!0), L = v(/* @__PURE__ */ new Set()), I = v([]), Z = v("local_node"), B = v(null), pe = v(!1), ee = v(!0), ze = v("main");
    v(!1), v(null);
    const u = v(null), Ne = v(!1), O = v(""), Ue = v(!1), j = v(0), G = v(""), V = v(!1), A = v(!1), W = v(null), ge = v(!1), xe = v([]), Le = v(!1), K = _(
      () => U.value.files.filter((s) => L.value.has(s.path))
    ), Ze = _(
      () => K.value.reduce((s, t) => s + (t.size || 0), 0)
    ), Ie = _(() => {
      const s = I.value.find((t) => t.id === Z.value);
      return (s == null ? void 0 : s.watch_dirs) || [];
    });
    function et({ paths: s, selected: t }) {
      const n = new Set(L.value);
      for (const p of s)
        t ? n.add(p) : n.delete(p);
      L.value = n;
    }
    function tt() {
      L.value = new Set(U.value.files.map((s) => s.path));
    }
    function st() {
      L.value = /* @__PURE__ */ new Set();
    }
    async function lt(s) {
      var t, n;
      if (u.value = s, O.value = "", Ue.value = !0, s.type === "text") {
        Ne.value = !0;
        try {
          const p = s.node.stream_url || s.node.mediaStreamUrl || s.node.url || s.node.mediaDownloadUrl;
          if (!p) {
            O.value = "（无法获取文件 URL）";
            return;
          }
          O.value = await Rt(p);
        } catch (p) {
          O.value = `加载失败: ${((n = (t = p == null ? void 0 : p.response) == null ? void 0 : t.data) == null ? void 0 : n.detail) || p.message}`;
        } finally {
          Ne.value = !1;
        }
      }
    }
    function ot() {
      Ue.value = !1, u.value = null, O.value = "";
    }
    async function nt() {
      var s, t;
      Be.value = !0;
      try {
        d.value = await Pt(b.value);
      } catch (n) {
        x.error("加载作品失败", ((t = (s = n == null ? void 0 : n.response) == null ? void 0 : s.data) == null ? void 0 : t.detail) || n.message, n);
      } finally {
        Be.value = !1;
      }
    }
    async function at() {
      var s, t;
      Re.value = !0;
      try {
        const n = await jt(b.value);
        U.value = n, L.value = new Set(n.files.map((p) => p.path));
      } catch (n) {
        x.error("加载文件树失败", ((t = (s = n == null ? void 0 : n.response) == null ? void 0 : s.data) == null ? void 0 : t.detail) || n.message, n);
      } finally {
        Re.value = !1;
      }
    }
    async function rt() {
      try {
        const s = await Dt();
        if (I.value = s.nodes || [], I.value.length > 0) {
          Z.value = I.value[0].id;
          const t = I.value[0].watch_dirs || [];
          t.length > 0 && (B.value = t[0].id);
        }
      } catch (s) {
        console.error("加载目标节点失败:", s);
      }
    }
    function it(s) {
      Z.value = s;
      const t = I.value.find((p) => p.id === s), n = (t == null ? void 0 : t.watch_dirs) || [];
      B.value = n.length > 0 ? n[0].id : null;
    }
    async function dt() {
      var s, t;
      if (K.value.length === 0) {
        x.warning("请至少选择一个文件");
        return;
      }
      if (!B.value) {
        x.warning("请选择目标监控目录");
        return;
      }
      pe.value = !0;
      try {
        const n = d.value || {}, p = (n.vas || []).map((ke) => ke.name).filter(Boolean).join(", ") || "", ye = {
          album: n.title || "",
          artist: p,
          album_artist: n.name || "",
          cover_type: ee.value ? ze.value : null,
          source_url: `https://asmr.one/work/${n.id}`
        }, he = {
          work_id: n.id,
          work_title: n.title,
          source_id: n.source_id,
          target_node_id: Z.value,
          watch_dir_id: B.value,
          selected_paths: Array.from(L.value),
          files: K.value,
          metadata: ye
        }, we = await zt(he);
        x.success(`已创建下载任务 #${we.id}（${K.value.length} 个文件）`), h.push("/asmr/downloads");
      } catch (n) {
        x.error("创建下载任务失败", ((t = (s = n == null ? void 0 : n.response) == null ? void 0 : s.data) == null ? void 0 : t.detail) || n.message);
      } finally {
        pe.value = !1;
      }
    }
    function Ve(s) {
      return s ? s >= 1024 * 1024 * 1024 ? (s / 1024 / 1024 / 1024).toFixed(2) + " GB" : s >= 1024 * 1024 ? (s / 1024 / 1024).toFixed(1) + " MB" : s >= 1024 ? (s / 1024).toFixed(1) + " KB" : s + " B" : "0 B";
    }
    function We(s) {
      if (!s) return "--:--";
      const t = Math.floor(s / 3600), n = Math.floor(s % 3600 / 60), p = Math.floor(s % 60);
      return t > 0 ? `${t}:${String(n).padStart(2, "0")}:${String(p).padStart(2, "0")}` : `${n}:${String(p).padStart(2, "0")}`;
    }
    function ut() {
      var s;
      (s = d.value) != null && s.source_url && window.open(d.value.source_url, "_blank");
    }
    function ct(s) {
      At({ id: s.id, name: s.name }), h.push({
        path: "/asmr",
        query: { tag: s.id, tagName: s.name, page: 1 }
      });
    }
    function ft(s) {
      Mt({ id: s.id, name: s.name }), h.push({
        path: "/asmr",
        query: { va: s.id, vaName: s.name, page: 1 }
      });
    }
    function mt() {
      if (!d.value) return;
      const s = d.value.circle_id, t = d.value.name || "";
      s && (Vt({ id: s, name: t }), h.push({
        path: "/asmr",
        query: { circle: s, circleName: t, page: 1 }
      }));
    }
    _e(() => {
      nt(), at(), rt(), vt(), T.isLoggedIn && pt();
    });
    async function vt() {
      Le.value = !0;
      try {
        const s = await _t(b.value);
        xe.value = s.works || [];
      } catch {
        xe.value = [];
      } finally {
        Le.value = !1;
      }
    }
    async function pt() {
      try {
        const t = (await bt(b.value)).playlists || [];
        if (t.length > 0) {
          const n = t[0];
          W.value = n.id, A.value = !0;
        }
      } catch {
      }
      try {
        const s = await Ct(), n = (s.reviews || s.works || []).find((p) => (p.work_id || p.id) === b.value);
        n && (j.value = n.rating || 0, G.value = n.review_text || n.review || "");
      } catch {
      }
    }
    async function gt() {
      var s, t;
      if (j.value === 0) {
        x.warning("请先选择评分");
        return;
      }
      V.value = !0;
      try {
        await Nt(b.value, j.value, G.value), x.success("评价已提交");
      } catch (n) {
        x.error("提交失败", ((t = (s = n == null ? void 0 : n.response) == null ? void 0 : s.data) == null ? void 0 : t.detail) || n.message);
      } finally {
        V.value = !1;
      }
    }
    async function xt() {
      var s, t;
      V.value = !0;
      try {
        await Ut(b.value), j.value = 0, G.value = "", x.success("已删除评价");
      } catch (n) {
        x.error("删除失败", ((t = (s = n == null ? void 0 : n.response) == null ? void 0 : s.data) == null ? void 0 : t.detail) || n.message);
      } finally {
        V.value = !1;
      }
    }
    async function yt() {
      var s, t;
      if (!T.isLoggedIn) {
        x.warning("请先登录"), h.push("/asmr/account");
        return;
      }
      ge.value = !0;
      try {
        if (A.value && W.value)
          await $t(W.value, [b.value]), A.value = !1, x.success("已取消收藏");
        else {
          if (!W.value)
            try {
              const n = await Ft();
              W.value = n.id;
            } catch {
              const p = await Tt("我的收藏", 0, "默认收藏夹", [b.value]);
              W.value = p.id, A.value = !0, x.success("已收藏（新建收藏夹）");
              return;
            }
          await Bt(W.value, [b.value]), A.value = !0, x.success("已收藏");
        }
      } catch (n) {
        x.error("操作失败", ((t = (s = n == null ? void 0 : n.response) == null ? void 0 : s.data) == null ? void 0 : t.detail) || n.message);
      } finally {
        ge.value = !1;
      }
    }
    function ht(s) {
      j.value = s;
    }
    function wt(s) {
      h.push(`/asmr/work/${s}`);
    }
    return (s, t) => {
      var p, ye, he, we, ke, Ee, He, Oe, Ge;
      const n = Ye("router-link");
      return o(), r("div", Gt, [
        l("div", Kt, [
          f(e(z), {
            variant: "ghost",
            size: "sm",
            onClick: t[0] || (t[0] = (a) => e(h).back())
          }, {
            default: y(() => [
              f(e(Y), { class: "h-4 w-4" }),
              t[6] || (t[6] = m(" 返回 ", -1))
            ]),
            _: 1
          }),
          t[8] || (t[8] = l("div", { class: "flex-1" }, null, -1)),
          (p = e(d)) != null && p.source_url ? (o(), g(e(z), {
            key: 0,
            variant: "ghost",
            size: "sm",
            onClick: ut
          }, {
            default: y(() => [
              f(e(ce), { class: "h-4 w-4" }),
              t[7] || (t[7] = m(" 原站 ", -1))
            ]),
            _: 1
          })) : w("", !0)
        ]),
        e(Be) ? (o(), r("div", Jt, [
          f(e($), { class: "mr-2 h-5 w-5 animate-spin" }),
          t[9] || (t[9] = m(" 加载作品信息... ", -1))
        ])) : e(d) ? (o(), r(S, { key: 1 }, [
          l("div", Xt, [
            l("img", {
              src: e(Xe)(e(d).id),
              alt: e(d).title,
              class: "h-40 w-40 rounded-md object-cover border border-border shrink-0"
            }, null, 8, Qt),
            l("div", Yt, [
              l("div", Zt, [
                l("h2", es, c(e(d).title), 1),
                f(e(z), {
                  variant: "ghost",
                  size: "sm",
                  disabled: e(ge),
                  class: ne(e(A) ? "text-rose-500" : "text-muted-foreground"),
                  onClick: yt
                }, {
                  default: y(() => [
                    e(ge) ? (o(), g(e($), {
                      key: 0,
                      class: "h-4 w-4 animate-spin"
                    })) : (o(), g(e($e), {
                      key: 1,
                      class: "h-4 w-4",
                      fill: e(A) ? "currentColor" : "none"
                    }, null, 8, ["fill"])),
                    m(" " + c(e(A) ? "已收藏" : "收藏"), 1)
                  ]),
                  _: 1
                }, 8, ["disabled", "class"]),
                e(d).nsfw ? (o(), g(e(J), {
                  key: 0,
                  variant: "destructive"
                }, {
                  default: y(() => [...t[10] || (t[10] = [
                    m("R18", -1)
                  ])]),
                  _: 1
                })) : w("", !0)
              ]),
              l("div", ts, [
                t[11] || (t[11] = m(" 社团： ", -1)),
                e(d).circle_id ? (o(), r("button", {
                  key: 0,
                  class: "text-primary hover:underline",
                  onClick: mt
                }, c(e(d).name || "—"), 1)) : (o(), r("span", ss, c(e(d).name || "—"), 1)),
                t[12] || (t[12] = l("span", { class: "mx-2" }, "·", -1)),
                m(" 发布：" + c(e(d).release || "—") + " ", 1),
                t[13] || (t[13] = l("span", { class: "mx-2" }, "·", -1)),
                m(" 时长：" + c(We(e(d).duration)), 1)
              ]),
              l("div", ls, [
                m(" 评分：★ " + c(e(d).rate_average_2dp || "—") + "（" + c(e(d).rate_count) + " 人） ", 1),
                t[14] || (t[14] = l("span", { class: "mx-2" }, "·", -1)),
                m(" 下载：" + c(e(d).dl_count) + " 次 ", 1),
                t[15] || (t[15] = l("span", { class: "mx-2" }, "·", -1)),
                m(" 价格：¥" + c(e(d).price), 1)
              ]),
              l("div", os, [
                (o(!0), r(S, null, R((e(d).tags || []).slice(0, 12), (a) => (o(), g(e(J), {
                  key: a.id,
                  variant: "outline",
                  class: "cursor-pointer font-normal text-xs hover:border-primary/60 hover:text-primary",
                  onClick: (D) => ct(a)
                }, {
                  default: y(() => [
                    m(c(a.name), 1)
                  ]),
                  _: 2
                }, 1032, ["onClick"]))), 128))
              ]),
              (ye = e(d).vas) != null && ye.length ? (o(), r("div", ns, [
                t[16] || (t[16] = m(" 声优： ", -1)),
                (o(!0), r(S, null, R(e(d).vas, (a, D) => (o(), r(S, {
                  key: a.id
                }, [
                  D > 0 ? (o(), r("span", as, "、")) : w("", !0),
                  l("button", {
                    class: "text-primary hover:underline",
                    onClick: (Ae) => ft(a)
                  }, c(a.name), 9, rs)
                ], 64))), 128))
              ])) : w("", !0)
            ])
          ]),
          l("div", is, [
            l("div", ds, [
              l("div", us, [
                l("div", cs, [
                  t[17] || (t[17] = l("span", null, "文件列表", -1)),
                  f(e(J), {
                    variant: "outline",
                    class: "text-xs"
                  }, {
                    default: y(() => [
                      m(c(e(U).total) + " 个文件 / " + c(Ve(e(U).total_size)), 1)
                    ]),
                    _: 1
                  })
                ]),
                l("div", fs, [
                  l("button", {
                    class: "text-primary hover:underline",
                    onClick: tt
                  }, [
                    f(e(H), { class: "inline h-3.5 w-3.5" }),
                    t[18] || (t[18] = m(" 全选 ", -1))
                  ]),
                  l("button", {
                    class: "text-muted-foreground hover:underline",
                    onClick: st
                  }, [
                    f(e(ue), { class: "inline h-3.5 w-3.5" }),
                    t[19] || (t[19] = m(" 清空 ", -1))
                  ])
                ])
              ]),
              l("div", ms, [
                e(Re) ? (o(), r("div", vs, [
                  f(e($), { class: "mr-2 h-4 w-4 animate-spin" }),
                  t[20] || (t[20] = m(" 加载文件树... ", -1))
                ])) : e(U).tree.length === 0 ? (o(), g(e(Se), {
                  key: 1,
                  icon: e(fe),
                  title: "无可下载文件",
                  class: "py-8"
                }, null, 8, ["icon"])) : w("", !0),
                (o(!0), r(S, null, R(e(U).tree, (a, D) => (o(), g(Ot, {
                  key: D,
                  node: a,
                  level: 0,
                  "selected-paths": e(L),
                  "path-prefix": "",
                  onToggle: et,
                  onPreview: lt
                }, null, 8, ["node", "selected-paths"]))), 128))
              ])
            ]),
            l("div", ps, [
              t[36] || (t[36] = l("div", { class: "text-sm font-medium" }, "下载到节点", -1)),
              l("div", gs, [
                t[21] || (t[21] = l("label", { class: "text-xs text-muted-foreground" }, "目标节点", -1)),
                f(e(ae), {
                  "model-value": e(Z),
                  "onUpdate:modelValue": it
                }, {
                  default: y(() => [
                    f(e(re), { class: "h-9" }, {
                      default: y(() => [
                        f(e(ie), { placeholder: "选择节点" })
                      ]),
                      _: 1
                    }),
                    f(e(de), null, {
                      default: y(() => [
                        (o(!0), r(S, null, R(e(I), (a) => (o(), g(e(k), {
                          key: a.id,
                          value: a.id
                        }, {
                          default: y(() => [
                            m(c(a.name), 1)
                          ]),
                          _: 2
                        }, 1032, ["value"]))), 128))
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }, 8, ["model-value"]),
                e(I).length === 0 ? (o(), r("p", xs, " 没有可用的目标节点（请启用 local_node 插件） ")) : w("", !0)
              ]),
              l("div", ys, [
                t[22] || (t[22] = l("label", { class: "text-xs text-muted-foreground" }, "监控目录", -1)),
                f(e(ae), {
                  modelValue: e(B),
                  "onUpdate:modelValue": t[1] || (t[1] = (a) => Me(B) ? B.value = a : null)
                }, {
                  default: y(() => [
                    f(e(re), { class: "h-9" }, {
                      default: y(() => [
                        f(e(ie), { placeholder: "选择目录" })
                      ]),
                      _: 1
                    }),
                    f(e(de), null, {
                      default: y(() => [
                        (o(!0), r(S, null, R(e(Ie), (a) => (o(), g(e(k), {
                          key: a.id,
                          value: a.id
                        }, {
                          default: y(() => [
                            m(c(a.path), 1)
                          ]),
                          _: 2
                        }, 1032, ["value"]))), 128))
                      ]),
                      _: 1
                    })
                  ]),
                  _: 1
                }, 8, ["modelValue"]),
                e(Ie).length === 0 ? (o(), r("p", hs, " 该节点未配置监控目录，请先到「扫描管理」添加 ")) : w("", !0)
              ]),
              l("div", ws, [
                l("div", ks, [
                  t[23] || (t[23] = l("span", { class: "text-muted-foreground" }, "已选文件", -1)),
                  l("span", _s, c(e(K).length) + " / " + c(e(U).total), 1)
                ]),
                l("div", bs, [
                  t[24] || (t[24] = l("span", { class: "text-muted-foreground" }, "总大小", -1)),
                  l("span", Cs, c(Ve(e(Ze))), 1)
                ])
              ]),
              l("div", Ss, [
                t[28] || (t[28] = l("div", { class: "text-muted-foreground mb-1" }, "下载后将自动写入以下标签：", -1)),
                l("div", Ps, [
                  t[25] || (t[25] = l("span", { class: "text-muted-foreground shrink-0" }, "专辑", -1)),
                  l("span", {
                    class: "text-foreground truncate",
                    title: (he = e(d)) == null ? void 0 : he.title
                  }, c(((we = e(d)) == null ? void 0 : we.title) || "—"), 9, js)
                ]),
                l("div", Ds, [
                  t[26] || (t[26] = l("span", { class: "text-muted-foreground shrink-0" }, "艺术家", -1)),
                  l("span", {
                    class: "text-foreground truncate",
                    title: (((ke = e(d)) == null ? void 0 : ke.vas) || []).map((a) => a.name).join(", ")
                  }, c((((Ee = e(d)) == null ? void 0 : Ee.vas) || []).map((a) => a.name).join(", ") || "—"), 9, $s)
                ]),
                l("div", Fs, [
                  t[27] || (t[27] = l("span", { class: "text-muted-foreground shrink-0" }, "专辑艺术家", -1)),
                  l("span", {
                    class: "text-foreground truncate",
                    title: (He = e(d)) == null ? void 0 : He.name
                  }, c(((Oe = e(d)) == null ? void 0 : Oe.name) || "—"), 9, Ts)
                ])
              ]),
              l("div", Bs, [
                l("div", Rs, [
                  t[29] || (t[29] = l("label", { class: "text-xs text-muted-foreground" }, "嵌入封面到音频文件", -1)),
                  f(e(E), {
                    checked: e(ee),
                    "onUpdate:checked": t[2] || (t[2] = (a) => Me(ee) ? ee.value = a : null)
                  }, null, 8, ["checked"])
                ]),
                e(ee) ? (o(), r("div", zs, [
                  (o(), r(S, null, R([{ v: "main", l: "主封面" }, { v: "sam", l: "小图" }, { v: "240x240", l: "240" }], (a) => l("button", {
                    key: a.v,
                    type: "button",
                    class: ne(["relative rounded border-2 overflow-hidden aspect-square", e(ze) === a.v ? "border-primary" : "border-transparent hover:border-border"]),
                    onClick: (D) => ze.value = a.v
                  }, [
                    e(d) ? (o(), r("img", {
                      key: 0,
                      src: e(Xe)(e(d).id, a.v),
                      alt: a.l,
                      class: "h-full w-full object-cover",
                      loading: "lazy"
                    }, null, 8, Us)) : w("", !0),
                    l("span", Ls, c(a.l), 1)
                  ], 10, Ns)), 64))
                ])) : w("", !0)
              ]),
              f(e(z), {
                variant: "gold",
                disabled: e(pe) || e(K).length === 0 || !e(B),
                onClick: dt
              }, {
                default: y(() => [
                  e(pe) ? (o(), g(e($), {
                    key: 0,
                    class: "h-4 w-4 animate-spin"
                  })) : (o(), g(e(De), {
                    key: 1,
                    class: "h-4 w-4"
                  })),
                  t[30] || (t[30] = m(" 创建下载任务 ", -1))
                ]),
                _: 1
              }, 8, ["disabled"]),
              l("p", Is, [
                t[31] || (t[31] = m(" 文件将下载到：", -1)),
                t[32] || (t[32] = l("br", null, null, -1)),
                l("code", Vs, c(((Ge = e(Ie).find((a) => a.id === e(B))) == null ? void 0 : Ge.path) || "...") + "/{ASMR 子目录}/" + c(e(d).title || "作品名") + "/...", 1),
                t[33] || (t[33] = l("br", null, null, -1)),
                t[34] || (t[34] = l("br", null, null, -1)),
                t[35] || (t[35] = m(" 下载完成后会自动写入标签并触发扫描入库。 ", -1))
              ])
            ])
          ]),
          l("div", As, [
            l("div", Ms, [
              f(e(me), { class: "h-4 w-4 text-amber-400" }),
              t[40] || (t[40] = l("span", { class: "text-sm font-medium" }, "我的评价", -1)),
              e(T).isLoggedIn ? w("", !0) : (o(), r("span", qs, [
                t[38] || (t[38] = m(" （请先 ", -1)),
                f(n, {
                  to: "/asmr/account",
                  class: "text-primary hover:underline"
                }, {
                  default: y(() => [...t[37] || (t[37] = [
                    m("登录", -1)
                  ])]),
                  _: 1
                }),
                t[39] || (t[39] = m(" 后评价） ", -1))
              ]))
            ]),
            e(T).isLoggedIn ? (o(), r(S, { key: 0 }, [
              l("div", Ws, [
                t[41] || (t[41] = l("span", { class: "text-xs text-muted-foreground mr-2" }, "评分：", -1)),
                (o(), r(S, null, R(10, (a) => l("button", {
                  key: a,
                  type: "button",
                  class: ne(["p-0.5", a <= e(j) ? "text-amber-400" : "text-muted-foreground/40 hover:text-muted-foreground"]),
                  onClick: (D) => ht(a)
                }, [
                  f(e(me), {
                    class: "h-4 w-4",
                    fill: a <= e(j) ? "currentColor" : "none"
                  }, null, 8, ["fill"])
                ], 10, Es)), 64)),
                l("span", Hs, c(e(j)) + "/10", 1)
              ]),
              St(l("textarea", {
                "onUpdate:modelValue": t[3] || (t[3] = (a) => Me(G) ? G.value = a : null),
                placeholder: "写下你的评价（可选）...",
                class: "mb-3 min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
                disabled: e(V)
              }, null, 8, Os), [
                [Lt, e(G)]
              ]),
              l("div", Gs, [
                f(e(z), {
                  size: "sm",
                  disabled: e(V) || e(j) === 0,
                  onClick: gt
                }, {
                  default: y(() => [
                    e(V) ? (o(), g(e($), {
                      key: 0,
                      class: "h-3.5 w-3.5 animate-spin"
                    })) : w("", !0),
                    m(" " + c(e(j) > 0 ? "更新评价" : "提交评价"), 1)
                  ]),
                  _: 1
                }, 8, ["disabled"]),
                e(j) > 0 ? (o(), g(e(z), {
                  key: 0,
                  size: "sm",
                  variant: "outline",
                  disabled: e(V),
                  onClick: xt
                }, {
                  default: y(() => [...t[42] || (t[42] = [
                    m(" 删除评价 ", -1)
                  ])]),
                  _: 1
                }, 8, ["disabled"])) : w("", !0)
              ])
            ], 64)) : (o(), r("div", Ks, " 登录后可以为本作品打分并撰写评价。 "))
          ]),
          l("div", Js, [
            l("div", Xs, [
              f(e(ve), { class: "h-4 w-4 text-primary" }),
              t[43] || (t[43] = l("span", { class: "text-sm font-medium" }, "相似推荐", -1))
            ]),
            e(Le) ? (o(), r("div", Qs, [
              f(e($), { class: "mr-2 h-4 w-4 animate-spin" }),
              t[44] || (t[44] = m(" 加载中... ", -1))
            ])) : e(xe).length === 0 ? (o(), r("div", Ys, " 暂无相似推荐 ")) : (o(), r("div", Zs, [
              (o(!0), r(S, null, R(e(xe), (a) => (o(), g(It, {
                key: a.id,
                work: a,
                onClick: (D) => wt(a.id)
              }, null, 8, ["work", "onClick"]))), 128))
            ]))
          ])
        ], 64)) : w("", !0),
        f(e(N), {
          open: e(Ue),
          "onUpdate:open": t[5] || (t[5] = (a) => {
            a || ot();
          })
        }, {
          default: y(() => [
            f(e(C), { class: "sm:max-w-2xl max-h-[85vh] flex flex-col" }, {
              default: y(() => {
                var a, D, Ae, Ke;
                return [
                  f(e(q), { class: "shrink-0" }, {
                    default: y(() => [
                      f(e(X), { class: "flex items-center gap-2 pr-6" }, {
                        default: y(() => {
                          var M, te, se, le, oe, Je;
                          return [
                            ((M = e(u)) == null ? void 0 : M.type) === "audio" || ((te = e(u)) == null ? void 0 : te.type) === "video" ? (o(), g(e(i), {
                              key: 0,
                              class: "h-4 w-4 shrink-0 text-emerald-400"
                            })) : ((se = e(u)) == null ? void 0 : se.type) === "image" ? (o(), g(e(Te), {
                              key: 1,
                              class: "h-4 w-4 shrink-0 text-sky-400"
                            })) : ((le = e(u)) == null ? void 0 : le.type) === "text" ? (o(), g(e(Fe), {
                              key: 2,
                              class: "h-4 w-4 shrink-0 text-muted-foreground"
                            })) : w("", !0),
                            l("span", el, c(((Je = (oe = e(u)) == null ? void 0 : oe.node) == null ? void 0 : Je.title) || "预览"), 1)
                          ];
                        }),
                        _: 1
                      }),
                      f(e(Q), { class: "truncate" }, {
                        default: y(() => {
                          var M, te, se, le, oe;
                          return [
                            m(c((M = e(u)) == null ? void 0 : M.fullPath) + " ", 1),
                            (se = (te = e(u)) == null ? void 0 : te.node) != null && se.size ? (o(), r("span", tl, "· " + c(Ve(e(u).node.size)), 1)) : w("", !0),
                            (oe = (le = e(u)) == null ? void 0 : le.node) != null && oe.duration ? (o(), r("span", sl, "· " + c(We(e(u).node.duration)), 1)) : w("", !0)
                          ];
                        }),
                        _: 1
                      })
                    ]),
                    _: 1
                  }),
                  l("div", ll, [
                    ((a = e(u)) == null ? void 0 : a.type) === "audio" ? (o(), r("div", ol, [
                      l("div", nl, [
                        f(e(i), {
                          class: "h-12 w-12 text-emerald-400",
                          fill: "currentColor"
                        })
                      ]),
                      (o(), r("audio", {
                        key: e(u).node.stream_url || e(u).node.mediaStreamUrl || e(u).node.url || e(u).node.mediaDownloadUrl,
                        src: e(u).node.stream_url || e(u).node.mediaStreamUrl || e(u).node.url || e(u).node.mediaDownloadUrl,
                        controls: "",
                        autoplay: "",
                        class: "w-full"
                      }, " 您的浏览器不支持音频播放 ", 8, al)),
                      t[45] || (t[45] = l("p", { class: "text-xs text-muted-foreground" }, " 如果无法播放，可能是文件需要登录才能访问 ", -1))
                    ])) : ((D = e(u)) == null ? void 0 : D.type) === "video" ? (o(), r("div", rl, [
                      (o(), r("video", {
                        key: e(u).node.stream_url || e(u).node.mediaStreamUrl || e(u).node.url || e(u).node.mediaDownloadUrl,
                        src: e(u).node.stream_url || e(u).node.mediaStreamUrl || e(u).node.url || e(u).node.mediaDownloadUrl,
                        controls: "",
                        autoplay: "",
                        class: "max-w-full max-h-[60vh] rounded"
                      }, " 您的浏览器不支持视频播放 ", 8, il))
                    ])) : ((Ae = e(u)) == null ? void 0 : Ae.type) === "image" ? (o(), r("div", dl, [
                      l("img", {
                        src: e(u).node.url || e(u).node.mediaDownloadUrl,
                        alt: e(u).node.title,
                        class: "max-w-full max-h-[60vh] rounded-lg border border-border object-contain",
                        onError: t[4] || (t[4] = (M) => {
                          M.target.style.display = "none", M.target.nextElementSibling.style.display = "block";
                        })
                      }, null, 40, ul),
                      t[46] || (t[46] = l("p", { class: "hidden text-sm text-muted-foreground py-8 text-center" }, " 图片加载失败（可能需要登录或文件不存在） ", -1))
                    ])) : ((Ke = e(u)) == null ? void 0 : Ke.type) === "text" ? (o(), r("div", cl, [
                      e(Ne) ? (o(), r("div", fl, [
                        f(e($), { class: "mr-2 h-4 w-4 animate-spin" }),
                        t[47] || (t[47] = m(" 加载文本内容... ", -1))
                      ])) : (o(), r("pre", ml, c(e(O) || "（空文件）"), 1))
                    ])) : (o(), r("div", vl, " 此文件类型不支持预览 "))
                  ])
                ];
              }),
              _: 1
            })
          ]),
          _: 1
        }, 8, ["open"])
      ]);
    };
  }
};
export {
  wl as default
};
