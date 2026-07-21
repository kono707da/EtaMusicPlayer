/**
* @vue/shared v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
// @__NO_SIDE_EFFECTS__
function ve(t) {
  const e = /* @__PURE__ */ Object.create(null);
  for (const n of t.split(",")) e[n] = 1;
  return (n) => n in e;
}
const Ot = process.env.NODE_ENV !== "production" ? Object.freeze({}) : {}, Ie = process.env.NODE_ENV !== "production" ? Object.freeze([]) : [], Bt = () => {
}, Te = (t) => t.charCodeAt(0) === 111 && t.charCodeAt(1) === 110 && // uppercase letter
(t.charCodeAt(2) > 122 || t.charCodeAt(2) < 97), xe = (t) => t.startsWith("onUpdate:"), H = Object.assign, Ce = Object.prototype.hasOwnProperty, Rt = (t, e) => Ce.call(t, e), h = Array.isArray, z = (t) => ft(t) === "[object Map]", $e = (t) => ft(t) === "[object Set]", P = (t) => typeof t == "function", N = (t) => typeof t == "string", k = (t) => typeof t == "symbol", _ = (t) => t !== null && typeof t == "object", qt = Object.prototype.toString, ft = (t) => qt.call(t), Yt = (t) => ft(t).slice(8, -1), De = (t) => ft(t) === "[object Object]", Dt = (t) => N(t) && t !== "NaN" && t[0] !== "-" && "" + parseInt(t, 10) === t, Jt = (t) => {
  const e = /* @__PURE__ */ Object.create(null);
  return (n) => e[n] || (e[n] = t(n));
}, Ae = /\B([A-Z])/g, Ln = Jt(
  (t) => t.replace(Ae, "-$1").toLowerCase()
), Me = Jt((t) => t.charAt(0).toUpperCase() + t.slice(1)), L = (t, e) => !Object.is(t, e);
let Ht;
const dt = () => Ht || (Ht = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {});
function At(t) {
  if (h(t)) {
    const e = {};
    for (let n = 0; n < t.length; n++) {
      const s = t[n], r = N(s) ? Ke(s) : At(s);
      if (r)
        for (const o in r)
          e[o] = r[o];
    }
    return e;
  } else if (N(t) || _(t))
    return t;
}
const Pe = /;(?![^(]*\))/g, Fe = /:([^]+)/, je = /\/\*[^]*?\*\//g;
function Ke(t) {
  const e = {};
  return t.replace(je, "").split(Pe).forEach((n) => {
    if (n) {
      const s = n.split(Fe);
      s.length > 1 && (e[s[0].trim()] = s[1].trim());
    }
  }), e;
}
function Mt(t) {
  let e = "";
  if (N(t))
    e = t;
  else if (h(t))
    for (let n = 0; n < t.length; n++) {
      const s = Mt(t[n]);
      s && (e += s + " ");
    }
  else if (_(t))
    for (const n in t)
      t[n] && (e += n + " ");
  return e.trim();
}
const Gt = (t) => !!(t && t.__v_isRef === !0), He = (t) => N(t) ? t : t == null ? "" : h(t) || _(t) && (t.toString === qt || !P(t.toString)) ? Gt(t) ? He(t.value) : JSON.stringify(t, Qt, 2) : String(t), Qt = (t, e) => Gt(e) ? Qt(t, e.value) : z(e) ? {
  [`Map(${e.size})`]: [...e.entries()].reduce(
    (n, [s, r], o) => (n[mt(s, o) + " =>"] = r, n),
    {}
  )
} : $e(e) ? {
  [`Set(${e.size})`]: [...e.values()].map((n) => mt(n))
} : k(e) ? mt(e) : _(e) && !h(e) && !De(e) ? String(e) : e, mt = (t, e = "") => {
  var n;
  return (
    // Symbol.description in es2019+ so we need to cast here to pass
    // the lib: es2016 check
    k(t) ? `Symbol(${(n = t.description) != null ? n : e})` : t
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
let ke, Zt = 0, yt;
function Pt() {
  Zt++;
}
function Ft() {
  if (--Zt > 0)
    return;
  let t;
  for (; yt; ) {
    let e = yt;
    for (yt = void 0; e; ) {
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
let st = !0;
const Xt = [];
function pt() {
  Xt.push(st), st = !1;
}
function ht() {
  const t = Xt.pop();
  st = t === void 0 ? !0 : t;
}
class Ue {
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
    Pt();
    try {
      if (process.env.NODE_ENV !== "production")
        for (let n = this.subsHead; n; n = n.nextSub)
          n.sub.onTrigger && !(n.sub.flags & 8) && n.sub.onTrigger(
            H(
              {
                effect: n.sub
              },
              e
            )
          );
      for (let n = this.subs; n; n = n.prevSub)
        n.sub.notify() && n.sub.dep.notify();
    } finally {
      Ft();
    }
  }
}
const Vt = /* @__PURE__ */ new WeakMap(), F = /* @__PURE__ */ Symbol(
  process.env.NODE_ENV !== "production" ? "Object iterate" : ""
), vt = /* @__PURE__ */ Symbol(
  process.env.NODE_ENV !== "production" ? "Map keys iterate" : ""
), X = /* @__PURE__ */ Symbol(
  process.env.NODE_ENV !== "production" ? "Array iterate" : ""
);
function g(t, e, n) {
  if (st && ke) {
    let s = Vt.get(t);
    s || Vt.set(t, s = /* @__PURE__ */ new Map());
    let r = s.get(n);
    r || (s.set(n, r = new Ue()), r.map = s, r.key = n), process.env.NODE_ENV !== "production" ? r.track({
      target: t,
      type: e,
      key: n
    }) : r.track();
  }
}
function A(t, e, n, s, r, o) {
  const c = Vt.get(t);
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
  if (Pt(), e === "clear")
    c.forEach(i);
  else {
    const a = h(t), u = a && Dt(n);
    if (a && n === "length") {
      const f = Number(s);
      c.forEach((l, d) => {
        (d === "length" || d === X || !k(d) && d >= f) && i(l);
      });
    } else
      switch ((n !== void 0 || c.has(void 0)) && i(c.get(n)), u && i(c.get(X)), e) {
        case "add":
          a ? u && i(c.get("length")) : (i(c.get(F)), z(t) && i(c.get(vt)));
          break;
        case "delete":
          a || (i(c.get(F)), z(t) && i(c.get(vt)));
          break;
        case "set":
          z(t) && i(c.get(F));
          break;
      }
  }
  Ft();
}
function U(t) {
  const e = /* @__PURE__ */ p(t);
  return e === t ? e : (g(e, "iterate", X), /* @__PURE__ */ b(t) ? e : e.map($));
}
function _t(t) {
  return g(t = /* @__PURE__ */ p(t), "iterate", X), t;
}
function V(t, e) {
  return /* @__PURE__ */ v(t) ? J(/* @__PURE__ */ gt(t) ? $(e) : e) : $(e);
}
const Le = {
  __proto__: null,
  [Symbol.iterator]() {
    return wt(this, Symbol.iterator, (t) => V(this, t));
  },
  concat(...t) {
    return U(this).concat(
      ...t.map((e) => h(e) ? U(e) : e)
    );
  },
  entries() {
    return wt(this, "entries", (t) => (t[1] = V(this, t[1]), t));
  },
  every(t, e) {
    return I(this, "every", t, e, void 0, arguments);
  },
  filter(t, e) {
    return I(
      this,
      "filter",
      t,
      e,
      (n) => n.map((s) => V(this, s)),
      arguments
    );
  },
  find(t, e) {
    return I(
      this,
      "find",
      t,
      e,
      (n) => V(this, n),
      arguments
    );
  },
  findIndex(t, e) {
    return I(this, "findIndex", t, e, void 0, arguments);
  },
  findLast(t, e) {
    return I(
      this,
      "findLast",
      t,
      e,
      (n) => V(this, n),
      arguments
    );
  },
  findLastIndex(t, e) {
    return I(this, "findLastIndex", t, e, void 0, arguments);
  },
  // flat, flatMap could benefit from ARRAY_ITERATE but are not straight-forward to implement
  forEach(t, e) {
    return I(this, "forEach", t, e, void 0, arguments);
  },
  includes(...t) {
    return Et(this, "includes", t);
  },
  indexOf(...t) {
    return Et(this, "indexOf", t);
  },
  join(t) {
    return U(this).join(t);
  },
  // keys() iterator only reads `length`, no optimization required
  lastIndexOf(...t) {
    return Et(this, "lastIndexOf", t);
  },
  map(t, e) {
    return I(this, "map", t, e, void 0, arguments);
  },
  pop() {
    return Q(this, "pop");
  },
  push(...t) {
    return Q(this, "push", t);
  },
  reduce(t, ...e) {
    return kt(this, "reduce", t, e);
  },
  reduceRight(t, ...e) {
    return kt(this, "reduceRight", t, e);
  },
  shift() {
    return Q(this, "shift");
  },
  // slice could use ARRAY_ITERATE but also seems to beg for range tracking
  some(t, e) {
    return I(this, "some", t, e, void 0, arguments);
  },
  splice(...t) {
    return Q(this, "splice", t);
  },
  toReversed() {
    return U(this).toReversed();
  },
  toSorted(t) {
    return U(this).toSorted(t);
  },
  toSpliced(...t) {
    return U(this).toSpliced(...t);
  },
  unshift(...t) {
    return Q(this, "unshift", t);
  },
  values() {
    return wt(this, "values", (t) => V(this, t));
  }
};
function wt(t, e, n) {
  const s = _t(t), r = s[e]();
  return s !== t && !/* @__PURE__ */ b(t) && (r._next = r.next, r.next = () => {
    const o = r._next();
    return o.done || (o.value = n(o.value)), o;
  }), r;
}
const We = Array.prototype;
function I(t, e, n, s, r, o) {
  const c = _t(t), i = c !== t && !/* @__PURE__ */ b(t), a = c[e];
  if (a !== We[e]) {
    const l = a.apply(t, o);
    return i ? $(l) : l;
  }
  let u = n;
  c !== t && (i ? u = function(l, d) {
    return n.call(this, V(t, l), d, t);
  } : n.length > 2 && (u = function(l, d) {
    return n.call(this, l, d, t);
  }));
  const f = a.call(c, u, s);
  return i && r ? r(f) : f;
}
function kt(t, e, n, s) {
  const r = _t(t), o = r !== t && !/* @__PURE__ */ b(t);
  let c = n, i = !1;
  r !== t && (o ? (i = s.length === 0, c = function(u, f, l) {
    return i && (i = !1, u = V(t, u)), n.call(this, u, V(t, f), l, t);
  }) : n.length > 3 && (c = function(u, f, l) {
    return n.call(this, u, f, l, t);
  }));
  const a = r[e](c, ...s);
  return i ? V(t, a) : a;
}
function Et(t, e, n) {
  const s = /* @__PURE__ */ p(t);
  g(s, "iterate", X);
  const r = s[e](...n);
  return (r === -1 || r === !1) && /* @__PURE__ */ it(n[0]) ? (n[0] = /* @__PURE__ */ p(n[0]), s[e](...n)) : r;
}
function Q(t, e, n = []) {
  pt(), Pt();
  const s = (/* @__PURE__ */ p(t))[e].apply(t, n);
  return Ft(), ht(), s;
}
const ze = /* @__PURE__ */ ve("__proto__,__v_isRef,__isVue"), te = new Set(
  /* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((t) => t !== "arguments" && t !== "caller").map((t) => Symbol[t]).filter(k)
);
function Be(t) {
  k(t) || (t = String(t));
  const e = /* @__PURE__ */ p(this);
  return g(e, "has", t), e.hasOwnProperty(t);
}
class ee {
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
      return s === (r ? o ? nn : oe : o ? en : re).get(e) || // receiver is not the reactive proxy, but has the same prototype
      // this means the receiver is a user proxy of the reactive proxy
      Object.getPrototypeOf(e) === Object.getPrototypeOf(s) ? e : void 0;
    const c = h(e);
    if (!r) {
      let a;
      if (c && (a = Le[n]))
        return a;
      if (n === "hasOwnProperty")
        return Be;
    }
    const i = Reflect.get(
      e,
      n,
      // if this is a proxy wrapping a ref, return methods using the raw ref
      // as receiver so that we don't have to call `toRaw` on the ref in all
      // its class methods
      /* @__PURE__ */ C(e) ? e : s
    );
    if ((k(n) ? te.has(n) : ze(n)) || (r || g(e, "get", n), o))
      return i;
    if (/* @__PURE__ */ C(i)) {
      const a = c && Dt(n) ? i : i.value;
      return r && _(a) ? /* @__PURE__ */ Tt(a) : a;
    }
    return _(i) ? r ? /* @__PURE__ */ Tt(i) : /* @__PURE__ */ se(i) : i;
  }
}
class qe extends ee {
  constructor(e = !1) {
    super(!1, e);
  }
  set(e, n, s, r) {
    let o = e[n];
    const c = h(e) && Dt(n);
    if (!this._isShallow) {
      const u = /* @__PURE__ */ v(o);
      if (!/* @__PURE__ */ b(s) && !/* @__PURE__ */ v(s) && (o = /* @__PURE__ */ p(o), s = /* @__PURE__ */ p(s)), !c && /* @__PURE__ */ C(o) && !/* @__PURE__ */ C(s))
        return u ? (process.env.NODE_ENV !== "production" && Y(
          `Set operation on key "${String(n)}" failed: target is readonly.`,
          e[n]
        ), !0) : (o.value = s, !0);
    }
    const i = c ? Number(n) < e.length : Rt(e, n), a = Reflect.set(
      e,
      n,
      s,
      /* @__PURE__ */ C(e) ? e : r
    );
    return e === /* @__PURE__ */ p(r) && a && (i ? L(s, o) && A(e, "set", n, s, o) : A(e, "add", n, s)), a;
  }
  deleteProperty(e, n) {
    const s = Rt(e, n), r = e[n], o = Reflect.deleteProperty(e, n);
    return o && s && A(e, "delete", n, void 0, r), o;
  }
  has(e, n) {
    const s = Reflect.has(e, n);
    return (!k(n) || !te.has(n)) && g(e, "has", n), s;
  }
  ownKeys(e) {
    return g(
      e,
      "iterate",
      h(e) ? "length" : F
    ), Reflect.ownKeys(e);
  }
}
class Ye extends ee {
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
const Je = /* @__PURE__ */ new qe(), Ge = /* @__PURE__ */ new Ye(), It = (t) => t, nt = (t) => Reflect.getPrototypeOf(t);
function Qe(t, e, n) {
  return function(...s) {
    const r = this.__v_raw, o = /* @__PURE__ */ p(r), c = z(o), i = t === "entries" || t === Symbol.iterator && c, a = t === "keys" && c, u = r[t](...s), f = n ? It : e ? J : $;
    return !e && g(
      o,
      "iterate",
      a ? vt : F
    ), H(
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
function rt(t) {
  return function(...e) {
    if (process.env.NODE_ENV !== "production") {
      const n = e[0] ? `on key "${e[0]}" ` : "";
      Y(
        `${Me(t)} operation ${n}failed: target is readonly.`,
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
      t || (L(r, i) && g(c, "get", r), g(c, "get", i));
      const { has: a } = nt(c), u = e ? It : t ? J : $;
      if (a.call(c, r))
        return u(o.get(r));
      if (a.call(c, i))
        return u(o.get(i));
      o !== c && o.get(r);
    },
    get size() {
      const r = this.__v_raw;
      return !t && g(/* @__PURE__ */ p(r), "iterate", F), r.size;
    },
    has(r) {
      const o = this.__v_raw, c = /* @__PURE__ */ p(o), i = /* @__PURE__ */ p(r);
      return t || (L(r, i) && g(c, "has", r), g(c, "has", i)), r === i ? o.has(r) : o.has(r) || o.has(i);
    },
    forEach(r, o) {
      const c = this, i = c.__v_raw, a = /* @__PURE__ */ p(i), u = e ? It : t ? J : $;
      return !t && g(a, "iterate", F), i.forEach((f, l) => r.call(o, u(f), u(l), c));
    }
  };
  return H(
    n,
    t ? {
      add: rt("add"),
      set: rt("set"),
      delete: rt("delete"),
      clear: rt("clear")
    } : {
      add(r) {
        const o = /* @__PURE__ */ p(this), c = nt(o), i = /* @__PURE__ */ p(r), a = !e && !/* @__PURE__ */ b(r) && !/* @__PURE__ */ v(r) ? i : r;
        return c.has.call(o, a) || L(r, a) && c.has.call(o, r) || L(i, a) && c.has.call(o, i) || (o.add(a), A(o, "add", a, a)), this;
      },
      set(r, o) {
        !e && !/* @__PURE__ */ b(o) && !/* @__PURE__ */ v(o) && (o = /* @__PURE__ */ p(o));
        const c = /* @__PURE__ */ p(this), { has: i, get: a } = nt(c);
        let u = i.call(c, r);
        u ? process.env.NODE_ENV !== "production" && Ut(c, i, r) : (r = /* @__PURE__ */ p(r), u = i.call(c, r));
        const f = a.call(c, r);
        return c.set(r, o), u ? L(o, f) && A(c, "set", r, o, f) : A(c, "add", r, o), this;
      },
      delete(r) {
        const o = /* @__PURE__ */ p(this), { has: c, get: i } = nt(o);
        let a = c.call(o, r);
        a ? process.env.NODE_ENV !== "production" && Ut(o, c, r) : (r = /* @__PURE__ */ p(r), a = c.call(o, r));
        const u = i ? i.call(o, r) : void 0, f = o.delete(r);
        return a && A(o, "delete", r, void 0, u), f;
      },
      clear() {
        const r = /* @__PURE__ */ p(this), o = r.size !== 0, c = process.env.NODE_ENV !== "production" ? z(r) ? new Map(r) : new Set(r) : void 0, i = r.clear();
        return o && A(
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
    n[r] = Qe(r, t, e);
  }), n;
}
function ne(t, e) {
  const n = Ze(t, e);
  return (s, r, o) => r === "__v_isReactive" ? !t : r === "__v_isReadonly" ? t : r === "__v_raw" ? s : Reflect.get(
    Rt(n, r) && r in s ? n : s,
    r,
    o
  );
}
const Xe = {
  get: /* @__PURE__ */ ne(!1, !1)
}, tn = {
  get: /* @__PURE__ */ ne(!0, !1)
};
function Ut(t, e, n) {
  const s = /* @__PURE__ */ p(n);
  if (s !== n && e.call(t, s)) {
    const r = Yt(t);
    Y(
      `Reactive ${r} contains both the raw and reactive versions of the same object${r === "Map" ? " as keys" : ""}, which can lead to inconsistencies. Avoid differentiating between the raw and reactive versions of an object and only use the reactive version if possible.`
    );
  }
}
const re = /* @__PURE__ */ new WeakMap(), en = /* @__PURE__ */ new WeakMap(), oe = /* @__PURE__ */ new WeakMap(), nn = /* @__PURE__ */ new WeakMap();
function rn(t) {
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
function se(t) {
  return /* @__PURE__ */ v(t) ? t : ie(
    t,
    !1,
    Je,
    Xe,
    re
  );
}
// @__NO_SIDE_EFFECTS__
function Tt(t) {
  return ie(
    t,
    !0,
    Ge,
    tn,
    oe
  );
}
function ie(t, e, n, s, r) {
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
  const c = rn(Yt(t));
  if (c === 0)
    return t;
  const i = new Proxy(
    t,
    c === 2 ? s : n
  );
  return r.set(t, i), i;
}
// @__NO_SIDE_EFFECTS__
function gt(t) {
  return /* @__PURE__ */ v(t) ? /* @__PURE__ */ gt(t.__v_raw) : !!(t && t.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function v(t) {
  return !!(t && t.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function b(t) {
  return !!(t && t.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function it(t) {
  return t ? !!t.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function p(t) {
  const e = t && t.__v_raw;
  return e ? /* @__PURE__ */ p(e) : t;
}
const $ = (t) => _(t) ? /* @__PURE__ */ se(t) : t, J = (t) => _(t) ? /* @__PURE__ */ Tt(t) : t;
// @__NO_SIDE_EFFECTS__
function C(t) {
  return t ? t.__v_isRef === !0 : !1;
}
function Wn(t) {
  return /* @__PURE__ */ C(t) ? t.value : t;
}
/**
* @vue/runtime-core v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
const j = [];
function on(t) {
  j.push(t);
}
function sn() {
  j.pop();
}
let bt = !1;
function K(t, ...e) {
  if (bt) return;
  bt = !0, pt();
  const n = j.length ? j[j.length - 1].component : null, s = n && n.appContext.config.warnHandler, r = cn();
  if (s)
    jt(
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
          ({ vnode: o }) => `at <${Re(n, o.type)}>`
        ).join(`
`),
        r
      ]
    );
  else {
    const o = [`[Vue warn]: ${t}`, ...e];
    r.length && o.push(`
`, ...an(r)), console.warn(...o);
  }
  ht(), bt = !1;
}
function cn() {
  let t = j[j.length - 1];
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
function an(t) {
  const e = [];
  return t.forEach((n, s) => {
    e.push(...s === 0 ? [] : [`
`], ...ln(n));
  }), e;
}
function ln({ vnode: t, recurseCount: e }) {
  const n = e > 0 ? `... (${e} recursive calls)` : "", s = t.component ? t.component.parent == null : !1, r = ` at <${Re(
    t.component,
    t.type,
    s
  )}`, o = ">" + n;
  return t.props ? [r, ...un(t.props), o] : [r + o];
}
function un(t) {
  const e = [], n = Object.keys(t);
  return n.slice(0, 3).forEach((s) => {
    e.push(...ce(s, t[s]));
  }), n.length > 3 && e.push(" ..."), e;
}
function ce(t, e, n) {
  return N(e) ? (e = JSON.stringify(e), n ? e : [`${t}=${e}`]) : typeof e == "number" || typeof e == "boolean" || e == null ? n ? e : [`${t}=${e}`] : /* @__PURE__ */ C(e) ? (e = ce(t, /* @__PURE__ */ p(e.value), !0), n ? e : [`${t}=Ref<`, e, ">"]) : P(e) ? [`${t}=fn${e.name ? `<${e.name}>` : ""}`] : (e = /* @__PURE__ */ p(e), n ? e : [`${t}=`, e]);
}
const ae = {
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
function jt(t, e, n, s) {
  try {
    return s ? t(...s) : t();
  } catch (r) {
    le(r, e, n);
  }
}
function le(t, e, n, s = !0) {
  const r = e ? e.vnode : null, { errorHandler: o, throwUnhandledErrorInProduction: c } = e && e.appContext.config || Ot;
  if (e) {
    let i = e.parent;
    const a = e.proxy, u = process.env.NODE_ENV !== "production" ? ae[n] : `https://vuejs.org/error-reference/#runtime-${n}`;
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
      pt(), jt(o, null, 10, [
        t,
        a,
        u
      ]), ht();
      return;
    }
  }
  fn(t, n, r, s, c);
}
function fn(t, e, n, s = !0, r = !1) {
  if (process.env.NODE_ENV !== "production") {
    const o = ae[e];
    if (n && on(n), K(`Unhandled error${o ? ` during execution of ${o}` : ""}`), n && sn(), s)
      throw t;
    console.error(t);
  } else {
    if (r)
      throw t;
    console.error(t);
  }
}
const w = [];
let T = -1;
const B = [];
let D = null, W = 0;
const dn = /* @__PURE__ */ Promise.resolve();
let xt = null;
const pn = 100;
function hn(t) {
  let e = T + 1, n = w.length;
  for (; e < n; ) {
    const s = e + n >>> 1, r = w[s], o = tt(r);
    o < t || o === t && r.flags & 2 ? e = s + 1 : n = s;
  }
  return e;
}
function _n(t) {
  if (!(t.flags & 1)) {
    const e = tt(t), n = w[w.length - 1];
    !n || // fast path when the job id is larger than the tail
    !(t.flags & 2) && e >= tt(n) ? w.push(t) : w.splice(hn(e), 0, t), t.flags |= 1, ue();
  }
}
function ue() {
  xt || (xt = dn.then(fe));
}
function gn(t) {
  h(t) ? B.push(...t) : D && t.id === -1 ? D.splice(W + 1, 0, t) : t.flags & 1 || (B.push(t), t.flags |= 1), ue();
}
function mn(t) {
  if (B.length) {
    const e = [...new Set(B)].sort(
      (n, s) => tt(n) - tt(s)
    );
    if (B.length = 0, D) {
      D.push(...e);
      return;
    }
    for (D = e, process.env.NODE_ENV !== "production" && (t = t || /* @__PURE__ */ new Map()), W = 0; W < D.length; W++) {
      const n = D[W];
      process.env.NODE_ENV !== "production" && de(t, n) || (n.flags & 4 && (n.flags &= -2), n.flags & 8 || n(), n.flags &= -2);
    }
    D = null, W = 0;
  }
}
const tt = (t) => t.id == null ? t.flags & 2 ? -1 : 1 / 0 : t.id;
function fe(t) {
  process.env.NODE_ENV !== "production" && (t = t || /* @__PURE__ */ new Map());
  const e = process.env.NODE_ENV !== "production" ? (n) => de(t, n) : Bt;
  try {
    for (T = 0; T < w.length; T++) {
      const n = w[T];
      if (n && !(n.flags & 8)) {
        if (process.env.NODE_ENV !== "production" && e(n))
          continue;
        n.flags & 4 && (n.flags &= -2), jt(
          n,
          n.i,
          n.i ? 15 : 14
        ), n.flags & 4 || (n.flags &= -2);
      }
    }
  } finally {
    for (; T < w.length; T++) {
      const n = w[T];
      n && (n.flags &= -2);
    }
    T = -1, w.length = 0, mn(t), xt = null, (w.length || B.length) && fe(t);
  }
}
function de(t, e) {
  const n = t.get(e) || 0;
  if (n > pn) {
    const s = e.i, r = s && Oe(s.type);
    return le(
      `Maximum recursive updates exceeded${r ? ` in component <${r}>` : ""}. This means you have a reactive effect that is mutating its own dependencies and thus recursively triggering itself. Possible sources include component template, render function, updated hook or watcher source function.`,
      null,
      10
    ), !0;
  }
  return t.set(e, n + 1), !1;
}
const Nt = /* @__PURE__ */ new Map();
process.env.NODE_ENV !== "production" && (dt().__VUE_HMR_RUNTIME__ = {
  createRecord: St(yn),
  rerender: St(wn),
  reload: St(En)
});
const ct = /* @__PURE__ */ new Map();
function yn(t, e) {
  return ct.has(t) ? !1 : (ct.set(t, {
    initialDef: at(e),
    instances: /* @__PURE__ */ new Set()
  }), !0);
}
function at(t) {
  return Ve(t) ? t.__vccOpts : t;
}
function wn(t, e) {
  const n = ct.get(t);
  n && (n.initialDef.render = e, [...n.instances].forEach((s) => {
    e && (s.render = e, at(s.type).render = e), s.renderCache = [], s.job.flags & 8 || s.update();
  }));
}
function En(t, e) {
  const n = ct.get(t);
  if (!n) return;
  e = at(e), Lt(n.initialDef, e);
  const s = [...n.instances];
  for (let r = 0; r < s.length; r++) {
    const o = s[r], c = at(o.type);
    let i = Nt.get(c);
    i || (c !== n.initialDef && Lt(c, e), Nt.set(c, i = /* @__PURE__ */ new Set())), i.add(o), o.appContext.propsCache.delete(o.type), o.appContext.emitsCache.delete(o.type), o.appContext.optionsCache.delete(o.type), o.ceReload ? (i.add(o), o.ceReload(e.styles), i.delete(o)) : o.parent ? _n(() => {
      o.job.flags & 8 || (o.parent.update(), i.delete(o));
    }) : o.appContext.reload ? o.appContext.reload() : typeof window < "u" ? window.location.reload() : console.warn(
      "[HMR] Root or manually mounted instance modified. Full reload required."
    ), o.root.ce && o !== o.root && o.root.ce._removeChildStyle(c);
  }
  gn(() => {
    Nt.clear();
  });
}
function Lt(t, e) {
  H(t, e);
  for (const n in t)
    n !== "__file" && !(n in e) && delete t[n];
}
function St(t) {
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
let M, Z = [], Ct = !1;
function bn(t, ...e) {
  M ? M.emit(t, ...e) : Ct || Z.push({ event: t, args: e });
}
function pe(t, e) {
  var n, s;
  M = t, M ? (M.enabled = !0, Z.forEach(({ event: r, args: o }) => M.emit(r, ...o)), Z = []) : /* handle late devtools injection - only do this if we are in an actual */ /* browser environment to avoid the timer handle stalling test runner exit */ /* (#4815) */ typeof window < "u" && // some envs mock window but not fully
  window.HTMLElement && // also exclude jsdom
  // eslint-disable-next-line no-restricted-syntax
  !((s = (n = window.navigator) == null ? void 0 : n.userAgent) != null && s.includes("jsdom")) ? ((e.__VUE_DEVTOOLS_HOOK_REPLAY__ = e.__VUE_DEVTOOLS_HOOK_REPLAY__ || []).push((o) => {
    pe(o, e);
  }), setTimeout(() => {
    M || (e.__VUE_DEVTOOLS_HOOK_REPLAY__ = null, Ct = !0, Z = []);
  }, 3e3)) : (Ct = !0, Z = []);
}
const Nn = /* @__PURE__ */ Sn(
  "component:updated"
  /* COMPONENT_UPDATED */
);
// @__NO_SIDE_EFFECTS__
function Sn(t) {
  return (e) => {
    bn(
      t,
      e.appContext.app,
      e.uid,
      e.parent ? e.parent.uid : void 0,
      e
    );
  };
}
let x = null, he = null;
function Wt(t) {
  const e = x;
  return x = t, he = t && t.type.__scopeId || null, e;
}
function zn(t, e = x, n) {
  if (!e || t._n)
    return t;
  const s = (...r) => {
    s._d && zt(-1);
    const o = Wt(e), c = q.length;
    let i;
    try {
      i = t(...r);
    } finally {
      for (let a = q.length; a > c; a--) ye();
      Wt(o), s._d && zt(1);
    }
    return process.env.NODE_ENV !== "production" && Nn(e), i;
  };
  return s._n = !0, s._c = !0, s._d = !0, s;
}
const On = (t) => t.__isTeleport;
function _e(t, e) {
  t.shapeFlag & 6 && t.component ? (t.transition = e, _e(t.component.subTree, e)) : t.shapeFlag & 128 ? (t.ssContent.transition = e.clone(t.ssContent), t.ssFallback.transition = e.clone(t.ssFallback)) : t.transition = e;
}
dt().requestIdleCallback;
dt().cancelIdleCallback;
const Rn = /* @__PURE__ */ Symbol.for("v-ndc");
function Bn(t, e, n, s) {
  let r;
  const o = n, c = h(t);
  if (c || N(t)) {
    const i = c && /* @__PURE__ */ gt(t);
    let a = !1, u = !1;
    i && (a = !/* @__PURE__ */ b(t), u = /* @__PURE__ */ v(t), t = _t(t)), r = new Array(t.length);
    for (let f = 0, l = t.length; f < l; f++)
      r[f] = e(
        a ? u ? J($(t[f])) : $(t[f]) : t[f],
        f,
        void 0,
        o
      );
  } else if (typeof t == "number")
    if (process.env.NODE_ENV !== "production" && (!Number.isInteger(t) || t < 0))
      K(
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
const Vn = {};
process.env.NODE_ENV !== "production" && (Vn.ownKeys = (t) => (K(
  "Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead."
), Reflect.ownKeys(t)));
const vn = {}, ge = (t) => Object.getPrototypeOf(t) === vn, In = (t) => t.__isSuspense, me = /* @__PURE__ */ Symbol.for("v-fgt"), Tn = /* @__PURE__ */ Symbol.for("v-txt"), $t = /* @__PURE__ */ Symbol.for("v-cmt"), q = [];
let m = null;
function xn(t = !1) {
  q.push(m = t ? null : []);
}
function ye() {
  q.pop(), m = q[q.length - 1] || null;
}
let et = 1;
function zt(t, e = !1) {
  et += t, t < 0 && m && e && (m.hasOnce = !0);
}
function we(t) {
  return t.dynamicChildren = et > 0 ? m || Ie : null, ye(), et > 0 && m && m.push(t), t;
}
function qn(t, e, n, s, r, o) {
  return we(
    be(
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
  return we(
    Kt(
      t,
      e,
      n,
      s,
      r,
      !0
    )
  );
}
function $n(t) {
  return t ? t.__v_isVNode === !0 : !1;
}
const Dn = (...t) => Ne(
  ...t
), Ee = ({ key: t }) => t ?? null, ot = ({
  ref: t,
  ref_key: e,
  ref_for: n
}) => (typeof t == "number" && (t = "" + t), t != null ? N(t) || /* @__PURE__ */ C(t) || P(t) ? { i: x, r: t, k: e, f: !!n } : t : null);
function be(t, e = null, n = null, s = 0, r = null, o = t === me ? 0 : 1, c = !1, i = !1) {
  const a = {
    __v_isVNode: !0,
    __v_skip: !0,
    type: t,
    props: e,
    key: e && Ee(e),
    ref: e && ot(e),
    scopeId: he,
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
    ctx: x
  };
  return i ? (ut(a, n), o & 128 && t.normalize(a)) : n && (a.shapeFlag |= N(n) ? 8 : 16), process.env.NODE_ENV !== "production" && a.key !== a.key && K("VNode created with invalid key (NaN). VNode type:", a.type), et > 0 && // avoid a block node from tracking itself
  !c && // has current parent block
  m && // presence of a patch flag indicates this node needs patching on updates.
  // component nodes also should always be patched, because even if the
  // component doesn't need to update, it needs to persist the instance on to
  // the next vnode so that it can be properly unmounted later.
  (a.patchFlag > 0 || o & 6) && // the EVENTS flag is only for hydration and if it is the only flag, the
  // vnode should not be considered dynamic due to handler caching.
  a.patchFlag !== 32 && m.push(a), a;
}
const Kt = process.env.NODE_ENV !== "production" ? Dn : Ne;
function Ne(t, e = null, n = null, s = 0, r = null, o = !1) {
  if ((!t || t === Rn) && (process.env.NODE_ENV !== "production" && !t && K(`Invalid vnode type when creating vnode: ${t}.`), t = $t), $n(t)) {
    const i = lt(
      t,
      e,
      !0
      /* mergeRef: true */
    );
    return n && ut(i, n), et > 0 && !o && m && (i.shapeFlag & 6 ? m[m.indexOf(t)] = i : m.push(i)), i.patchFlag = -2, i;
  }
  if (Ve(t) && (t = t.__vccOpts), e) {
    e = An(e);
    let { class: i, style: a } = e;
    i && !N(i) && (e.class = Mt(i)), _(a) && (/* @__PURE__ */ it(a) && !h(a) && (a = H({}, a)), e.style = At(a));
  }
  const c = N(t) ? 1 : In(t) ? 128 : On(t) ? 64 : _(t) ? 4 : P(t) ? 2 : 0;
  return process.env.NODE_ENV !== "production" && c & 4 && /* @__PURE__ */ it(t) && (t = /* @__PURE__ */ p(t), K(
    "Vue received a Component that was made a reactive object. This can lead to unnecessary performance overhead and should be avoided by marking the component with `markRaw` or using `shallowRef` instead of `ref`.",
    `
Component that was made reactive: `,
    t
  )), be(
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
function An(t) {
  return t ? /* @__PURE__ */ it(t) || ge(t) ? H({}, t) : t : null;
}
function lt(t, e, n = !1, s = !1) {
  const { props: r, ref: o, patchFlag: c, children: i, transition: a } = t, u = e ? Pn(r || {}, e) : r, f = {
    __v_isVNode: !0,
    __v_skip: !0,
    type: t.type,
    props: u,
    key: u && Ee(u),
    ref: e && e.ref ? (
      // #2078 in the case of <component :is="vnode" ref="extra"/>
      // if the vnode itself already has a ref, cloneVNode will need to merge
      // the refs so the single vnode can be set on multiple refs
      n && o ? h(o) ? o.concat(ot(e)) : [o, ot(e)] : ot(e)
    ) : o,
    scopeId: t.scopeId,
    slotScopeIds: t.slotScopeIds,
    children: process.env.NODE_ENV !== "production" && c === -1 && h(i) ? i.map(Se) : i,
    target: t.target,
    targetStart: t.targetStart,
    targetAnchor: t.targetAnchor,
    staticCount: t.staticCount,
    shapeFlag: t.shapeFlag,
    // if the vnode is cloned with extra props, we can no longer assume its
    // existing patch flag to be reliable and need to add the FULL_PROPS flag.
    // note: preserve flag for fragments since they use the flag for children
    // fast paths only.
    patchFlag: e && t.type !== me ? c === -1 ? 16 : c | 16 : c,
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
    ssContent: t.ssContent && lt(t.ssContent),
    ssFallback: t.ssFallback && lt(t.ssFallback),
    placeholder: t.placeholder,
    el: t.el,
    anchor: t.anchor,
    ctx: t.ctx,
    ce: t.ce
  };
  return a && s && _e(
    f,
    a.clone(f)
  ), f;
}
function Se(t) {
  const e = lt(t);
  return h(t.children) && (e.children = t.children.map(Se)), e;
}
function Mn(t = " ", e = 0) {
  return Kt(Tn, null, t, e);
}
function Yn(t = "", e = !1) {
  return e ? (xn(), Cn($t, null, t)) : Kt($t, null, t);
}
function ut(t, e) {
  let n = 0;
  const { shapeFlag: s } = t;
  if (e == null)
    e = null;
  else if (h(e))
    n = 16;
  else if (typeof e == "object")
    if (s & 65) {
      const r = e.default;
      r && (r._c && (r._d = !1), ut(t, r()), r._c && (r._d = !0));
      return;
    } else {
      n = 32;
      const r = e._;
      !r && !ge(e) ? e._ctx = x : r === 3 && x && (x.slots._ === 1 ? e._ = 1 : (e._ = 2, t.patchFlag |= 1024));
    }
  else if (P(e)) {
    if (s & 65) {
      ut(t, { default: e });
      return;
    }
    e = { default: e, _ctx: x }, n = 32;
  } else
    e = String(e), s & 64 ? (n = 16, e = [Mn(e)]) : n = 8;
  t.children = e, t.shapeFlag |= n;
}
function Pn(...t) {
  const e = {};
  for (let n = 0; n < t.length; n++) {
    const s = t[n];
    for (const r in s)
      if (r === "class")
        e.class !== s.class && (e.class = Mt([e.class, s.class]));
      else if (r === "style")
        e.style = At([e.style, s.style]);
      else if (Te(r)) {
        const o = e[r], c = s[r];
        c && o !== c && !(h(o) && o.includes(c)) ? e[r] = o ? [].concat(o, c) : c : c == null && o == null && // mergeProps({ 'onUpdate:modelValue': undefined }) should not retain
        // the model listener.
        !xe(r) && (e[r] = c);
      } else r !== "" && (e[r] = s[r]);
  }
  return e;
}
{
  const t = dt(), e = (n, s) => {
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
const Fn = /(?:^|[-_])\w/g, jn = (t) => t.replace(Fn, (e) => e.toUpperCase()).replace(/[-_]/g, "");
function Oe(t, e = !0) {
  return P(t) ? t.displayName || t.name : t.name || e && t.__name;
}
function Re(t, e, n = !1) {
  let s = Oe(e);
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
  return s ? jn(s) : n ? "App" : "Anonymous";
}
function Ve(t) {
  return P(t) && "__vccOpts" in t;
}
function Kn() {
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
        pt();
        const d = l.value;
        return ht(), [
          "div",
          {},
          ["span", t, f(l)],
          "<",
          i(d),
          ">"
        ];
      } else {
        if (/* @__PURE__ */ gt(l))
          return [
            "div",
            {},
            ["span", t, /* @__PURE__ */ b(l) ? "ShallowReactive" : "Reactive"],
            "<",
            i(l),
            `>${/* @__PURE__ */ v(l) ? " (readonly)" : ""}`
          ];
        if (/* @__PURE__ */ v(l))
          return [
            "div",
            {},
            ["span", t, /* @__PURE__ */ b(l) ? "ShallowReadonly" : "Readonly"],
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
    l.type.props && l.props && d.push(c("props", /* @__PURE__ */ p(l.props))), l.setupState !== Ot && d.push(c("setup", l.setupState)), l.data !== Ot && d.push(c("data", /* @__PURE__ */ p(l.data)));
    const y = a(l, "computed");
    y && d.push(c("computed", y));
    const R = a(l, "inject");
    return R && d.push(c("injected", R)), d.push([
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
    return d = H({}, d), Object.keys(d).length ? [
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
        ...Object.keys(d).map((y) => [
          "div",
          {},
          ["span", s, y + ": "],
          i(d[y], !1)
        ])
      ]
    ] : ["span", {}];
  }
  function i(l, d = !0) {
    return typeof l == "number" ? ["span", e, l] : typeof l == "string" ? ["span", n, JSON.stringify(l)] : typeof l == "boolean" ? ["span", s, l] : _(l) ? ["object", { object: d ? /* @__PURE__ */ p(l) : l }] : ["span", n, String(l)];
  }
  function a(l, d) {
    const y = l.type;
    if (P(y))
      return;
    const R = {};
    for (const G in l.ctx)
      u(y, G, d) && (R[G] = l.ctx[G]);
    return R;
  }
  function u(l, d, y) {
    const R = l[y];
    if (h(R) && R.includes(d) || _(R) && d in R || l.extends && u(l.extends, d, y) || l.mixins && l.mixins.some((G) => u(G, d, y)))
      return !0;
  }
  function f(l) {
    return /* @__PURE__ */ b(l) ? "ShallowRef" : l.effect ? "ComputedRef" : "Ref";
  }
  window.devtoolsFormatters ? window.devtoolsFormatters.push(r) : window.devtoolsFormatters = [r];
}
const Jn = process.env.NODE_ENV !== "production" ? K : Bt;
process.env.NODE_ENV;
process.env.NODE_ENV;
/**
* vue v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
function Hn() {
  Kn();
}
process.env.NODE_ENV !== "production" && Hn();
const kn = window.__etamusic.axios, S = kn.create({ baseURL: "", timeout: 3e4 }), E = "/api/netease";
function O(t, e = "") {
  var r, o;
  const n = ((o = (r = t.response) == null ? void 0 : r.data) == null ? void 0 : o.detail) || t.message || "未知错误", s = e ? `${e}: ${n}` : n;
  throw new Error(s);
}
async function Gn() {
  try {
    return (await S.get(`${E}/accounts`)).data;
  } catch (t) {
    O(t, "获取账号列表失败");
  }
}
async function Qn(t) {
  try {
    return (await S.post(`${E}/accounts/switch`, null, { params: { ncm_uid: t } })).data;
  } catch (e) {
    O(e, "切换账号失败");
  }
}
async function Zn(t) {
  try {
    return (await S.delete(`${E}/accounts/${t}`)).data;
  } catch (e) {
    O(e, "删除账号失败");
  }
}
async function Xn() {
  try {
    return (await S.get(`${E}/login/qrcode/key`)).data;
  } catch (t) {
    O(t, "获取二维码 key 失败");
  }
}
async function tr(t) {
  return `${E}/login/qrcode/image?unikey=${encodeURIComponent(t)}&_t=${Date.now()}`;
}
async function er(t) {
  try {
    return (await S.get(`${E}/login/qrcode/poll`, { params: { unikey: t } })).data;
  } catch (e) {
    O(e, "查询扫码状态失败");
  }
}
async function nr() {
  try {
    return (await S.post(`${E}/login/refresh`)).data;
  } catch (t) {
    O(t, "刷新登录状态失败");
  }
}
async function rr(t, e = 1, n = 30, s = 0) {
  try {
    return (await S.get(`${E}/search`, { params: { keyword: t, type: e, limit: n, offset: s } })).data;
  } catch (r) {
    O(r, "搜索失败");
  }
}
async function or() {
  try {
    return (await S.get(`${E}/search/hot`)).data;
  } catch (t) {
    O(t, "获取热搜失败");
  }
}
async function Un(t, e = "standard") {
  try {
    const n = Array.isArray(t) ? t.join(",") : String(t);
    return (await S.get(`${E}/song/url`, { params: { ids: n, level: e } })).data;
  } catch (n) {
    O(n, "获取播放 URL 失败");
  }
}
async function sr(t) {
  try {
    return (await S.get(`${E}/playlist/detail`, { params: { id: t } })).data;
  } catch (e) {
    O(e, "获取歌单详情失败");
  }
}
async function ir() {
  try {
    return (await S.get(`${E}/user/self/playlists`)).data;
  } catch (t) {
    O(t, "获取我的歌单失败");
  }
}
async function cr(t, e = "standard") {
  if (!t || t.length === 0) return [];
  const n = t.map((o) => o.id), s = await Un(n, e), r = /* @__PURE__ */ new Map();
  for (const o of (s == null ? void 0 : s.data) || [])
    o.url && r.set(o.id, o.url);
  return t.map((o) => {
    var c, i;
    return {
      id: o.id,
      name: o.name,
      artist: (o.ar || []).map((a) => a.name).join(" / ") || "未知艺术家",
      album: ((c = o.al) == null ? void 0 : c.name) || "",
      duration: Math.floor((o.dt || 0) / 1e3),
      cover: ((i = o.al) == null ? void 0 : i.picUrl) || "",
      __streamUrl: r.get(o.id) || null,
      __nodeName: "网易云",
      __source: "netease"
    };
  }).filter((o) => o.__streamUrl);
}
export {
  Jn as A,
  me as F,
  be as a,
  Kt as b,
  qn as c,
  Cn as d,
  Yn as e,
  Mn as f,
  Xn as g,
  tr as h,
  C as i,
  or as j,
  cr as k,
  ir as l,
  nr as m,
  Mt as n,
  xn as o,
  er as p,
  Zn as q,
  Bn as r,
  rr as s,
  He as t,
  Wn as u,
  Qn as v,
  zn as w,
  Gn as x,
  sr as y,
  Ln as z
};
