/**
* @vue/shared v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
// @__NO_SIDE_EFFECTS__
function Ve(t) {
  const e = /* @__PURE__ */ Object.create(null);
  for (const n of t.split(",")) e[n] = 1;
  return (n) => n in e;
}
const St = process.env.NODE_ENV !== "production" ? Object.freeze({}) : {}, ve = process.env.NODE_ENV !== "production" ? Object.freeze([]) : [], Ut = () => {
}, xe = (t) => t.charCodeAt(0) === 111 && t.charCodeAt(1) === 110 && // uppercase letter
(t.charCodeAt(2) > 122 || t.charCodeAt(2) < 97), Te = (t) => t.startsWith("onUpdate:"), K = Object.assign, Ce = Object.prototype.hasOwnProperty, Ot = (t, e) => Ce.call(t, e), h = Array.isArray, L = (t) => ut(t) === "[object Map]", Ie = (t) => ut(t) === "[object Set]", M = (t) => typeof t == "function", S = (t) => typeof t == "string", H = (t) => typeof t == "symbol", _ = (t) => t !== null && typeof t == "object", Bt = Object.prototype.toString, ut = (t) => Bt.call(t), Yt = (t) => ut(t).slice(8, -1), $e = (t) => ut(t) === "[object Object]", $t = (t) => S(t) && t !== "NaN" && t[0] !== "-" && "" + parseInt(t, 10) === t, Jt = (t) => {
  const e = /* @__PURE__ */ Object.create(null);
  return (n) => e[n] || (e[n] = t(n));
}, De = /\B([A-Z])/g, kn = Jt(
  (t) => t.replace(De, "-$1").toLowerCase()
), Ae = Jt((t) => t.charAt(0).toUpperCase() + t.slice(1)), z = (t, e) => !Object.is(t, e);
let Kt;
const ft = () => Kt || (Kt = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {});
function Dt(t) {
  if (h(t)) {
    const e = {};
    for (let n = 0; n < t.length; n++) {
      const s = t[n], r = S(s) ? je(s) : Dt(s);
      if (r)
        for (const o in r)
          e[o] = r[o];
    }
    return e;
  } else if (S(t) || _(t))
    return t;
}
const Me = /;(?![^(]*\))/g, Pe = /:([^]+)/, Fe = /\/\*[^]*?\*\//g;
function je(t) {
  const e = {};
  return t.replace(Fe, "").split(Me).forEach((n) => {
    if (n) {
      const s = n.split(Pe);
      s.length > 1 && (e[s[0].trim()] = s[1].trim());
    }
  }), e;
}
function At(t) {
  let e = "";
  if (S(t))
    e = t;
  else if (h(t))
    for (let n = 0; n < t.length; n++) {
      const s = At(t[n]);
      s && (e += s + " ");
    }
  else if (_(t))
    for (const n in t)
      t[n] && (e += n + " ");
  return e.trim();
}
const qt = (t) => !!(t && t.__v_isRef === !0), Ke = (t) => S(t) ? t : t == null ? "" : h(t) || _(t) && (t.toString === Bt || !M(t.toString)) ? qt(t) ? Ke(t.value) : JSON.stringify(t, Gt, 2) : String(t), Gt = (t, e) => qt(e) ? Gt(t, e.value) : L(e) ? {
  [`Map(${e.size})`]: [...e.entries()].reduce(
    (n, [s, r], o) => (n[gt(s, o) + " =>"] = r, n),
    {}
  )
} : Ie(e) ? {
  [`Set(${e.size})`]: [...e.values()].map((n) => gt(n))
} : H(e) ? gt(e) : _(e) && !h(e) && !$e(e) ? String(e) : e, gt = (t, e = "") => {
  var n;
  return (
    // Symbol.description in es2019+ so we need to cast here to pass
    // the lib: es2016 check
    H(t) ? `Symbol(${(n = t.description) != null ? n : e})` : t
  );
};
/**
* @vue/reactivity v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
function Y(t, ...e) {
  console.warn(`[Vue warn] ${t}`, ...e);
}
let He, Zt = 0, mt;
function Mt() {
  Zt++;
}
function Pt() {
  if (--Zt > 0)
    return;
  let t;
  for (; mt; ) {
    let e = mt;
    for (mt = void 0; e; ) {
      const n = e.next;
      if (e.next = void 0, e.flags &= -9, e.flags & 1)
        try {
          e.trigger();
        } catch (s) {
          t || (t = s);
        }
      e = n;
    }
  }
  if (t) throw t;
}
let ot = !0;
const Qt = [];
function dt() {
  Qt.push(ot), ot = !1;
}
function pt() {
  const t = Qt.pop();
  ot = t === void 0 ? !0 : t;
}
class ke {
  // TODO isolatedDeclarations "__v_skip"
  constructor(e) {
    this.computed = e, this.version = 0, this.activeLink = void 0, this.subs = void 0, this.map = void 0, this.key = void 0, this.sc = 0, this.__v_skip = !0, process.env.NODE_ENV !== "production" && (this.subsHead = void 0);
  }
  track(e) {
  }
  trigger(e) {
    this.version++, this.notify(e);
  }
  notify(e) {
    Mt();
    try {
      if (process.env.NODE_ENV !== "production")
        for (let n = this.subsHead; n; n = n.nextSub)
          n.sub.onTrigger && !(n.sub.flags & 8) && n.sub.onTrigger(
            K(
              {
                effect: n.sub
              },
              e
            )
          );
      for (let n = this.subs; n; n = n.prevSub)
        n.sub.notify() && n.sub.dep.notify();
    } finally {
      Pt();
    }
  }
}
const Rt = /* @__PURE__ */ new WeakMap(), P = /* @__PURE__ */ Symbol(
  process.env.NODE_ENV !== "production" ? "Object iterate" : ""
), Vt = /* @__PURE__ */ Symbol(
  process.env.NODE_ENV !== "production" ? "Map keys iterate" : ""
), Q = /* @__PURE__ */ Symbol(
  process.env.NODE_ENV !== "production" ? "Array iterate" : ""
);
function g(t, e, n) {
  if (ot && He) {
    let s = Rt.get(t);
    s || Rt.set(t, s = /* @__PURE__ */ new Map());
    let r = s.get(n);
    r || (s.set(n, r = new ke()), r.map = s, r.key = n), process.env.NODE_ENV !== "production" ? r.track({
      target: t,
      type: e,
      key: n
    }) : r.track();
  }
}
function D(t, e, n, s, r, o) {
  const c = Rt.get(t);
  if (!c)
    return;
  const i = (a) => {
    a && (process.env.NODE_ENV !== "production" ? a.trigger({
      target: t,
      type: e,
      key: n,
      newValue: s,
      oldValue: r,
      oldTarget: o
    }) : a.trigger());
  };
  if (Mt(), e === "clear")
    c.forEach(i);
  else {
    const a = h(t), u = a && $t(n);
    if (a && n === "length") {
      const f = Number(s);
      c.forEach((l, d) => {
        (d === "length" || d === Q || !H(d) && d >= f) && i(l);
      });
    } else
      switch ((n !== void 0 || c.has(void 0)) && i(c.get(n)), u && i(c.get(Q)), e) {
        case "add":
          a ? u && i(c.get("length")) : (i(c.get(P)), L(t) && i(c.get(Vt)));
          break;
        case "delete":
          a || (i(c.get(P)), L(t) && i(c.get(Vt)));
          break;
        case "set":
          L(t) && i(c.get(P));
          break;
      }
  }
  Pt();
}
function k(t) {
  const e = /* @__PURE__ */ p(t);
  return e === t ? e : (g(e, "iterate", Q), /* @__PURE__ */ N(t) ? e : e.map(I));
}
function ht(t) {
  return g(t = /* @__PURE__ */ p(t), "iterate", Q), t;
}
function R(t, e) {
  return /* @__PURE__ */ V(t) ? J(/* @__PURE__ */ _t(t) ? I(e) : e) : I(e);
}
const ze = {
  __proto__: null,
  [Symbol.iterator]() {
    return bt(this, Symbol.iterator, (t) => R(this, t));
  },
  concat(...t) {
    return k(this).concat(
      ...t.map((e) => h(e) ? k(e) : e)
    );
  },
  entries() {
    return bt(this, "entries", (t) => (t[1] = R(this, t[1]), t));
  },
  every(t, e) {
    return v(this, "every", t, e, void 0, arguments);
  },
  filter(t, e) {
    return v(
      this,
      "filter",
      t,
      e,
      (n) => n.map((s) => R(this, s)),
      arguments
    );
  },
  find(t, e) {
    return v(
      this,
      "find",
      t,
      e,
      (n) => R(this, n),
      arguments
    );
  },
  findIndex(t, e) {
    return v(this, "findIndex", t, e, void 0, arguments);
  },
  findLast(t, e) {
    return v(
      this,
      "findLast",
      t,
      e,
      (n) => R(this, n),
      arguments
    );
  },
  findLastIndex(t, e) {
    return v(this, "findLastIndex", t, e, void 0, arguments);
  },
  // flat, flatMap could benefit from ARRAY_ITERATE but are not straight-forward to implement
  forEach(t, e) {
    return v(this, "forEach", t, e, void 0, arguments);
  },
  includes(...t) {
    return wt(this, "includes", t);
  },
  indexOf(...t) {
    return wt(this, "indexOf", t);
  },
  join(t) {
    return k(this).join(t);
  },
  // keys() iterator only reads `length`, no optimization required
  lastIndexOf(...t) {
    return wt(this, "lastIndexOf", t);
  },
  map(t, e) {
    return v(this, "map", t, e, void 0, arguments);
  },
  pop() {
    return G(this, "pop");
  },
  push(...t) {
    return G(this, "push", t);
  },
  reduce(t, ...e) {
    return Ht(this, "reduce", t, e);
  },
  reduceRight(t, ...e) {
    return Ht(this, "reduceRight", t, e);
  },
  shift() {
    return G(this, "shift");
  },
  // slice could use ARRAY_ITERATE but also seems to beg for range tracking
  some(t, e) {
    return v(this, "some", t, e, void 0, arguments);
  },
  splice(...t) {
    return G(this, "splice", t);
  },
  toReversed() {
    return k(this).toReversed();
  },
  toSorted(t) {
    return k(this).toSorted(t);
  },
  toSpliced(...t) {
    return k(this).toSpliced(...t);
  },
  unshift(...t) {
    return G(this, "unshift", t);
  },
  values() {
    return bt(this, "values", (t) => R(this, t));
  }
};
function bt(t, e, n) {
  const s = ht(t), r = s[e]();
  return s !== t && !/* @__PURE__ */ N(t) && (r._next = r.next, r.next = () => {
    const o = r._next();
    return o.done || (o.value = n(o.value)), o;
  }), r;
}
const We = Array.prototype;
function v(t, e, n, s, r, o) {
  const c = ht(t), i = c !== t && !/* @__PURE__ */ N(t), a = c[e];
  if (a !== We[e]) {
    const l = a.apply(t, o);
    return i ? I(l) : l;
  }
  let u = n;
  c !== t && (i ? u = function(l, d) {
    return n.call(this, R(t, l), d, t);
  } : n.length > 2 && (u = function(l, d) {
    return n.call(this, l, d, t);
  }));
  const f = a.call(c, u, s);
  return i && r ? r(f) : f;
}
function Ht(t, e, n, s) {
  const r = ht(t), o = r !== t && !/* @__PURE__ */ N(t);
  let c = n, i = !1;
  r !== t && (o ? (i = s.length === 0, c = function(u, f, l) {
    return i && (i = !1, u = R(t, u)), n.call(this, u, R(t, f), l, t);
  }) : n.length > 3 && (c = function(u, f, l) {
    return n.call(this, u, f, l, t);
  }));
  const a = r[e](c, ...s);
  return i ? R(t, a) : a;
}
function wt(t, e, n) {
  const s = /* @__PURE__ */ p(t);
  g(s, "iterate", Q);
  const r = s[e](...n);
  return (r === -1 || r === !1) && /* @__PURE__ */ st(n[0]) ? (n[0] = /* @__PURE__ */ p(n[0]), s[e](...n)) : r;
}
function G(t, e, n = []) {
  dt(), Mt();
  const s = (/* @__PURE__ */ p(t))[e].apply(t, n);
  return Pt(), pt(), s;
}
const Le = /* @__PURE__ */ Ve("__proto__,__v_isRef,__isVue"), Xt = new Set(
  /* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((t) => t !== "arguments" && t !== "caller").map((t) => Symbol[t]).filter(H)
);
function Ue(t) {
  H(t) || (t = String(t));
  const e = /* @__PURE__ */ p(this);
  return g(e, "has", t), e.hasOwnProperty(t);
}
class te {
  constructor(e = !1, n = !1) {
    this._isReadonly = e, this._isShallow = n;
  }
  get(e, n, s) {
    if (n === "__v_skip") return e.__v_skip;
    const r = this._isReadonly, o = this._isShallow;
    if (n === "__v_isReactive")
      return !r;
    if (n === "__v_isReadonly")
      return r;
    if (n === "__v_isShallow")
      return o;
    if (n === "__v_raw")
      return s === (r ? o ? en : re : o ? tn : ne).get(e) || // receiver is not the reactive proxy, but has the same prototype
      // this means the receiver is a user proxy of the reactive proxy
      Object.getPrototypeOf(e) === Object.getPrototypeOf(s) ? e : void 0;
    const c = h(e);
    if (!r) {
      let a;
      if (c && (a = ze[n]))
        return a;
      if (n === "hasOwnProperty")
        return Ue;
    }
    const i = Reflect.get(
      e,
      n,
      // if this is a proxy wrapping a ref, return methods using the raw ref
      // as receiver so that we don't have to call `toRaw` on the ref in all
      // its class methods
      /* @__PURE__ */ C(e) ? e : s
    );
    if ((H(n) ? Xt.has(n) : Le(n)) || (r || g(e, "get", n), o))
      return i;
    if (/* @__PURE__ */ C(i)) {
      const a = c && $t(n) ? i : i.value;
      return r && _(a) ? /* @__PURE__ */ xt(a) : a;
    }
    return _(i) ? r ? /* @__PURE__ */ xt(i) : /* @__PURE__ */ oe(i) : i;
  }
}
class Be extends te {
  constructor(e = !1) {
    super(!1, e);
  }
  set(e, n, s, r) {
    let o = e[n];
    const c = h(e) && $t(n);
    if (!this._isShallow) {
      const u = /* @__PURE__ */ V(o);
      if (!/* @__PURE__ */ N(s) && !/* @__PURE__ */ V(s) && (o = /* @__PURE__ */ p(o), s = /* @__PURE__ */ p(s)), !c && /* @__PURE__ */ C(o) && !/* @__PURE__ */ C(s))
        return u ? (process.env.NODE_ENV !== "production" && Y(
          `Set operation on key "${String(n)}" failed: target is readonly.`,
          e[n]
        ), !0) : (o.value = s, !0);
    }
    const i = c ? Number(n) < e.length : Ot(e, n), a = Reflect.set(
      e,
      n,
      s,
      /* @__PURE__ */ C(e) ? e : r
    );
    return e === /* @__PURE__ */ p(r) && a && (i ? z(s, o) && D(e, "set", n, s, o) : D(e, "add", n, s)), a;
  }
  deleteProperty(e, n) {
    const s = Ot(e, n), r = e[n], o = Reflect.deleteProperty(e, n);
    return o && s && D(e, "delete", n, void 0, r), o;
  }
  has(e, n) {
    const s = Reflect.has(e, n);
    return (!H(n) || !Xt.has(n)) && g(e, "has", n), s;
  }
  ownKeys(e) {
    return g(
      e,
      "iterate",
      h(e) ? "length" : P
    ), Reflect.ownKeys(e);
  }
}
class Ye extends te {
  constructor(e = !1) {
    super(!0, e);
  }
  set(e, n) {
    return process.env.NODE_ENV !== "production" && Y(
      `Set operation on key "${String(n)}" failed: target is readonly.`,
      e
    ), !0;
  }
  deleteProperty(e, n) {
    return process.env.NODE_ENV !== "production" && Y(
      `Delete operation on key "${String(n)}" failed: target is readonly.`,
      e
    ), !0;
  }
}
const Je = /* @__PURE__ */ new Be(), qe = /* @__PURE__ */ new Ye(), vt = (t) => t, et = (t) => Reflect.getPrototypeOf(t);
function Ge(t, e, n) {
  return function(...s) {
    const r = this.__v_raw, o = /* @__PURE__ */ p(r), c = L(o), i = t === "entries" || t === Symbol.iterator && c, a = t === "keys" && c, u = r[t](...s), f = n ? vt : e ? J : I;
    return !e && g(
      o,
      "iterate",
      a ? Vt : P
    ), K(
      // inheriting all iterator properties
      Object.create(u),
      {
        // iterator protocol
        next() {
          const { value: l, done: d } = u.next();
          return d ? { value: l, done: d } : {
            value: i ? [f(l[0]), f(l[1])] : f(l),
            done: d
          };
        }
      }
    );
  };
}
function nt(t) {
  return function(...e) {
    if (process.env.NODE_ENV !== "production") {
      const n = e[0] ? `on key "${e[0]}" ` : "";
      Y(
        `${Ae(t)} operation ${n}failed: target is readonly.`,
        /* @__PURE__ */ p(this)
      );
    }
    return t === "delete" ? !1 : t === "clear" ? void 0 : this;
  };
}
function Ze(t, e) {
  const n = {
    get(r) {
      const o = this.__v_raw, c = /* @__PURE__ */ p(o), i = /* @__PURE__ */ p(r);
      t || (z(r, i) && g(c, "get", r), g(c, "get", i));
      const { has: a } = et(c), u = e ? vt : t ? J : I;
      if (a.call(c, r))
        return u(o.get(r));
      if (a.call(c, i))
        return u(o.get(i));
      o !== c && o.get(r);
    },
    get size() {
      const r = this.__v_raw;
      return !t && g(/* @__PURE__ */ p(r), "iterate", P), r.size;
    },
    has(r) {
      const o = this.__v_raw, c = /* @__PURE__ */ p(o), i = /* @__PURE__ */ p(r);
      return t || (z(r, i) && g(c, "has", r), g(c, "has", i)), r === i ? o.has(r) : o.has(r) || o.has(i);
    },
    forEach(r, o) {
      const c = this, i = c.__v_raw, a = /* @__PURE__ */ p(i), u = e ? vt : t ? J : I;
      return !t && g(a, "iterate", P), i.forEach((f, l) => r.call(o, u(f), u(l), c));
    }
  };
  return K(
    n,
    t ? {
      add: nt("add"),
      set: nt("set"),
      delete: nt("delete"),
      clear: nt("clear")
    } : {
      add(r) {
        const o = /* @__PURE__ */ p(this), c = et(o), i = /* @__PURE__ */ p(r), a = !e && !/* @__PURE__ */ N(r) && !/* @__PURE__ */ V(r) ? i : r;
        return c.has.call(o, a) || z(r, a) && c.has.call(o, r) || z(i, a) && c.has.call(o, i) || (o.add(a), D(o, "add", a, a)), this;
      },
      set(r, o) {
        !e && !/* @__PURE__ */ N(o) && !/* @__PURE__ */ V(o) && (o = /* @__PURE__ */ p(o));
        const c = /* @__PURE__ */ p(this), { has: i, get: a } = et(c);
        let u = i.call(c, r);
        u ? process.env.NODE_ENV !== "production" && kt(c, i, r) : (r = /* @__PURE__ */ p(r), u = i.call(c, r));
        const f = a.call(c, r);
        return c.set(r, o), u ? z(o, f) && D(c, "set", r, o, f) : D(c, "add", r, o), this;
      },
      delete(r) {
        const o = /* @__PURE__ */ p(this), { has: c, get: i } = et(o);
        let a = c.call(o, r);
        a ? process.env.NODE_ENV !== "production" && kt(o, c, r) : (r = /* @__PURE__ */ p(r), a = c.call(o, r));
        const u = i ? i.call(o, r) : void 0, f = o.delete(r);
        return a && D(o, "delete", r, void 0, u), f;
      },
      clear() {
        const r = /* @__PURE__ */ p(this), o = r.size !== 0, c = process.env.NODE_ENV !== "production" ? L(r) ? new Map(r) : new Set(r) : void 0, i = r.clear();
        return o && D(
          r,
          "clear",
          void 0,
          void 0,
          c
        ), i;
      }
    }
  ), [
    "keys",
    "values",
    "entries",
    Symbol.iterator
  ].forEach((r) => {
    n[r] = Ge(r, t, e);
  }), n;
}
function ee(t, e) {
  const n = Ze(t, e);
  return (s, r, o) => r === "__v_isReactive" ? !t : r === "__v_isReadonly" ? t : r === "__v_raw" ? s : Reflect.get(
    Ot(n, r) && r in s ? n : s,
    r,
    o
  );
}
const Qe = {
  get: /* @__PURE__ */ ee(!1, !1)
}, Xe = {
  get: /* @__PURE__ */ ee(!0, !1)
};
function kt(t, e, n) {
  const s = /* @__PURE__ */ p(n);
  if (s !== n && e.call(t, s)) {
    const r = Yt(t);
    Y(
      `Reactive ${r} contains both the raw and reactive versions of the same object${r === "Map" ? " as keys" : ""}, which can lead to inconsistencies. Avoid differentiating between the raw and reactive versions of an object and only use the reactive version if possible.`
    );
  }
}
const ne = /* @__PURE__ */ new WeakMap(), tn = /* @__PURE__ */ new WeakMap(), re = /* @__PURE__ */ new WeakMap(), en = /* @__PURE__ */ new WeakMap();
function nn(t) {
  switch (t) {
    case "Object":
    case "Array":
      return 1;
    case "Map":
    case "Set":
    case "WeakMap":
    case "WeakSet":
      return 2;
    default:
      return 0;
  }
}
// @__NO_SIDE_EFFECTS__
function oe(t) {
  return /* @__PURE__ */ V(t) ? t : se(
    t,
    !1,
    Je,
    Qe,
    ne
  );
}
// @__NO_SIDE_EFFECTS__
function xt(t) {
  return se(
    t,
    !0,
    qe,
    Xe,
    re
  );
}
function se(t, e, n, s, r) {
  if (!_(t))
    return process.env.NODE_ENV !== "production" && Y(
      `value cannot be made ${e ? "readonly" : "reactive"}: ${String(
        t
      )}`
    ), t;
  if (t.__v_raw && !(e && t.__v_isReactive) || t.__v_skip || !Object.isExtensible(t))
    return t;
  const o = r.get(t);
  if (o)
    return o;
  const c = nn(Yt(t));
  if (c === 0)
    return t;
  const i = new Proxy(
    t,
    c === 2 ? s : n
  );
  return r.set(t, i), i;
}
// @__NO_SIDE_EFFECTS__
function _t(t) {
  return /* @__PURE__ */ V(t) ? /* @__PURE__ */ _t(t.__v_raw) : !!(t && t.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function V(t) {
  return !!(t && t.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function N(t) {
  return !!(t && t.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function st(t) {
  return t ? !!t.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function p(t) {
  const e = t && t.__v_raw;
  return e ? /* @__PURE__ */ p(e) : t;
}
const I = (t) => _(t) ? /* @__PURE__ */ oe(t) : t, J = (t) => _(t) ? /* @__PURE__ */ xt(t) : t;
// @__NO_SIDE_EFFECTS__
function C(t) {
  return t ? t.__v_isRef === !0 : !1;
}
function zn(t) {
  return /* @__PURE__ */ C(t) ? t.value : t;
}
/**
* @vue/runtime-core v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
const F = [];
function rn(t) {
  F.push(t);
}
function on() {
  F.pop();
}
let Et = !1;
function j(t, ...e) {
  if (Et) return;
  Et = !0, dt();
  const n = F.length ? F[F.length - 1].component : null, s = n && n.appContext.config.warnHandler, r = sn();
  if (s)
    Ft(
      s,
      n,
      11,
      [
        // eslint-disable-next-line no-restricted-syntax
        t + e.map((o) => {
          var c, i;
          return (i = (c = o.toString) == null ? void 0 : c.call(o)) != null ? i : JSON.stringify(o);
        }).join(""),
        n && n.proxy,
        r.map(
          ({ vnode: o }) => `at <${Oe(n, o.type)}>`
        ).join(`
`),
        r
      ]
    );
  else {
    const o = [`[Vue warn]: ${t}`, ...e];
    r.length && o.push(`
`, ...cn(r)), console.warn(...o);
  }
  pt(), Et = !1;
}
function sn() {
  let t = F[F.length - 1];
  if (!t)
    return [];
  const e = [];
  for (; t; ) {
    const n = e[0];
    n && n.vnode === t ? n.recurseCount++ : e.push({
      vnode: t,
      recurseCount: 0
    });
    const s = t.component && t.component.parent;
    t = s && s.vnode;
  }
  return e;
}
function cn(t) {
  const e = [];
  return t.forEach((n, s) => {
    e.push(...s === 0 ? [] : [`
`], ...an(n));
  }), e;
}
function an({ vnode: t, recurseCount: e }) {
  const n = e > 0 ? `... (${e} recursive calls)` : "", s = t.component ? t.component.parent == null : !1, r = ` at <${Oe(
    t.component,
    t.type,
    s
  )}`, o = ">" + n;
  return t.props ? [r, ...ln(t.props), o] : [r + o];
}
function ln(t) {
  const e = [], n = Object.keys(t);
  return n.slice(0, 3).forEach((s) => {
    e.push(...ie(s, t[s]));
  }), n.length > 3 && e.push(" ..."), e;
}
function ie(t, e, n) {
  return S(e) ? (e = JSON.stringify(e), n ? e : [`${t}=${e}`]) : typeof e == "number" || typeof e == "boolean" || e == null ? n ? e : [`${t}=${e}`] : /* @__PURE__ */ C(e) ? (e = ie(t, /* @__PURE__ */ p(e.value), !0), n ? e : [`${t}=Ref<`, e, ">"]) : M(e) ? [`${t}=fn${e.name ? `<${e.name}>` : ""}`] : (e = /* @__PURE__ */ p(e), n ? e : [`${t}=`, e]);
}
const ce = {
  sp: "serverPrefetch hook",
  bc: "beforeCreate hook",
  c: "created hook",
  bm: "beforeMount hook",
  m: "mounted hook",
  bu: "beforeUpdate hook",
  u: "updated",
  bum: "beforeUnmount hook",
  um: "unmounted hook",
  a: "activated hook",
  da: "deactivated hook",
  ec: "errorCaptured hook",
  rtc: "renderTracked hook",
  rtg: "renderTriggered hook",
  0: "setup function",
  1: "render function",
  2: "watcher getter",
  3: "watcher callback",
  4: "watcher cleanup function",
  5: "native event handler",
  6: "component event handler",
  7: "vnode hook",
  8: "directive hook",
  9: "transition hook",
  10: "app errorHandler",
  11: "app warnHandler",
  12: "ref function",
  13: "async component loader",
  14: "scheduler flush",
  15: "component update",
  16: "app unmount cleanup function"
};
function Ft(t, e, n, s) {
  try {
    return s ? t(...s) : t();
  } catch (r) {
    ae(r, e, n);
  }
}
function ae(t, e, n, s = !0) {
  const r = e ? e.vnode : null, { errorHandler: o, throwUnhandledErrorInProduction: c } = e && e.appContext.config || St;
  if (e) {
    let i = e.parent;
    const a = e.proxy, u = process.env.NODE_ENV !== "production" ? ce[n] : `https://vuejs.org/error-reference/#runtime-${n}`;
    for (; i; ) {
      const f = i.ec;
      if (f) {
        for (let l = 0; l < f.length; l++)
          if (f[l](t, a, u) === !1)
            return;
      }
      i = i.parent;
    }
    if (o) {
      dt(), Ft(o, null, 10, [
        t,
        a,
        u
      ]), pt();
      return;
    }
  }
  un(t, n, r, s, c);
}
function un(t, e, n, s = !0, r = !1) {
  if (process.env.NODE_ENV !== "production") {
    const o = ce[e];
    if (n && rn(n), j(`Unhandled error${o ? ` during execution of ${o}` : ""}`), n && on(), s)
      throw t;
    console.error(t);
  } else {
    if (r)
      throw t;
    console.error(t);
  }
}
const y = [];
let x = -1;
const U = [];
let $ = null, W = 0;
const fn = /* @__PURE__ */ Promise.resolve();
let Tt = null;
const dn = 100;
function pn(t) {
  let e = x + 1, n = y.length;
  for (; e < n; ) {
    const s = e + n >>> 1, r = y[s], o = X(r);
    o < t || o === t && r.flags & 2 ? e = s + 1 : n = s;
  }
  return e;
}
function hn(t) {
  if (!(t.flags & 1)) {
    const e = X(t), n = y[y.length - 1];
    !n || // fast path when the job id is larger than the tail
    !(t.flags & 2) && e >= X(n) ? y.push(t) : y.splice(pn(e), 0, t), t.flags |= 1, le();
  }
}
function le() {
  Tt || (Tt = fn.then(ue));
}
function _n(t) {
  h(t) ? U.push(...t) : $ && t.id === -1 ? $.splice(W + 1, 0, t) : t.flags & 1 || (U.push(t), t.flags |= 1), le();
}
function gn(t) {
  if (U.length) {
    const e = [...new Set(U)].sort(
      (n, s) => X(n) - X(s)
    );
    if (U.length = 0, $) {
      $.push(...e);
      return;
    }
    for ($ = e, process.env.NODE_ENV !== "production" && (t = t || /* @__PURE__ */ new Map()), W = 0; W < $.length; W++) {
      const n = $[W];
      process.env.NODE_ENV !== "production" && fe(t, n) || (n.flags & 4 && (n.flags &= -2), n.flags & 8 || n(), n.flags &= -2);
    }
    $ = null, W = 0;
  }
}
const X = (t) => t.id == null ? t.flags & 2 ? -1 : 1 / 0 : t.id;
function ue(t) {
  process.env.NODE_ENV !== "production" && (t = t || /* @__PURE__ */ new Map());
  const e = process.env.NODE_ENV !== "production" ? (n) => fe(t, n) : Ut;
  try {
    for (x = 0; x < y.length; x++) {
      const n = y[x];
      if (n && !(n.flags & 8)) {
        if (process.env.NODE_ENV !== "production" && e(n))
          continue;
        n.flags & 4 && (n.flags &= -2), Ft(
          n,
          n.i,
          n.i ? 15 : 14
        ), n.flags & 4 || (n.flags &= -2);
      }
    }
  } finally {
    for (; x < y.length; x++) {
      const n = y[x];
      n && (n.flags &= -2);
    }
    x = -1, y.length = 0, gn(t), Tt = null, (y.length || U.length) && ue(t);
  }
}
function fe(t, e) {
  const n = t.get(e) || 0;
  if (n > dn) {
    const s = e.i, r = s && Se(s.type);
    return ae(
      `Maximum recursive updates exceeded${r ? ` in component <${r}>` : ""}. This means you have a reactive effect that is mutating its own dependencies and thus recursively triggering itself. Possible sources include component template, render function, updated hook or watcher source function.`,
      null,
      10
    ), !0;
  }
  return t.set(e, n + 1), !1;
}
const yt = /* @__PURE__ */ new Map();
process.env.NODE_ENV !== "production" && (ft().__VUE_HMR_RUNTIME__ = {
  createRecord: Nt(mn),
  rerender: Nt(bn),
  reload: Nt(wn)
});
const it = /* @__PURE__ */ new Map();
function mn(t, e) {
  return it.has(t) ? !1 : (it.set(t, {
    initialDef: ct(e),
    instances: /* @__PURE__ */ new Set()
  }), !0);
}
function ct(t) {
  return Re(t) ? t.__vccOpts : t;
}
function bn(t, e) {
  const n = it.get(t);
  n && (n.initialDef.render = e, [...n.instances].forEach((s) => {
    e && (s.render = e, ct(s.type).render = e), s.renderCache = [], s.job.flags & 8 || s.update();
  }));
}
function wn(t, e) {
  const n = it.get(t);
  if (!n) return;
  e = ct(e), zt(n.initialDef, e);
  const s = [...n.instances];
  for (let r = 0; r < s.length; r++) {
    const o = s[r], c = ct(o.type);
    let i = yt.get(c);
    i || (c !== n.initialDef && zt(c, e), yt.set(c, i = /* @__PURE__ */ new Set())), i.add(o), o.appContext.propsCache.delete(o.type), o.appContext.emitsCache.delete(o.type), o.appContext.optionsCache.delete(o.type), o.ceReload ? (i.add(o), o.ceReload(e.styles), i.delete(o)) : o.parent ? hn(() => {
      o.job.flags & 8 || (o.parent.update(), i.delete(o));
    }) : o.appContext.reload ? o.appContext.reload() : typeof window < "u" ? window.location.reload() : console.warn(
      "[HMR] Root or manually mounted instance modified. Full reload required."
    ), o.root.ce && o !== o.root && o.root.ce._removeChildStyle(c);
  }
  _n(() => {
    yt.clear();
  });
}
function zt(t, e) {
  K(t, e);
  for (const n in t)
    n !== "__file" && !(n in e) && delete t[n];
}
function Nt(t) {
  return (e, n) => {
    try {
      return t(e, n);
    } catch (s) {
      console.error(s), console.warn(
        "[HMR] Something went wrong during Vue component hot-reload. Full reload required."
      );
    }
  };
}
let A, Z = [], Ct = !1;
function En(t, ...e) {
  A ? A.emit(t, ...e) : Ct || Z.push({ event: t, args: e });
}
function de(t, e) {
  var n, s;
  A = t, A ? (A.enabled = !0, Z.forEach(({ event: r, args: o }) => A.emit(r, ...o)), Z = []) : /* handle late devtools injection - only do this if we are in an actual */ /* browser environment to avoid the timer handle stalling test runner exit */ /* (#4815) */ typeof window < "u" && // some envs mock window but not fully
  window.HTMLElement && // also exclude jsdom
  // eslint-disable-next-line no-restricted-syntax
  !((s = (n = window.navigator) == null ? void 0 : n.userAgent) != null && s.includes("jsdom")) ? ((e.__VUE_DEVTOOLS_HOOK_REPLAY__ = e.__VUE_DEVTOOLS_HOOK_REPLAY__ || []).push((o) => {
    de(o, e);
  }), setTimeout(() => {
    A || (e.__VUE_DEVTOOLS_HOOK_REPLAY__ = null, Ct = !0, Z = []);
  }, 3e3)) : (Ct = !0, Z = []);
}
const yn = /* @__PURE__ */ Nn(
  "component:updated"
  /* COMPONENT_UPDATED */
);
// @__NO_SIDE_EFFECTS__
function Nn(t) {
  return (e) => {
    En(
      t,
      e.appContext.app,
      e.uid,
      e.parent ? e.parent.uid : void 0,
      e
    );
  };
}
let T = null, pe = null;
function Wt(t) {
  const e = T;
  return T = t, pe = t && t.type.__scopeId || null, e;
}
function Wn(t, e = T, n) {
  if (!e || t._n)
    return t;
  const s = (...r) => {
    s._d && Lt(-1);
    const o = Wt(e), c = B.length;
    let i;
    try {
      i = t(...r);
    } finally {
      for (let a = B.length; a > c; a--) me();
      Wt(o), s._d && Lt(1);
    }
    return process.env.NODE_ENV !== "production" && yn(e), i;
  };
  return s._n = !0, s._c = !0, s._d = !0, s;
}
const Sn = (t) => t.__isTeleport;
function he(t, e) {
  t.shapeFlag & 6 && t.component ? (t.transition = e, he(t.component.subTree, e)) : t.shapeFlag & 128 ? (t.ssContent.transition = e.clone(t.ssContent), t.ssFallback.transition = e.clone(t.ssFallback)) : t.transition = e;
}
ft().requestIdleCallback;
ft().cancelIdleCallback;
const On = /* @__PURE__ */ Symbol.for("v-ndc");
function Ln(t, e, n, s) {
  let r;
  const o = n, c = h(t);
  if (c || S(t)) {
    const i = c && /* @__PURE__ */ _t(t);
    let a = !1, u = !1;
    i && (a = !/* @__PURE__ */ N(t), u = /* @__PURE__ */ V(t), t = ht(t)), r = new Array(t.length);
    for (let f = 0, l = t.length; f < l; f++)
      r[f] = e(
        a ? u ? J(I(t[f])) : I(t[f]) : t[f],
        f,
        void 0,
        o
      );
  } else if (typeof t == "number")
    if (process.env.NODE_ENV !== "production" && (!Number.isInteger(t) || t < 0))
      j(
        `The v-for range expects a positive integer value but got ${t}.`
      ), r = [];
    else {
      r = new Array(t);
      for (let i = 0; i < t; i++)
        r[i] = e(i + 1, i, void 0, o);
    }
  else if (_(t))
    if (t[Symbol.iterator])
      r = Array.from(
        t,
        (i, a) => e(i, a, void 0, o)
      );
    else {
      const i = Object.keys(t);
      r = new Array(i.length);
      for (let a = 0, u = i.length; a < u; a++) {
        const f = i[a];
        r[a] = e(t[f], f, a, o);
      }
    }
  else
    r = [];
  return r;
}
const Rn = {};
process.env.NODE_ENV !== "production" && (Rn.ownKeys = (t) => (j(
  "Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead."
), Reflect.ownKeys(t)));
const Vn = {}, _e = (t) => Object.getPrototypeOf(t) === Vn, vn = (t) => t.__isSuspense, ge = /* @__PURE__ */ Symbol.for("v-fgt"), xn = /* @__PURE__ */ Symbol.for("v-txt"), It = /* @__PURE__ */ Symbol.for("v-cmt"), B = [];
let m = null;
function Tn(t = !1) {
  B.push(m = t ? null : []);
}
function me() {
  B.pop(), m = B[B.length - 1] || null;
}
let tt = 1;
function Lt(t, e = !1) {
  tt += t, t < 0 && m && e && (m.hasOnce = !0);
}
function be(t) {
  return t.dynamicChildren = tt > 0 ? m || ve : null, me(), tt > 0 && m && m.push(t), t;
}
function Un(t, e, n, s, r, o) {
  return be(
    Ee(
      t,
      e,
      n,
      s,
      r,
      o,
      !0
    )
  );
}
function Cn(t, e, n, s, r) {
  return be(
    jt(
      t,
      e,
      n,
      s,
      r,
      !0
    )
  );
}
function In(t) {
  return t ? t.__v_isVNode === !0 : !1;
}
const $n = (...t) => ye(
  ...t
), we = ({ key: t }) => t ?? null, rt = ({
  ref: t,
  ref_key: e,
  ref_for: n
}) => (typeof t == "number" && (t = "" + t), t != null ? S(t) || /* @__PURE__ */ C(t) || M(t) ? { i: T, r: t, k: e, f: !!n } : t : null);
function Ee(t, e = null, n = null, s = 0, r = null, o = t === ge ? 0 : 1, c = !1, i = !1) {
  const a = {
    __v_isVNode: !0,
    __v_skip: !0,
    type: t,
    props: e,
    key: e && we(e),
    ref: e && rt(e),
    scopeId: pe,
    slotScopeIds: null,
    children: n,
    component: null,
    suspense: null,
    ssContent: null,
    ssFallback: null,
    dirs: null,
    transition: null,
    el: null,
    anchor: null,
    target: null,
    targetStart: null,
    targetAnchor: null,
    staticCount: 0,
    shapeFlag: o,
    patchFlag: s,
    dynamicProps: r,
    dynamicChildren: null,
    appContext: null,
    ctx: T
  };
  return i ? (lt(a, n), o & 128 && t.normalize(a)) : n && (a.shapeFlag |= S(n) ? 8 : 16), process.env.NODE_ENV !== "production" && a.key !== a.key && j("VNode created with invalid key (NaN). VNode type:", a.type), tt > 0 && // avoid a block node from tracking itself
  !c && // has current parent block
  m && // presence of a patch flag indicates this node needs patching on updates.
  // component nodes also should always be patched, because even if the
  // component doesn't need to update, it needs to persist the instance on to
  // the next vnode so that it can be properly unmounted later.
  (a.patchFlag > 0 || o & 6) && // the EVENTS flag is only for hydration and if it is the only flag, the
  // vnode should not be considered dynamic due to handler caching.
  a.patchFlag !== 32 && m.push(a), a;
}
const jt = process.env.NODE_ENV !== "production" ? $n : ye;
function ye(t, e = null, n = null, s = 0, r = null, o = !1) {
  if ((!t || t === On) && (process.env.NODE_ENV !== "production" && !t && j(`Invalid vnode type when creating vnode: ${t}.`), t = It), In(t)) {
    const i = at(
      t,
      e,
      !0
      /* mergeRef: true */
    );
    return n && lt(i, n), tt > 0 && !o && m && (i.shapeFlag & 6 ? m[m.indexOf(t)] = i : m.push(i)), i.patchFlag = -2, i;
  }
  if (Re(t) && (t = t.__vccOpts), e) {
    e = Dn(e);
    let { class: i, style: a } = e;
    i && !S(i) && (e.class = At(i)), _(a) && (/* @__PURE__ */ st(a) && !h(a) && (a = K({}, a)), e.style = Dt(a));
  }
  const c = S(t) ? 1 : vn(t) ? 128 : Sn(t) ? 64 : _(t) ? 4 : M(t) ? 2 : 0;
  return process.env.NODE_ENV !== "production" && c & 4 && /* @__PURE__ */ st(t) && (t = /* @__PURE__ */ p(t), j(
    "Vue received a Component that was made a reactive object. This can lead to unnecessary performance overhead and should be avoided by marking the component with `markRaw` or using `shallowRef` instead of `ref`.",
    `
Component that was made reactive: `,
    t
  )), Ee(
    t,
    e,
    n,
    s,
    r,
    c,
    o,
    !0
  );
}
function Dn(t) {
  return t ? /* @__PURE__ */ st(t) || _e(t) ? K({}, t) : t : null;
}
function at(t, e, n = !1, s = !1) {
  const { props: r, ref: o, patchFlag: c, children: i, transition: a } = t, u = e ? Mn(r || {}, e) : r, f = {
    __v_isVNode: !0,
    __v_skip: !0,
    type: t.type,
    props: u,
    key: u && we(u),
    ref: e && e.ref ? (
      // #2078 in the case of <component :is="vnode" ref="extra"/>
      // if the vnode itself already has a ref, cloneVNode will need to merge
      // the refs so the single vnode can be set on multiple refs
      n && o ? h(o) ? o.concat(rt(e)) : [o, rt(e)] : rt(e)
    ) : o,
    scopeId: t.scopeId,
    slotScopeIds: t.slotScopeIds,
    children: process.env.NODE_ENV !== "production" && c === -1 && h(i) ? i.map(Ne) : i,
    target: t.target,
    targetStart: t.targetStart,
    targetAnchor: t.targetAnchor,
    staticCount: t.staticCount,
    shapeFlag: t.shapeFlag,
    // if the vnode is cloned with extra props, we can no longer assume its
    // existing patch flag to be reliable and need to add the FULL_PROPS flag.
    // note: preserve flag for fragments since they use the flag for children
    // fast paths only.
    patchFlag: e && t.type !== ge ? c === -1 ? 16 : c | 16 : c,
    dynamicProps: t.dynamicProps,
    dynamicChildren: t.dynamicChildren,
    appContext: t.appContext,
    dirs: t.dirs,
    transition: a,
    // These should technically only be non-null on mounted VNodes. However,
    // they *should* be copied for kept-alive vnodes. So we just always copy
    // them since them being non-null during a mount doesn't affect the logic as
    // they will simply be overwritten.
    component: t.component,
    suspense: t.suspense,
    ssContent: t.ssContent && at(t.ssContent),
    ssFallback: t.ssFallback && at(t.ssFallback),
    placeholder: t.placeholder,
    el: t.el,
    anchor: t.anchor,
    ctx: t.ctx,
    ce: t.ce
  };
  return a && s && he(
    f,
    a.clone(f)
  ), f;
}
function Ne(t) {
  const e = at(t);
  return h(t.children) && (e.children = t.children.map(Ne)), e;
}
function An(t = " ", e = 0) {
  return jt(xn, null, t, e);
}
function Bn(t = "", e = !1) {
  return e ? (Tn(), Cn(It, null, t)) : jt(It, null, t);
}
function lt(t, e) {
  let n = 0;
  const { shapeFlag: s } = t;
  if (e == null)
    e = null;
  else if (h(e))
    n = 16;
  else if (typeof e == "object")
    if (s & 65) {
      const r = e.default;
      r && (r._c && (r._d = !1), lt(t, r()), r._c && (r._d = !0));
      return;
    } else {
      n = 32;
      const r = e._;
      !r && !_e(e) ? e._ctx = T : r === 3 && T && (T.slots._ === 1 ? e._ = 1 : (e._ = 2, t.patchFlag |= 1024));
    }
  else if (M(e)) {
    if (s & 65) {
      lt(t, { default: e });
      return;
    }
    e = { default: e, _ctx: T }, n = 32;
  } else
    e = String(e), s & 64 ? (n = 16, e = [An(e)]) : n = 8;
  t.children = e, t.shapeFlag |= n;
}
function Mn(...t) {
  const e = {};
  for (let n = 0; n < t.length; n++) {
    const s = t[n];
    for (const r in s)
      if (r === "class")
        e.class !== s.class && (e.class = At([e.class, s.class]));
      else if (r === "style")
        e.style = Dt([e.style, s.style]);
      else if (xe(r)) {
        const o = e[r], c = s[r];
        c && o !== c && !(h(o) && o.includes(c)) ? e[r] = o ? [].concat(o, c) : c : c == null && o == null && // mergeProps({ 'onUpdate:modelValue': undefined }) should not retain
        // the model listener.
        !Te(r) && (e[r] = c);
      } else r !== "" && (e[r] = s[r]);
  }
  return e;
}
{
  const t = ft(), e = (n, s) => {
    let r;
    return (r = t[n]) || (r = t[n] = []), r.push(s), (o) => {
      r.length > 1 ? r.forEach((c) => c(o)) : r[0](o);
    };
  };
  e(
    "__VUE_INSTANCE_SETTERS__",
    (n) => n
  ), e(
    "__VUE_SSR_SETTERS__",
    (n) => n
  );
}
process.env.NODE_ENV;
const Pn = /(?:^|[-_])\w/g, Fn = (t) => t.replace(Pn, (e) => e.toUpperCase()).replace(/[-_]/g, "");
function Se(t, e = !0) {
  return M(t) ? t.displayName || t.name : t.name || e && t.__name;
}
function Oe(t, e, n = !1) {
  let s = Se(e);
  if (!s && e.__file) {
    const r = e.__file.match(/([^/\\]+)\.\w+$/);
    r && (s = r[1]);
  }
  if (!s && t) {
    const r = (o) => {
      for (const c in o)
        if (o[c] === e)
          return c;
    };
    s = r(t.components) || t.parent && r(
      t.parent.type.components
    ) || r(t.appContext.components);
  }
  return s ? Fn(s) : n ? "App" : "Anonymous";
}
function Re(t) {
  return M(t) && "__vccOpts" in t;
}
function jn() {
  if (process.env.NODE_ENV === "production" || typeof window > "u")
    return;
  const t = { style: "color:#3ba776" }, e = { style: "color:#1677ff" }, n = { style: "color:#f5222d" }, s = { style: "color:#eb2f96" }, r = {
    __vue_custom_formatter: !0,
    header(l) {
      if (!_(l))
        return null;
      if (l.__isVue)
        return ["div", t, "VueInstance"];
      if (/* @__PURE__ */ C(l)) {
        dt();
        const d = l.value;
        return pt(), [
          "div",
          {},
          ["span", t, f(l)],
          "<",
          i(d),
          ">"
        ];
      } else {
        if (/* @__PURE__ */ _t(l))
          return [
            "div",
            {},
            ["span", t, /* @__PURE__ */ N(l) ? "ShallowReactive" : "Reactive"],
            "<",
            i(l),
            `>${/* @__PURE__ */ V(l) ? " (readonly)" : ""}`
          ];
        if (/* @__PURE__ */ V(l))
          return [
            "div",
            {},
            ["span", t, /* @__PURE__ */ N(l) ? "ShallowReadonly" : "Readonly"],
            "<",
            i(l),
            ">"
          ];
      }
      return null;
    },
    hasBody(l) {
      return l && l.__isVue;
    },
    body(l) {
      if (l && l.__isVue)
        return [
          "div",
          {},
          ...o(l.$)
        ];
    }
  };
  function o(l) {
    const d = [];
    l.type.props && l.props && d.push(c("props", /* @__PURE__ */ p(l.props))), l.setupState !== St && d.push(c("setup", l.setupState)), l.data !== St && d.push(c("data", /* @__PURE__ */ p(l.data)));
    const E = a(l, "computed");
    E && d.push(c("computed", E));
    const O = a(l, "inject");
    return O && d.push(c("injected", O)), d.push([
      "div",
      {},
      [
        "span",
        {
          style: s.style + ";opacity:0.66"
        },
        "$ (internal): "
      ],
      ["object", { object: l }]
    ]), d;
  }
  function c(l, d) {
    return d = K({}, d), Object.keys(d).length ? [
      "div",
      { style: "line-height:1.25em;margin-bottom:0.6em" },
      [
        "div",
        {
          style: "color:#476582"
        },
        l
      ],
      [
        "div",
        {
          style: "padding-left:1.25em"
        },
        ...Object.keys(d).map((E) => [
          "div",
          {},
          ["span", s, E + ": "],
          i(d[E], !1)
        ])
      ]
    ] : ["span", {}];
  }
  function i(l, d = !0) {
    return typeof l == "number" ? ["span", e, l] : typeof l == "string" ? ["span", n, JSON.stringify(l)] : typeof l == "boolean" ? ["span", s, l] : _(l) ? ["object", { object: d ? /* @__PURE__ */ p(l) : l }] : ["span", n, String(l)];
  }
  function a(l, d) {
    const E = l.type;
    if (M(E))
      return;
    const O = {};
    for (const q in l.ctx)
      u(E, q, d) && (O[q] = l.ctx[q]);
    return O;
  }
  function u(l, d, E) {
    const O = l[E];
    if (h(O) && O.includes(d) || _(O) && d in O || l.extends && u(l.extends, d, E) || l.mixins && l.mixins.some((q) => u(q, d, E)))
      return !0;
  }
  function f(l) {
    return /* @__PURE__ */ N(l) ? "ShallowRef" : l.effect ? "ComputedRef" : "Ref";
  }
  window.devtoolsFormatters ? window.devtoolsFormatters.push(r) : window.devtoolsFormatters = [r];
}
const Yn = process.env.NODE_ENV !== "production" ? j : Ut;
process.env.NODE_ENV;
process.env.NODE_ENV;
/**
* vue v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
function Kn() {
  jn();
}
process.env.NODE_ENV !== "production" && Kn();
const Hn = window.__etamusic.axios, b = Hn.create({ baseURL: "", timeout: 3e4 }), w = "/api/bili";
function Jn(t) {
  return b.post(`${w}/parse`, { url: t }).then((e) => e.data);
}
function qn(t) {
  return b.post(`${w}/downloads`, t).then((e) => e.data);
}
function Gn(t = 1, e = 20) {
  return b.get(`${w}/downloads`, { params: { page: t, page_size: e } }).then((n) => n.data);
}
function Zn(t) {
  return b.post(`${w}/downloads/${t}/cancel`).then((e) => e.data);
}
function Qn(t) {
  return b.delete(`${w}/downloads/${t}`).then((e) => e.data);
}
function Xn() {
  return b.get(`${w}/settings`).then((t) => t.data);
}
function tr(t) {
  return b.put(`${w}/settings`, t).then((e) => e.data);
}
function er() {
  return b.get(`${w}/target-nodes`).then((t) => t.data);
}
function nr(t) {
  return b.post(`${w}/subscriptions`, t).then((e) => e.data);
}
function rr() {
  return b.get(`${w}/subscriptions`).then((t) => t.data);
}
function or(t) {
  return b.post(`${w}/subscriptions/${t}/check`).then((e) => e.data);
}
function sr(t) {
  return b.delete(`${w}/subscriptions/${t}`).then((e) => e.data);
}
function ir(t, e) {
  return b.put(`${w}/subscriptions/${t}`, e).then((n) => n.data);
}
export {
  Yn as A,
  Xn as B,
  tr as C,
  ge as F,
  Ee as a,
  jt as b,
  Un as c,
  Bn as d,
  An as e,
  Cn as f,
  er as g,
  qn as h,
  C as i,
  Dt as j,
  Zn as k,
  Gn as l,
  Qn as m,
  At as n,
  Tn as o,
  Jn as p,
  rr as q,
  Ln as r,
  nr as s,
  Ke as t,
  zn as u,
  or as v,
  Wn as w,
  ir as x,
  sr as y,
  kn as z
};
