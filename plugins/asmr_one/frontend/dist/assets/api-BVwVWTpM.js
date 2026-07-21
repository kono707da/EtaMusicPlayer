/**
* @vue/shared v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
// @__NO_SIDE_EFFECTS__
function bn(e) {
  const t = /* @__PURE__ */ Object.create(null);
  for (const n of e.split(",")) t[n] = 1;
  return (n) => n in t;
}
const oe = process.env.NODE_ENV !== "production" ? Object.freeze({}) : {}, Nn = process.env.NODE_ENV !== "production" ? Object.freeze([]) : [], ne = () => {
}, On = (e) => e.charCodeAt(0) === 111 && e.charCodeAt(1) === 110 && // uppercase letter
(e.charCodeAt(2) > 122 || e.charCodeAt(2) < 97), Sn = (e) => e.startsWith("onUpdate:"), D = Object.assign, xn = Object.prototype.hasOwnProperty, De = (e, t) => xn.call(e, t), y = Array.isArray, q = (e) => je(e) === "[object Map]", It = (e) => je(e) === "[object Set]", E = (e) => typeof e == "function", T = (e) => typeof e == "string", Z = (e) => typeof e == "symbol", b = (e) => e !== null && typeof e == "object", Dn = (e) => (b(e) || E(e)) && E(e.then) && E(e.catch), $t = Object.prototype.toString, je = (e) => $t.call(e), Pt = (e) => je(e).slice(8, -1), At = (e) => je(e) === "[object Object]", at = (e) => T(e) && e !== "NaN" && e[0] !== "-" && "" + parseInt(e, 10) === e, ct = (e) => {
  const t = /* @__PURE__ */ Object.create(null);
  return (n) => t[n] || (t[n] = e(n));
}, Vn = /-\w/g, Ve = ct(
  (e) => e.replace(Vn, (t) => t.slice(1).toUpperCase())
), Rn = /\B([A-Z])/g, os = ct(
  (e) => e.replace(Rn, "-$1").toLowerCase()
), Re = ct((e) => e.charAt(0).toUpperCase() + e.slice(1)), j = (e, t) => !Object.is(e, t), is = (e, ...t) => {
  for (let n = 0; n < e.length; n++)
    e[n](...t);
}, Tn = (e, t, n, s = !1) => {
  Object.defineProperty(e, t, {
    configurable: !0,
    enumerable: !1,
    writable: s,
    value: n
  });
}, as = (e) => {
  const t = parseFloat(e);
  return isNaN(t) ? e : t;
};
let vt;
const He = () => vt || (vt = typeof globalThis < "u" ? globalThis : typeof self < "u" ? self : typeof window < "u" ? window : typeof global < "u" ? global : {});
function lt(e) {
  if (y(e)) {
    const t = {};
    for (let n = 0; n < e.length; n++) {
      const s = e[n], r = T(s) ? Pn(s) : lt(s);
      if (r)
        for (const o in r)
          t[o] = r[o];
    }
    return t;
  } else if (T(e) || b(e))
    return e;
}
const Cn = /;(?![^(]*\))/g, In = /:([^]+)/, $n = /\/\*[^]*?\*\//g;
function Pn(e) {
  const t = {};
  return e.replace($n, "").split(Cn).forEach((n) => {
    if (n) {
      const s = n.split(In);
      s.length > 1 && (t[s[0].trim()] = s[1].trim());
    }
  }), t;
}
function ut(e) {
  let t = "";
  if (T(e))
    t = e;
  else if (y(e))
    for (let n = 0; n < e.length; n++) {
      const s = ut(e[n]);
      s && (t += s + " ");
    }
  else if (b(e))
    for (const n in e)
      e[n] && (t += n + " ");
  return t.trim();
}
const Mt = (e) => !!(e && e.__v_isRef === !0), An = (e) => T(e) ? e : e == null ? "" : y(e) || b(e) && (e.toString === $t || !E(e.toString)) ? Mt(e) ? An(e.value) : JSON.stringify(e, kt, 2) : String(e), kt = (e, t) => Mt(t) ? kt(e, t.value) : q(t) ? {
  [`Map(${t.size})`]: [...t.entries()].reduce(
    (n, [s, r], o) => (n[ze(s, o) + " =>"] = r, n),
    {}
  )
} : It(t) ? {
  [`Set(${t.size})`]: [...t.values()].map((n) => ze(n))
} : Z(t) ? ze(t) : b(t) && !y(t) && !At(t) ? String(t) : t, ze = (e, t = "") => {
  var n;
  return (
    // Symbol.description in es2019+ so we need to cast here to pass
    // the lib: es2016 check
    Z(e) ? `Symbol(${(n = e.description) != null ? n : t})` : e
  );
};
/**
* @vue/reactivity v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
function W(e, ...t) {
  console.warn(`[Vue warn] ${e}`, ...t);
}
let m;
const Ke = /* @__PURE__ */ new WeakSet();
class Mn {
  constructor(t) {
    this.fn = t, this.deps = void 0, this.depsTail = void 0, this.flags = 5, this.next = void 0, this.cleanup = void 0, this.scheduler = void 0;
  }
  pause() {
    this.flags |= 64;
  }
  resume() {
    this.flags & 64 && (this.flags &= -65, Ke.has(this) && (Ke.delete(this), this.trigger()));
  }
  /**
   * @internal
   */
  notify() {
    this.flags & 2 && !(this.flags & 32) || this.flags & 8 || kn(this);
  }
  run() {
    if (!(this.flags & 1))
      return this.fn();
    this.flags |= 2, Et(this), jt(this);
    const t = m, n = $;
    m = this, $ = !0;
    try {
      return this.fn();
    } finally {
      process.env.NODE_ENV !== "production" && m !== this && W(
        "Active effect was not restored correctly - this is likely a Vue internal bug."
      ), Ht(this), m = t, $ = n, this.flags &= -3;
    }
  }
  stop() {
    if (this.flags & 1) {
      for (let t = this.deps; t; t = t.nextDep)
        dt(t);
      this.deps = this.depsTail = void 0, Et(this), this.onStop && this.onStop(), this.flags &= -2;
    }
  }
  trigger() {
    this.flags & 64 ? Ke.add(this) : this.scheduler ? this.scheduler() : this.runIfDirty();
  }
  /**
   * @internal
   */
  runIfDirty() {
    Qe(this) && this.run();
  }
  get dirty() {
    return Qe(this);
  }
}
let Ft = 0, pe, de;
function kn(e, t = !1) {
  if (e.flags |= 8, t) {
    e.next = de, de = e;
    return;
  }
  e.next = pe, pe = e;
}
function ft() {
  Ft++;
}
function pt() {
  if (--Ft > 0)
    return;
  if (de) {
    let t = de;
    for (de = void 0; t; ) {
      const n = t.next;
      t.next = void 0, t.flags &= -9, t = n;
    }
  }
  let e;
  for (; pe; ) {
    let t = pe;
    for (pe = void 0; t; ) {
      const n = t.next;
      if (t.next = void 0, t.flags &= -9, t.flags & 1)
        try {
          t.trigger();
        } catch (s) {
          e || (e = s);
        }
      t = n;
    }
  }
  if (e) throw e;
}
function jt(e) {
  for (let t = e.deps; t; t = t.nextDep)
    t.version = -1, t.prevActiveLink = t.dep.activeLink, t.dep.activeLink = t;
}
function Ht(e) {
  let t, n = e.depsTail, s = n;
  for (; s; ) {
    const r = s.prevDep;
    s.version === -1 ? (s === n && (n = r), dt(s), jn(s)) : t = s, s.dep.activeLink = s.prevActiveLink, s.prevActiveLink = void 0, s = r;
  }
  e.deps = t, e.depsTail = n;
}
function Qe(e) {
  for (let t = e.deps; t; t = t.nextDep)
    if (t.dep.version !== t.version || t.dep.computed && (Fn(t.dep.computed) || t.dep.version !== t.version))
      return !0;
  return !!e._dirty;
}
function Fn(e) {
  if (e.flags & 4 && !(e.flags & 16) || (e.flags &= -17, e.globalVersion === Te) || (e.globalVersion = Te, !e.isSSR && e.flags & 128 && (!e.deps && !e._dirty || !Qe(e))))
    return;
  e.flags |= 2;
  const t = e.dep, n = m, s = $;
  m = e, $ = !0;
  try {
    jt(e);
    const r = e.fn(e._value);
    (t.version === 0 || j(r, e._value)) && (e.flags |= 128, e._value = r, t.version++);
  } catch (r) {
    throw t.version++, r;
  } finally {
    m = n, $ = s, Ht(e), e.flags &= -3;
  }
}
function dt(e, t = !1) {
  const { dep: n, prevSub: s, nextSub: r } = e;
  if (s && (s.nextSub = r, e.prevSub = void 0), r && (r.prevSub = s, e.nextSub = void 0), process.env.NODE_ENV !== "production" && n.subsHead === e && (n.subsHead = r), n.subs === e && (n.subs = s, !s && n.computed)) {
    n.computed.flags &= -5;
    for (let o = n.computed.deps; o; o = o.nextDep)
      dt(o, !0);
  }
  !t && !--n.sc && n.map && n.map.delete(n.key);
}
function jn(e) {
  const { prevDep: t, nextDep: n } = e;
  t && (t.nextDep = n, e.prevDep = void 0), n && (n.prevDep = t, e.nextDep = void 0);
}
let $ = !0;
const Wt = [];
function me() {
  Wt.push($), $ = !1;
}
function ye() {
  const e = Wt.pop();
  $ = e === void 0 ? !0 : e;
}
function Et(e) {
  const { cleanup: t } = e;
  if (e.cleanup = void 0, t) {
    const n = m;
    m = void 0;
    try {
      t();
    } finally {
      m = n;
    }
  }
}
let Te = 0;
class Hn {
  constructor(t, n) {
    this.sub = t, this.dep = n, this.version = n.version, this.nextDep = this.prevDep = this.nextSub = this.prevSub = this.prevActiveLink = void 0;
  }
}
class Wn {
  // TODO isolatedDeclarations "__v_skip"
  constructor(t) {
    this.computed = t, this.version = 0, this.activeLink = void 0, this.subs = void 0, this.map = void 0, this.key = void 0, this.sc = 0, this.__v_skip = !0, process.env.NODE_ENV !== "production" && (this.subsHead = void 0);
  }
  track(t) {
    if (!m || !$ || m === this.computed)
      return;
    let n = this.activeLink;
    if (n === void 0 || n.sub !== m)
      n = this.activeLink = new Hn(m, this), m.deps ? (n.prevDep = m.depsTail, m.depsTail.nextDep = n, m.depsTail = n) : m.deps = m.depsTail = n, Lt(n);
    else if (n.version === -1 && (n.version = this.version, n.nextDep)) {
      const s = n.nextDep;
      s.prevDep = n.prevDep, n.prevDep && (n.prevDep.nextDep = s), n.prevDep = m.depsTail, n.nextDep = void 0, m.depsTail.nextDep = n, m.depsTail = n, m.deps === n && (m.deps = s);
    }
    return process.env.NODE_ENV !== "production" && m.onTrack && m.onTrack(
      D(
        {
          effect: m
        },
        t
      )
    ), n;
  }
  trigger(t) {
    this.version++, Te++, this.notify(t);
  }
  notify(t) {
    ft();
    try {
      if (process.env.NODE_ENV !== "production")
        for (let n = this.subsHead; n; n = n.nextSub)
          n.sub.onTrigger && !(n.sub.flags & 8) && n.sub.onTrigger(
            D(
              {
                effect: n.sub
              },
              t
            )
          );
      for (let n = this.subs; n; n = n.prevSub)
        n.sub.notify() && n.sub.dep.notify();
    } finally {
      pt();
    }
  }
}
function Lt(e) {
  if (e.dep.sc++, e.sub.flags & 4) {
    const t = e.dep.computed;
    if (t && !e.dep.subs) {
      t.flags |= 20;
      for (let s = t.deps; s; s = s.nextDep)
        Lt(s);
    }
    const n = e.dep.subs;
    n !== e && (e.prevSub = n, n && (n.nextSub = e)), process.env.NODE_ENV !== "production" && e.dep.subsHead === void 0 && (e.dep.subsHead = e), e.dep.subs = e;
  }
}
const Ze = /* @__PURE__ */ new WeakMap(), G = /* @__PURE__ */ Symbol(
  process.env.NODE_ENV !== "production" ? "Object iterate" : ""
), Xe = /* @__PURE__ */ Symbol(
  process.env.NODE_ENV !== "production" ? "Map keys iterate" : ""
), he = /* @__PURE__ */ Symbol(
  process.env.NODE_ENV !== "production" ? "Array iterate" : ""
);
function O(e, t, n) {
  if ($ && m) {
    let s = Ze.get(e);
    s || Ze.set(e, s = /* @__PURE__ */ new Map());
    let r = s.get(n);
    r || (s.set(n, r = new Wn()), r.map = s, r.key = n), process.env.NODE_ENV !== "production" ? r.track({
      target: e,
      type: t,
      key: n
    }) : r.track();
  }
}
function K(e, t, n, s, r, o) {
  const i = Ze.get(e);
  if (!i) {
    Te++;
    return;
  }
  const a = (c) => {
    c && (process.env.NODE_ENV !== "production" ? c.trigger({
      target: e,
      type: t,
      key: n,
      newValue: s,
      oldValue: r,
      oldTarget: o
    }) : c.trigger());
  };
  if (ft(), t === "clear")
    i.forEach(a);
  else {
    const c = y(e), u = c && at(n);
    if (c && n === "length") {
      const p = Number(s);
      i.forEach((l, f) => {
        (f === "length" || f === he || !Z(f) && f >= p) && a(l);
      });
    } else
      switch ((n !== void 0 || i.has(void 0)) && a(i.get(n)), u && a(i.get(he)), t) {
        case "add":
          c ? u && a(i.get("length")) : (a(i.get(G)), q(e) && a(i.get(Xe)));
          break;
        case "delete":
          c || (a(i.get(G)), q(e) && a(i.get(Xe)));
          break;
        case "set":
          q(e) && a(i.get(G));
          break;
      }
  }
  pt();
}
function ee(e) {
  const t = /* @__PURE__ */ _(e);
  return t === e ? t : (O(t, "iterate", he), /* @__PURE__ */ S(e) ? t : t.map(L));
}
function We(e) {
  return O(e = /* @__PURE__ */ _(e), "iterate", he), e;
}
function A(e, t) {
  return /* @__PURE__ */ M(e) ? ie(/* @__PURE__ */ B(e) ? L(t) : t) : L(t);
}
const Ln = {
  __proto__: null,
  [Symbol.iterator]() {
    return Ue(this, Symbol.iterator, (e) => A(this, e));
  },
  concat(...e) {
    return ee(this).concat(
      ...e.map((t) => y(t) ? ee(t) : t)
    );
  },
  entries() {
    return Ue(this, "entries", (e) => (e[1] = A(this, e[1]), e));
  },
  every(e, t) {
    return k(this, "every", e, t, void 0, arguments);
  },
  filter(e, t) {
    return k(
      this,
      "filter",
      e,
      t,
      (n) => n.map((s) => A(this, s)),
      arguments
    );
  },
  find(e, t) {
    return k(
      this,
      "find",
      e,
      t,
      (n) => A(this, n),
      arguments
    );
  },
  findIndex(e, t) {
    return k(this, "findIndex", e, t, void 0, arguments);
  },
  findLast(e, t) {
    return k(
      this,
      "findLast",
      e,
      t,
      (n) => A(this, n),
      arguments
    );
  },
  findLastIndex(e, t) {
    return k(this, "findLastIndex", e, t, void 0, arguments);
  },
  // flat, flatMap could benefit from ARRAY_ITERATE but are not straight-forward to implement
  forEach(e, t) {
    return k(this, "forEach", e, t, void 0, arguments);
  },
  includes(...e) {
    return Be(this, "includes", e);
  },
  indexOf(...e) {
    return Be(this, "indexOf", e);
  },
  join(e) {
    return ee(this).join(e);
  },
  // keys() iterator only reads `length`, no optimization required
  lastIndexOf(...e) {
    return Be(this, "lastIndexOf", e);
  },
  map(e, t) {
    return k(this, "map", e, t, void 0, arguments);
  },
  pop() {
    return le(this, "pop");
  },
  push(...e) {
    return le(this, "push", e);
  },
  reduce(e, ...t) {
    return bt(this, "reduce", e, t);
  },
  reduceRight(e, ...t) {
    return bt(this, "reduceRight", e, t);
  },
  shift() {
    return le(this, "shift");
  },
  // slice could use ARRAY_ITERATE but also seems to beg for range tracking
  some(e, t) {
    return k(this, "some", e, t, void 0, arguments);
  },
  splice(...e) {
    return le(this, "splice", e);
  },
  toReversed() {
    return ee(this).toReversed();
  },
  toSorted(e) {
    return ee(this).toSorted(e);
  },
  toSpliced(...e) {
    return ee(this).toSpliced(...e);
  },
  unshift(...e) {
    return le(this, "unshift", e);
  },
  values() {
    return Ue(this, "values", (e) => A(this, e));
  }
};
function Ue(e, t, n) {
  const s = We(e), r = s[t]();
  return s !== e && !/* @__PURE__ */ S(e) && (r._next = r.next, r.next = () => {
    const o = r._next();
    return o.done || (o.value = n(o.value)), o;
  }), r;
}
const zn = Array.prototype;
function k(e, t, n, s, r, o) {
  const i = We(e), a = i !== e && !/* @__PURE__ */ S(e), c = i[t];
  if (c !== zn[t]) {
    const l = c.apply(e, o);
    return a ? L(l) : l;
  }
  let u = n;
  i !== e && (a ? u = function(l, f) {
    return n.call(this, A(e, l), f, e);
  } : n.length > 2 && (u = function(l, f) {
    return n.call(this, l, f, e);
  }));
  const p = c.call(i, u, s);
  return a && r ? r(p) : p;
}
function bt(e, t, n, s) {
  const r = We(e), o = r !== e && !/* @__PURE__ */ S(e);
  let i = n, a = !1;
  r !== e && (o ? (a = s.length === 0, i = function(u, p, l) {
    return a && (a = !1, u = A(e, u)), n.call(this, u, A(e, p), l, e);
  }) : n.length > 3 && (i = function(u, p, l) {
    return n.call(this, u, p, l, e);
  }));
  const c = r[t](i, ...s);
  return a ? A(e, c) : c;
}
function Be(e, t, n) {
  const s = /* @__PURE__ */ _(e);
  O(s, "iterate", he);
  const r = s[t](...n);
  return (r === -1 || r === !1) && /* @__PURE__ */ Ce(n[0]) ? (n[0] = /* @__PURE__ */ _(n[0]), s[t](...n)) : r;
}
function le(e, t, n = []) {
  me(), ft();
  const s = (/* @__PURE__ */ _(e))[t].apply(e, n);
  return pt(), ye(), s;
}
const Kn = /* @__PURE__ */ bn("__proto__,__v_isRef,__isVue"), zt = new Set(
  /* @__PURE__ */ Object.getOwnPropertyNames(Symbol).filter((e) => e !== "arguments" && e !== "caller").map((e) => Symbol[e]).filter(Z)
);
function Un(e) {
  Z(e) || (e = String(e));
  const t = /* @__PURE__ */ _(this);
  return O(t, "has", e), t.hasOwnProperty(e);
}
class Kt {
  constructor(t = !1, n = !1) {
    this._isReadonly = t, this._isShallow = n;
  }
  get(t, n, s) {
    if (n === "__v_skip") return t.__v_skip;
    const r = this._isReadonly, o = this._isShallow;
    if (n === "__v_isReactive")
      return !r;
    if (n === "__v_isReadonly")
      return r;
    if (n === "__v_isShallow")
      return o;
    if (n === "__v_raw")
      return s === (r ? o ? Yt : Jt : o ? tr : Bt).get(t) || // receiver is not the reactive proxy, but has the same prototype
      // this means the receiver is a user proxy of the reactive proxy
      Object.getPrototypeOf(t) === Object.getPrototypeOf(s) ? t : void 0;
    const i = y(t);
    if (!r) {
      let c;
      if (i && (c = Ln[n]))
        return c;
      if (n === "hasOwnProperty")
        return Un;
    }
    const a = Reflect.get(
      t,
      n,
      // if this is a proxy wrapping a ref, return methods using the raw ref
      // as receiver so that we don't have to call `toRaw` on the ref in all
      // its class methods
      /* @__PURE__ */ x(t) ? t : s
    );
    if ((Z(n) ? zt.has(n) : Kn(n)) || (r || O(t, "get", n), o))
      return a;
    if (/* @__PURE__ */ x(a)) {
      const c = i && at(n) ? a : a.value;
      return r && b(c) ? /* @__PURE__ */ tt(c) : c;
    }
    return b(a) ? r ? /* @__PURE__ */ tt(a) : /* @__PURE__ */ qt(a) : a;
  }
}
class Bn extends Kt {
  constructor(t = !1) {
    super(!1, t);
  }
  set(t, n, s, r) {
    let o = t[n];
    const i = y(t) && at(n);
    if (!this._isShallow) {
      const u = /* @__PURE__ */ M(o);
      if (!/* @__PURE__ */ S(s) && !/* @__PURE__ */ M(s) && (o = /* @__PURE__ */ _(o), s = /* @__PURE__ */ _(s)), !i && /* @__PURE__ */ x(o) && !/* @__PURE__ */ x(s))
        return u ? (process.env.NODE_ENV !== "production" && W(
          `Set operation on key "${String(n)}" failed: target is readonly.`,
          t[n]
        ), !0) : (o.value = s, !0);
    }
    const a = i ? Number(n) < t.length : De(t, n), c = Reflect.set(
      t,
      n,
      s,
      /* @__PURE__ */ x(t) ? t : r
    );
    return t === /* @__PURE__ */ _(r) && c && (a ? j(s, o) && K(t, "set", n, s, o) : K(t, "add", n, s)), c;
  }
  deleteProperty(t, n) {
    const s = De(t, n), r = t[n], o = Reflect.deleteProperty(t, n);
    return o && s && K(t, "delete", n, void 0, r), o;
  }
  has(t, n) {
    const s = Reflect.has(t, n);
    return (!Z(n) || !zt.has(n)) && O(t, "has", n), s;
  }
  ownKeys(t) {
    return O(
      t,
      "iterate",
      y(t) ? "length" : G
    ), Reflect.ownKeys(t);
  }
}
class Ut extends Kt {
  constructor(t = !1) {
    super(!0, t);
  }
  set(t, n) {
    return process.env.NODE_ENV !== "production" && W(
      `Set operation on key "${String(n)}" failed: target is readonly.`,
      t
    ), !0;
  }
  deleteProperty(t, n) {
    return process.env.NODE_ENV !== "production" && W(
      `Delete operation on key "${String(n)}" failed: target is readonly.`,
      t
    ), !0;
  }
}
const Jn = /* @__PURE__ */ new Bn(), Yn = /* @__PURE__ */ new Ut(), qn = /* @__PURE__ */ new Ut(!0), et = (e) => e, be = (e) => Reflect.getPrototypeOf(e);
function Gn(e, t, n) {
  return function(...s) {
    const r = this.__v_raw, o = /* @__PURE__ */ _(r), i = q(o), a = e === "entries" || e === Symbol.iterator && i, c = e === "keys" && i, u = r[e](...s), p = n ? et : t ? ie : L;
    return !t && O(
      o,
      "iterate",
      c ? Xe : G
    ), D(
      // inheriting all iterator properties
      Object.create(u),
      {
        // iterator protocol
        next() {
          const { value: l, done: f } = u.next();
          return f ? { value: l, done: f } : {
            value: a ? [p(l[0]), p(l[1])] : p(l),
            done: f
          };
        }
      }
    );
  };
}
function Ne(e) {
  return function(...t) {
    if (process.env.NODE_ENV !== "production") {
      const n = t[0] ? `on key "${t[0]}" ` : "";
      W(
        `${Re(e)} operation ${n}failed: target is readonly.`,
        /* @__PURE__ */ _(this)
      );
    }
    return e === "delete" ? !1 : e === "clear" ? void 0 : this;
  };
}
function Qn(e, t) {
  const n = {
    get(r) {
      const o = this.__v_raw, i = /* @__PURE__ */ _(o), a = /* @__PURE__ */ _(r);
      e || (j(r, a) && O(i, "get", r), O(i, "get", a));
      const { has: c } = be(i), u = t ? et : e ? ie : L;
      if (c.call(i, r))
        return u(o.get(r));
      if (c.call(i, a))
        return u(o.get(a));
      o !== i && o.get(r);
    },
    get size() {
      const r = this.__v_raw;
      return !e && O(/* @__PURE__ */ _(r), "iterate", G), r.size;
    },
    has(r) {
      const o = this.__v_raw, i = /* @__PURE__ */ _(o), a = /* @__PURE__ */ _(r);
      return e || (j(r, a) && O(i, "has", r), O(i, "has", a)), r === a ? o.has(r) : o.has(r) || o.has(a);
    },
    forEach(r, o) {
      const i = this, a = i.__v_raw, c = /* @__PURE__ */ _(a), u = t ? et : e ? ie : L;
      return !e && O(c, "iterate", G), a.forEach((p, l) => r.call(o, u(p), u(l), i));
    }
  };
  return D(
    n,
    e ? {
      add: Ne("add"),
      set: Ne("set"),
      delete: Ne("delete"),
      clear: Ne("clear")
    } : {
      add(r) {
        const o = /* @__PURE__ */ _(this), i = be(o), a = /* @__PURE__ */ _(r), c = !t && !/* @__PURE__ */ S(r) && !/* @__PURE__ */ M(r) ? a : r;
        return i.has.call(o, c) || j(r, c) && i.has.call(o, r) || j(a, c) && i.has.call(o, a) || (o.add(c), K(o, "add", c, c)), this;
      },
      set(r, o) {
        !t && !/* @__PURE__ */ S(o) && !/* @__PURE__ */ M(o) && (o = /* @__PURE__ */ _(o));
        const i = /* @__PURE__ */ _(this), { has: a, get: c } = be(i);
        let u = a.call(i, r);
        u ? process.env.NODE_ENV !== "production" && Nt(i, a, r) : (r = /* @__PURE__ */ _(r), u = a.call(i, r));
        const p = c.call(i, r);
        return i.set(r, o), u ? j(o, p) && K(i, "set", r, o, p) : K(i, "add", r, o), this;
      },
      delete(r) {
        const o = /* @__PURE__ */ _(this), { has: i, get: a } = be(o);
        let c = i.call(o, r);
        c ? process.env.NODE_ENV !== "production" && Nt(o, i, r) : (r = /* @__PURE__ */ _(r), c = i.call(o, r));
        const u = a ? a.call(o, r) : void 0, p = o.delete(r);
        return c && K(o, "delete", r, void 0, u), p;
      },
      clear() {
        const r = /* @__PURE__ */ _(this), o = r.size !== 0, i = process.env.NODE_ENV !== "production" ? q(r) ? new Map(r) : new Set(r) : void 0, a = r.clear();
        return o && K(
          r,
          "clear",
          void 0,
          void 0,
          i
        ), a;
      }
    }
  ), [
    "keys",
    "values",
    "entries",
    Symbol.iterator
  ].forEach((r) => {
    n[r] = Gn(r, e, t);
  }), n;
}
function ht(e, t) {
  const n = Qn(e, t);
  return (s, r, o) => r === "__v_isReactive" ? !e : r === "__v_isReadonly" ? e : r === "__v_raw" ? s : Reflect.get(
    De(n, r) && r in s ? n : s,
    r,
    o
  );
}
const Zn = {
  get: /* @__PURE__ */ ht(!1, !1)
}, Xn = {
  get: /* @__PURE__ */ ht(!0, !1)
}, er = {
  get: /* @__PURE__ */ ht(!0, !0)
};
function Nt(e, t, n) {
  const s = /* @__PURE__ */ _(n);
  if (s !== n && t.call(e, s)) {
    const r = Pt(e);
    W(
      `Reactive ${r} contains both the raw and reactive versions of the same object${r === "Map" ? " as keys" : ""}, which can lead to inconsistencies. Avoid differentiating between the raw and reactive versions of an object and only use the reactive version if possible.`
    );
  }
}
const Bt = /* @__PURE__ */ new WeakMap(), tr = /* @__PURE__ */ new WeakMap(), Jt = /* @__PURE__ */ new WeakMap(), Yt = /* @__PURE__ */ new WeakMap();
function nr(e) {
  switch (e) {
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
function qt(e) {
  return /* @__PURE__ */ M(e) ? e : gt(
    e,
    !1,
    Jn,
    Zn,
    Bt
  );
}
// @__NO_SIDE_EFFECTS__
function tt(e) {
  return gt(
    e,
    !0,
    Yn,
    Xn,
    Jt
  );
}
// @__NO_SIDE_EFFECTS__
function Oe(e) {
  return gt(
    e,
    !0,
    qn,
    er,
    Yt
  );
}
function gt(e, t, n, s, r) {
  if (!b(e))
    return process.env.NODE_ENV !== "production" && W(
      `value cannot be made ${t ? "readonly" : "reactive"}: ${String(
        e
      )}`
    ), e;
  if (e.__v_raw && !(t && e.__v_isReactive) || e.__v_skip || !Object.isExtensible(e))
    return e;
  const o = r.get(e);
  if (o)
    return o;
  const i = nr(Pt(e));
  if (i === 0)
    return e;
  const a = new Proxy(
    e,
    i === 2 ? s : n
  );
  return r.set(e, a), a;
}
// @__NO_SIDE_EFFECTS__
function B(e) {
  return /* @__PURE__ */ M(e) ? /* @__PURE__ */ B(e.__v_raw) : !!(e && e.__v_isReactive);
}
// @__NO_SIDE_EFFECTS__
function M(e) {
  return !!(e && e.__v_isReadonly);
}
// @__NO_SIDE_EFFECTS__
function S(e) {
  return !!(e && e.__v_isShallow);
}
// @__NO_SIDE_EFFECTS__
function Ce(e) {
  return e ? !!e.__v_raw : !1;
}
// @__NO_SIDE_EFFECTS__
function _(e) {
  const t = e && e.__v_raw;
  return t ? /* @__PURE__ */ _(t) : e;
}
function rr(e) {
  return !De(e, "__v_skip") && Object.isExtensible(e) && Tn(e, "__v_skip", !0), e;
}
const L = (e) => b(e) ? /* @__PURE__ */ qt(e) : e, ie = (e) => b(e) ? /* @__PURE__ */ tt(e) : e;
// @__NO_SIDE_EFFECTS__
function x(e) {
  return e ? e.__v_isRef === !0 : !1;
}
function sr(e) {
  return /* @__PURE__ */ x(e) ? e.value : e;
}
const or = {
  get: (e, t, n) => t === "__v_raw" ? e : sr(Reflect.get(e, t, n)),
  set: (e, t, n, s) => {
    const r = e[t];
    return /* @__PURE__ */ x(r) && !/* @__PURE__ */ x(n) ? (r.value = n, !0) : Reflect.set(e, t, n, s);
  }
};
function ir(e) {
  return /* @__PURE__ */ B(e) ? e : new Proxy(e, or);
}
const Se = {}, Ie = /* @__PURE__ */ new WeakMap();
let Y;
function ar(e, t = !1, n = Y) {
  if (n) {
    let s = Ie.get(n);
    s || Ie.set(n, s = []), s.push(e);
  } else process.env.NODE_ENV !== "production" && !t && W(
    "onWatcherCleanup() was called when there was no active watcher to associate with."
  );
}
function cr(e, t, n = oe) {
  const { immediate: s, deep: r, once: o, scheduler: i, augmentJob: a, call: c } = n, u = (g) => {
    (n.onWarn || W)(
      "Invalid watch source: ",
      g,
      "A watch source can only be a getter/effect function, a ref, a reactive object, or an array of these types."
    );
  }, p = (g) => r ? g : /* @__PURE__ */ S(g) || r === !1 || r === 0 ? H(g, 1) : H(g);
  let l, f, d, w, C = !1, ve = !1;
  if (/* @__PURE__ */ x(e) ? (f = () => e.value, C = /* @__PURE__ */ S(e)) : /* @__PURE__ */ B(e) ? (f = () => p(e), C = !0) : y(e) ? (ve = !0, C = e.some((g) => /* @__PURE__ */ B(g) || /* @__PURE__ */ S(g)), f = () => e.map((g) => {
    if (/* @__PURE__ */ x(g))
      return g.value;
    if (/* @__PURE__ */ B(g))
      return p(g);
    if (E(g))
      return c ? c(g, 2) : g();
    process.env.NODE_ENV !== "production" && u(g);
  })) : E(e) ? t ? f = c ? () => c(e, 2) : e : f = () => {
    if (d) {
      me();
      try {
        d();
      } finally {
        ye();
      }
    }
    const g = Y;
    Y = l;
    try {
      return c ? c(e, 3, [w]) : e(w);
    } finally {
      Y = g;
    }
  } : (f = ne, process.env.NODE_ENV !== "production" && u(e)), t && r) {
    const g = f, P = r === !0 ? 1 / 0 : r;
    f = () => H(g(), P);
  }
  const X = () => {
    l.stop();
  };
  if (o && t) {
    const g = t;
    t = (...P) => {
      const ce = g(...P);
      return X(), ce;
    };
  }
  let J = ve ? new Array(e.length).fill(Se) : Se;
  const ae = (g) => {
    if (!(!(l.flags & 1) || !l.dirty && !g))
      if (t) {
        const P = l.run();
        if (g || r || C || (ve ? P.some((ce, Ee) => j(ce, J[Ee])) : j(P, J))) {
          d && d();
          const ce = Y;
          Y = l;
          try {
            const Ee = [
              P,
              // pass undefined as the old value when it's changed for the first time
              J === Se ? void 0 : ve && J[0] === Se ? [] : J,
              w
            ];
            J = P, c ? c(t, 3, Ee) : (
              // @ts-expect-error
              t(...Ee)
            );
          } finally {
            Y = ce;
          }
        }
      } else
        l.run();
  };
  return a && a(ae), l = new Mn(f), l.scheduler = i ? () => i(ae, !1) : ae, w = (g) => ar(g, !1, l), d = l.onStop = () => {
    const g = Ie.get(l);
    if (g) {
      if (c)
        c(g, 4);
      else
        for (const P of g) P();
      Ie.delete(l);
    }
  }, process.env.NODE_ENV !== "production" && (l.onTrack = n.onTrack, l.onTrigger = n.onTrigger), t ? s ? ae(!0) : J = l.run() : i ? i(ae.bind(null, !0), !0) : l.run(), X.pause = l.pause.bind(l), X.resume = l.resume.bind(l), X.stop = X, X;
}
function H(e, t = 1 / 0, n) {
  if (t <= 0 || !b(e) || e.__v_skip || (n = n || /* @__PURE__ */ new Map(), (n.get(e) || 0) >= t))
    return e;
  if (n.set(e, t), t--, /* @__PURE__ */ x(e))
    H(e.value, t, n);
  else if (y(e))
    for (let s = 0; s < e.length; s++)
      H(e[s], t, n);
  else if (It(e) || q(e))
    e.forEach((s) => {
      H(s, t, n);
    });
  else if (At(e)) {
    for (const s in e)
      H(e[s], t, n);
    for (const s of Object.getOwnPropertySymbols(e))
      Object.prototype.propertyIsEnumerable.call(e, s) && H(e[s], t, n);
  }
  return e;
}
/**
* @vue/runtime-core v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
const Q = [];
function lr(e) {
  Q.push(e);
}
function ur() {
  Q.pop();
}
let Je = !1;
function v(e, ...t) {
  if (Je) return;
  Je = !0, me();
  const n = Q.length ? Q[Q.length - 1].component : null, s = n && n.appContext.config.warnHandler, r = fr();
  if (s)
    Le(
      s,
      n,
      11,
      [
        // eslint-disable-next-line no-restricted-syntax
        e + t.map((o) => {
          var i, a;
          return (a = (i = o.toString) == null ? void 0 : i.call(o)) != null ? a : JSON.stringify(o);
        }).join(""),
        n && n.proxy,
        r.map(
          ({ vnode: o }) => `at <${vn(n, o.type)}>`
        ).join(`
`),
        r
      ]
    );
  else {
    const o = [`[Vue warn]: ${e}`, ...t];
    r.length && o.push(`
`, ...pr(r)), console.warn(...o);
  }
  ye(), Je = !1;
}
function fr() {
  let e = Q[Q.length - 1];
  if (!e)
    return [];
  const t = [];
  for (; e; ) {
    const n = t[0];
    n && n.vnode === e ? n.recurseCount++ : t.push({
      vnode: e,
      recurseCount: 0
    });
    const s = e.component && e.component.parent;
    e = s && s.vnode;
  }
  return t;
}
function pr(e) {
  const t = [];
  return e.forEach((n, s) => {
    t.push(...s === 0 ? [] : [`
`], ...dr(n));
  }), t;
}
function dr({ vnode: e, recurseCount: t }) {
  const n = t > 0 ? `... (${t} recursive calls)` : "", s = e.component ? e.component.parent == null : !1, r = ` at <${vn(
    e.component,
    e.type,
    s
  )}`, o = ">" + n;
  return e.props ? [r, ...hr(e.props), o] : [r + o];
}
function hr(e) {
  const t = [], n = Object.keys(e);
  return n.slice(0, 3).forEach((s) => {
    t.push(...Gt(s, e[s]));
  }), n.length > 3 && t.push(" ..."), t;
}
function Gt(e, t, n) {
  return T(t) ? (t = JSON.stringify(t), n ? t : [`${e}=${t}`]) : typeof t == "number" || typeof t == "boolean" || t == null ? n ? t : [`${e}=${t}`] : /* @__PURE__ */ x(t) ? (t = Gt(e, /* @__PURE__ */ _(t.value), !0), n ? t : [`${e}=Ref<`, t, ">"]) : E(t) ? [`${e}=fn${t.name ? `<${t.name}>` : ""}`] : (t = /* @__PURE__ */ _(t), n ? t : [`${e}=`, t]);
}
const Qt = {
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
function Le(e, t, n, s) {
  try {
    return s ? e(...s) : e();
  } catch (r) {
    _t(r, t, n);
  }
}
function Zt(e, t, n, s) {
  if (E(e)) {
    const r = Le(e, t, n, s);
    return r && Dn(r) && r.catch((o) => {
      _t(o, t, n);
    }), r;
  }
  if (y(e)) {
    const r = [];
    for (let o = 0; o < e.length; o++)
      r.push(Zt(e[o], t, n, s));
    return r;
  } else process.env.NODE_ENV !== "production" && v(
    `Invalid value type passed to callWithAsyncErrorHandling(): ${typeof e}`
  );
}
function _t(e, t, n, s = !0) {
  const r = t ? t.vnode : null, { errorHandler: o, throwUnhandledErrorInProduction: i } = t && t.appContext.config || oe;
  if (t) {
    let a = t.parent;
    const c = t.proxy, u = process.env.NODE_ENV !== "production" ? Qt[n] : `https://vuejs.org/error-reference/#runtime-${n}`;
    for (; a; ) {
      const p = a.ec;
      if (p) {
        for (let l = 0; l < p.length; l++)
          if (p[l](e, c, u) === !1)
            return;
      }
      a = a.parent;
    }
    if (o) {
      me(), Le(o, null, 10, [
        e,
        c,
        u
      ]), ye();
      return;
    }
  }
  gr(e, n, r, s, i);
}
function gr(e, t, n, s = !0, r = !1) {
  if (process.env.NODE_ENV !== "production") {
    const o = Qt[t];
    if (n && lr(n), v(`Unhandled error${o ? ` during execution of ${o}` : ""}`), n && ur(), s)
      throw e;
    console.error(e);
  } else {
    if (r)
      throw e;
    console.error(e);
  }
}
const I = [];
let F = -1;
const re = [];
let z = null, te = 0;
const Xt = /* @__PURE__ */ Promise.resolve();
let $e = null;
const _r = 100;
function mr(e) {
  const t = $e || Xt;
  return e ? t.then(this ? e.bind(this) : e) : t;
}
function yr(e) {
  let t = F + 1, n = I.length;
  for (; t < n; ) {
    const s = t + n >>> 1, r = I[s], o = ge(r);
    o < e || o === e && r.flags & 2 ? t = s + 1 : n = s;
  }
  return t;
}
function mt(e) {
  if (!(e.flags & 1)) {
    const t = ge(e), n = I[I.length - 1];
    !n || // fast path when the job id is larger than the tail
    !(e.flags & 2) && t >= ge(n) ? I.push(e) : I.splice(yr(t), 0, e), e.flags |= 1, en();
  }
}
function en() {
  $e || ($e = Xt.then(nn));
}
function tn(e) {
  y(e) ? re.push(...e) : z && e.id === -1 ? z.splice(te + 1, 0, e) : e.flags & 1 || (re.push(e), e.flags |= 1), en();
}
function wr(e) {
  if (re.length) {
    const t = [...new Set(re)].sort(
      (n, s) => ge(n) - ge(s)
    );
    if (re.length = 0, z) {
      z.push(...t);
      return;
    }
    for (z = t, process.env.NODE_ENV !== "production" && (e = e || /* @__PURE__ */ new Map()), te = 0; te < z.length; te++) {
      const n = z[te];
      process.env.NODE_ENV !== "production" && rn(e, n) || (n.flags & 4 && (n.flags &= -2), n.flags & 8 || n(), n.flags &= -2);
    }
    z = null, te = 0;
  }
}
const ge = (e) => e.id == null ? e.flags & 2 ? -1 : 1 / 0 : e.id;
function nn(e) {
  process.env.NODE_ENV !== "production" && (e = e || /* @__PURE__ */ new Map());
  const t = process.env.NODE_ENV !== "production" ? (n) => rn(e, n) : ne;
  try {
    for (F = 0; F < I.length; F++) {
      const n = I[F];
      if (n && !(n.flags & 8)) {
        if (process.env.NODE_ENV !== "production" && t(n))
          continue;
        n.flags & 4 && (n.flags &= -2), Le(
          n,
          n.i,
          n.i ? 15 : 14
        ), n.flags & 4 || (n.flags &= -2);
      }
    }
  } finally {
    for (; F < I.length; F++) {
      const n = I[F];
      n && (n.flags &= -2);
    }
    F = -1, I.length = 0, wr(e), $e = null, (I.length || re.length) && nn(e);
  }
}
function rn(e, t) {
  const n = e.get(t) || 0;
  if (n > _r) {
    const s = t.i, r = s && wt(s.type);
    return _t(
      `Maximum recursive updates exceeded${r ? ` in component <${r}>` : ""}. This means you have a reactive effect that is mutating its own dependencies and thus recursively triggering itself. Possible sources include component template, render function, updated hook or watcher source function.`,
      null,
      10
    ), !0;
  }
  return e.set(t, n + 1), !1;
}
const Ye = /* @__PURE__ */ new Map();
process.env.NODE_ENV !== "production" && (He().__VUE_HMR_RUNTIME__ = {
  createRecord: qe(vr),
  rerender: qe(Er),
  reload: qe(br)
});
const Pe = /* @__PURE__ */ new Map();
function vr(e, t) {
  return Pe.has(e) ? !1 : (Pe.set(e, {
    initialDef: Ae(t),
    instances: /* @__PURE__ */ new Set()
  }), !0);
}
function Ae(e) {
  return En(e) ? e.__vccOpts : e;
}
function Er(e, t) {
  const n = Pe.get(e);
  n && (n.initialDef.render = t, [...n.instances].forEach((s) => {
    t && (s.render = t, Ae(s.type).render = t), s.renderCache = [], s.job.flags & 8 || s.update();
  }));
}
function br(e, t) {
  const n = Pe.get(e);
  if (!n) return;
  t = Ae(t), Ot(n.initialDef, t);
  const s = [...n.instances];
  for (let r = 0; r < s.length; r++) {
    const o = s[r], i = Ae(o.type);
    let a = Ye.get(i);
    a || (i !== n.initialDef && Ot(i, t), Ye.set(i, a = /* @__PURE__ */ new Set())), a.add(o), o.appContext.propsCache.delete(o.type), o.appContext.emitsCache.delete(o.type), o.appContext.optionsCache.delete(o.type), o.ceReload ? (a.add(o), o.ceReload(t.styles), a.delete(o)) : o.parent ? mt(() => {
      o.job.flags & 8 || (o.parent.update(), a.delete(o));
    }) : o.appContext.reload ? o.appContext.reload() : typeof window < "u" ? window.location.reload() : console.warn(
      "[HMR] Root or manually mounted instance modified. Full reload required."
    ), o.root.ce && o !== o.root && o.root.ce._removeChildStyle(i);
  }
  tn(() => {
    Ye.clear();
  });
}
function Ot(e, t) {
  D(e, t);
  for (const n in e)
    n !== "__file" && !(n in t) && delete e[n];
}
function qe(e) {
  return (t, n) => {
    try {
      return e(t, n);
    } catch (s) {
      console.error(s), console.warn(
        "[HMR] Something went wrong during Vue component hot-reload. Full reload required."
      );
    }
  };
}
let U, ue = [], nt = !1;
function Nr(e, ...t) {
  U ? U.emit(e, ...t) : nt || ue.push({ event: e, args: t });
}
function sn(e, t) {
  var n, s;
  U = e, U ? (U.enabled = !0, ue.forEach(({ event: r, args: o }) => U.emit(r, ...o)), ue = []) : /* handle late devtools injection - only do this if we are in an actual */ /* browser environment to avoid the timer handle stalling test runner exit */ /* (#4815) */ typeof window < "u" && // some envs mock window but not fully
  window.HTMLElement && // also exclude jsdom
  // eslint-disable-next-line no-restricted-syntax
  !((s = (n = window.navigator) == null ? void 0 : n.userAgent) != null && s.includes("jsdom")) ? ((t.__VUE_DEVTOOLS_HOOK_REPLAY__ = t.__VUE_DEVTOOLS_HOOK_REPLAY__ || []).push((o) => {
    sn(o, t);
  }), setTimeout(() => {
    U || (t.__VUE_DEVTOOLS_HOOK_REPLAY__ = null, nt = !0, ue = []);
  }, 3e3)) : (nt = !0, ue = []);
}
const Or = /* @__PURE__ */ Sr(
  "component:updated"
  /* COMPONENT_UPDATED */
);
// @__NO_SIDE_EFFECTS__
function Sr(e) {
  return (t) => {
    Nr(
      e,
      t.appContext.app,
      t.uid,
      t.parent ? t.parent.uid : void 0,
      t
    );
  };
}
let V = null, on = null;
function St(e) {
  const t = V;
  return V = e, on = e && e.type.__scopeId || null, t;
}
function cs(e, t = V, n) {
  if (!t || e._n)
    return e;
  const s = (...r) => {
    s._d && Ct(-1);
    const o = St(t), i = se.length;
    let a;
    try {
      a = e(...r);
    } finally {
      for (let c = se.length; c > i; c--) dn();
      St(o), s._d && Ct(1);
    }
    return process.env.NODE_ENV !== "production" && Or(t), a;
  };
  return s._n = !0, s._c = !0, s._d = !0, s;
}
function ls(e, t) {
  if (V === null)
    return process.env.NODE_ENV !== "production" && v("withDirectives can only be used inside render functions."), e;
  const n = wn(V), s = e.dirs || (e.dirs = []);
  for (let r = 0; r < t.length; r++) {
    let [o, i, a, c = oe] = t[r];
    o && (E(o) && (o = {
      mounted: o,
      updated: o
    }), o.deep && H(i), s.push({
      dir: o,
      instance: n,
      value: i,
      oldValue: void 0,
      arg: a,
      modifiers: c
    }));
  }
  return e;
}
function xr(e, t, n = !1) {
  const s = Qr();
  if (s || Fr) {
    let r = s ? s.parent == null || s.ce ? s.vnode.appContext && s.vnode.appContext.provides : s.parent.provides : void 0;
    if (r && e in r)
      return r[e];
    if (arguments.length > 1)
      return n && E(t) ? t.call(s && s.proxy) : t;
    process.env.NODE_ENV !== "production" && v(`injection "${String(e)}" not found.`);
  } else process.env.NODE_ENV !== "production" && v("inject() can only be used inside setup() or functional components.");
}
const Dr = /* @__PURE__ */ Symbol.for("v-scx"), Vr = () => {
  {
    const e = xr(Dr);
    return e || process.env.NODE_ENV !== "production" && v(
      "Server rendering context not provided. Make sure to only call useSSRContext() conditionally in the server build."
    ), e;
  }
};
function Rr(e, t, n = oe) {
  const { immediate: s, deep: r, flush: o, once: i } = n;
  process.env.NODE_ENV !== "production" && !t && (s !== void 0 && v(
    'watch() "immediate" option is only respected when using the watch(source, callback, options?) signature.'
  ), r !== void 0 && v(
    'watch() "deep" option is only respected when using the watch(source, callback, options?) signature.'
  ), i !== void 0 && v(
    'watch() "once" option is only respected when using the watch(source, callback, options?) signature.'
  ));
  const a = D({}, n);
  process.env.NODE_ENV !== "production" && (a.onWarn = v);
  const c = t && s || !t && o !== "post";
  let u;
  if (it) {
    if (o === "sync") {
      const d = Vr();
      u = d.__watcherHandles || (d.__watcherHandles = []);
    } else if (!c) {
      const d = () => {
      };
      return d.stop = ne, d.resume = ne, d.pause = ne, d;
    }
  }
  const p = we;
  a.call = (d, w, C) => Zt(d, p, w, C);
  let l = !1;
  o === "post" ? a.scheduler = (d) => {
    Hr(d, p && p.suspense);
  } : o !== "sync" && (l = !0, a.scheduler = (d, w) => {
    w ? d() : mt(d);
  }), a.augmentJob = (d) => {
    t && (d.flags |= 4), l && (d.flags |= 2, p && (d.id = p.uid, d.i = p));
  };
  const f = cr(e, t, a);
  return it && (u ? u.push(f) : c && f()), f;
}
function Tr(e, t, n) {
  const s = this.proxy, r = T(e) ? e.includes(".") ? Cr(s, e) : () => s[e] : e.bind(s, s);
  let o;
  E(t) ? o = t : (o = t.handler, n = t);
  const i = Zr(this), a = Rr(r, o.bind(s), n);
  return i(), a;
}
function Cr(e, t) {
  const n = t.split(".");
  return () => {
    let s = e;
    for (let r = 0; r < n.length && s; r++)
      s = s[n[r]];
    return s;
  };
}
const Ir = (e) => e.__isTeleport;
function an(e, t) {
  e.shapeFlag & 6 && e.component ? (e.transition = t, an(e.component.subTree, t)) : e.shapeFlag & 128 ? (e.ssContent.transition = t.clone(e.ssContent), e.ssFallback.transition = t.clone(e.ssFallback)) : e.transition = t;
}
He().requestIdleCallback;
He().cancelIdleCallback;
const cn = "components";
function us(e, t) {
  return un(cn, e, !0, t) || e;
}
const ln = /* @__PURE__ */ Symbol.for("v-ndc");
function fs(e) {
  return T(e) ? un(cn, e, !1) || e : e || ln;
}
function un(e, t, n = !0, s = !1) {
  const r = V || we;
  if (r) {
    const o = r.type;
    {
      const a = wt(
        o,
        !1
      );
      if (a && (a === t || a === Ve(t) || a === Re(Ve(t))))
        return o;
    }
    const i = (
      // local registration
      // check instance[type] first which is resolved for options API
      xt(r[e] || o[e], t) || // global registration
      xt(r.appContext[e], t)
    );
    return !i && s ? o : (process.env.NODE_ENV !== "production" && n && !i && v(`Failed to resolve ${e.slice(0, -1)}: ${t}
If this is a native custom element, make sure to exclude it from component resolution via compilerOptions.isCustomElement.`), i);
  } else process.env.NODE_ENV !== "production" && v(
    `resolve${Re(e.slice(0, -1))} can only be used in render() or setup().`
  );
}
function xt(e, t) {
  return e && (e[t] || e[Ve(t)] || e[Re(Ve(t))]);
}
function ps(e, t, n, s) {
  let r;
  const o = n, i = y(e);
  if (i || T(e)) {
    const a = i && /* @__PURE__ */ B(e);
    let c = !1, u = !1;
    a && (c = !/* @__PURE__ */ S(e), u = /* @__PURE__ */ M(e), e = We(e)), r = new Array(e.length);
    for (let p = 0, l = e.length; p < l; p++)
      r[p] = t(
        c ? u ? ie(L(e[p])) : L(e[p]) : e[p],
        p,
        void 0,
        o
      );
  } else if (typeof e == "number")
    if (process.env.NODE_ENV !== "production" && (!Number.isInteger(e) || e < 0))
      v(
        `The v-for range expects a positive integer value but got ${e}.`
      ), r = [];
    else {
      r = new Array(e);
      for (let a = 0; a < e; a++)
        r[a] = t(a + 1, a, void 0, o);
    }
  else if (b(e))
    if (e[Symbol.iterator])
      r = Array.from(
        e,
        (a, c) => t(a, c, void 0, o)
      );
    else {
      const a = Object.keys(e);
      r = new Array(a.length);
      for (let c = 0, u = a.length; c < u; c++) {
        const p = a[c];
        r[c] = t(e[p], p, c, o);
      }
    }
  else
    r = [];
  return r;
}
const rt = (e) => e ? Xr(e) ? wn(e) : rt(e.parent) : null, Ge = (
  // Move PURE marker to new line to workaround compiler discarding it
  // due to type annotation
  /* @__PURE__ */ D(/* @__PURE__ */ Object.create(null), {
    $: (e) => e,
    $el: (e) => e.vnode.el,
    $data: (e) => e.data,
    $props: (e) => process.env.NODE_ENV !== "production" ? /* @__PURE__ */ Oe(e.props) : e.props,
    $attrs: (e) => process.env.NODE_ENV !== "production" ? /* @__PURE__ */ Oe(e.attrs) : e.attrs,
    $slots: (e) => process.env.NODE_ENV !== "production" ? /* @__PURE__ */ Oe(e.slots) : e.slots,
    $refs: (e) => process.env.NODE_ENV !== "production" ? /* @__PURE__ */ Oe(e.refs) : e.refs,
    $parent: (e) => rt(e.parent),
    $root: (e) => rt(e.root),
    $host: (e) => e.ce,
    $emit: (e) => e.emit,
    $options: (e) => Pr(e),
    $forceUpdate: (e) => e.f || (e.f = () => {
      mt(e.update);
    }),
    $nextTick: (e) => e.n || (e.n = mr.bind(e.proxy)),
    $watch: (e) => Tr.bind(e)
  })
), $r = {};
process.env.NODE_ENV !== "production" && ($r.ownKeys = (e) => (v(
  "Avoid app logic that relies on enumerating keys on a component instance. The keys will be empty in production mode to avoid performance overhead."
), Reflect.ownKeys(e)));
function Dt(e) {
  return y(e) ? e.reduce(
    (t, n) => (t[n] = null, t),
    {}
  ) : e;
}
function Pr(e) {
  const t = e.type, { mixins: n, extends: s } = t, {
    mixins: r,
    optionsCache: o,
    config: { optionMergeStrategies: i }
  } = e.appContext, a = o.get(t);
  let c;
  return a ? c = a : !r.length && !n && !s ? c = t : (c = {}, r.length && r.forEach(
    (u) => Me(c, u, i, !0)
  ), Me(c, t, i)), b(t) && o.set(t, c), c;
}
function Me(e, t, n, s = !1) {
  const { mixins: r, extends: o } = t;
  o && Me(e, o, n, !0), r && r.forEach(
    (i) => Me(e, i, n, !0)
  );
  for (const i in t)
    if (s && i === "expose")
      process.env.NODE_ENV !== "production" && v(
        '"expose" option is ignored when declared in mixins or extends. It should only be declared in the base component itself.'
      );
    else {
      const a = Ar[i] || n && n[i];
      e[i] = a ? a(e[i], t[i]) : t[i];
    }
  return e;
}
const Ar = {
  data: Vt,
  props: Tt,
  emits: Tt,
  // objects
  methods: fe,
  computed: fe,
  // lifecycle
  beforeCreate: N,
  created: N,
  beforeMount: N,
  mounted: N,
  beforeUpdate: N,
  updated: N,
  beforeDestroy: N,
  beforeUnmount: N,
  destroyed: N,
  unmounted: N,
  activated: N,
  deactivated: N,
  errorCaptured: N,
  serverPrefetch: N,
  // assets
  components: fe,
  directives: fe,
  // watch
  watch: kr,
  // provide / inject
  provide: Vt,
  inject: Mr
};
function Vt(e, t) {
  return t ? e ? function() {
    return D(
      E(e) ? e.call(this, this) : e,
      E(t) ? t.call(this, this) : t
    );
  } : t : e;
}
function Mr(e, t) {
  return fe(Rt(e), Rt(t));
}
function Rt(e) {
  if (y(e)) {
    const t = {};
    for (let n = 0; n < e.length; n++)
      t[e[n]] = e[n];
    return t;
  }
  return e;
}
function N(e, t) {
  return e ? [...new Set([].concat(e, t))] : t;
}
function fe(e, t) {
  return e ? D(/* @__PURE__ */ Object.create(null), e, t) : t;
}
function Tt(e, t) {
  return e ? y(e) && y(t) ? [.../* @__PURE__ */ new Set([...e, ...t])] : D(
    /* @__PURE__ */ Object.create(null),
    Dt(e),
    Dt(t ?? {})
  ) : t;
}
function kr(e, t) {
  if (!e) return t;
  if (!t) return e;
  const n = D(/* @__PURE__ */ Object.create(null), e);
  for (const s in t)
    n[s] = N(e[s], t[s]);
  return n;
}
let Fr = null;
const jr = {}, fn = (e) => Object.getPrototypeOf(e) === jr, Hr = Lr, Wr = (e) => e.__isSuspense;
function Lr(e, t) {
  t && t.pendingBranch ? y(e) ? t.effects.push(...e) : t.effects.push(e) : tn(e);
}
const pn = /* @__PURE__ */ Symbol.for("v-fgt"), zr = /* @__PURE__ */ Symbol.for("v-txt"), st = /* @__PURE__ */ Symbol.for("v-cmt"), se = [];
let R = null;
function Kr(e = !1) {
  se.push(R = e ? null : []);
}
function dn() {
  se.pop(), R = se[se.length - 1] || null;
}
let _e = 1;
function Ct(e, t = !1) {
  _e += e, e < 0 && R && t && (R.hasOnce = !0);
}
function hn(e) {
  return e.dynamicChildren = _e > 0 ? R || Nn : null, dn(), _e > 0 && R && R.push(e), e;
}
function ds(e, t, n, s, r, o) {
  return hn(
    _n(
      e,
      t,
      n,
      s,
      r,
      o,
      !0
    )
  );
}
function Ur(e, t, n, s, r) {
  return hn(
    yt(
      e,
      t,
      n,
      s,
      r,
      !0
    )
  );
}
function Br(e) {
  return e ? e.__v_isVNode === !0 : !1;
}
const Jr = (...e) => mn(
  ...e
), gn = ({ key: e }) => e ?? null, xe = ({
  ref: e,
  ref_key: t,
  ref_for: n
}) => (typeof e == "number" && (e = "" + e), e != null ? T(e) || /* @__PURE__ */ x(e) || E(e) ? { i: V, r: e, k: t, f: !!n } : e : null);
function _n(e, t = null, n = null, s = 0, r = null, o = e === pn ? 0 : 1, i = !1, a = !1) {
  const c = {
    __v_isVNode: !0,
    __v_skip: !0,
    type: e,
    props: t,
    key: t && gn(t),
    ref: t && xe(t),
    scopeId: on,
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
    ctx: V
  };
  return a ? (Fe(c, n), o & 128 && e.normalize(c)) : n && (c.shapeFlag |= T(n) ? 8 : 16), process.env.NODE_ENV !== "production" && c.key !== c.key && v("VNode created with invalid key (NaN). VNode type:", c.type), _e > 0 && // avoid a block node from tracking itself
  !i && // has current parent block
  R && // presence of a patch flag indicates this node needs patching on updates.
  // component nodes also should always be patched, because even if the
  // component doesn't need to update, it needs to persist the instance on to
  // the next vnode so that it can be properly unmounted later.
  (c.patchFlag > 0 || o & 6) && // the EVENTS flag is only for hydration and if it is the only flag, the
  // vnode should not be considered dynamic due to handler caching.
  c.patchFlag !== 32 && R.push(c), c;
}
const yt = process.env.NODE_ENV !== "production" ? Jr : mn;
function mn(e, t = null, n = null, s = 0, r = null, o = !1) {
  if ((!e || e === ln) && (process.env.NODE_ENV !== "production" && !e && v(`Invalid vnode type when creating vnode: ${e}.`), e = st), Br(e)) {
    const a = ke(
      e,
      t,
      !0
      /* mergeRef: true */
    );
    return n && Fe(a, n), _e > 0 && !o && R && (a.shapeFlag & 6 ? R[R.indexOf(e)] = a : R.push(a)), a.patchFlag = -2, a;
  }
  if (En(e) && (e = e.__vccOpts), t) {
    t = Yr(t);
    let { class: a, style: c } = t;
    a && !T(a) && (t.class = ut(a)), b(c) && (/* @__PURE__ */ Ce(c) && !y(c) && (c = D({}, c)), t.style = lt(c));
  }
  const i = T(e) ? 1 : Wr(e) ? 128 : Ir(e) ? 64 : b(e) ? 4 : E(e) ? 2 : 0;
  return process.env.NODE_ENV !== "production" && i & 4 && /* @__PURE__ */ Ce(e) && (e = /* @__PURE__ */ _(e), v(
    "Vue received a Component that was made a reactive object. This can lead to unnecessary performance overhead and should be avoided by marking the component with `markRaw` or using `shallowRef` instead of `ref`.",
    `
Component that was made reactive: `,
    e
  )), _n(
    e,
    t,
    n,
    s,
    r,
    i,
    o,
    !0
  );
}
function Yr(e) {
  return e ? /* @__PURE__ */ Ce(e) || fn(e) ? D({}, e) : e : null;
}
function ke(e, t, n = !1, s = !1) {
  const { props: r, ref: o, patchFlag: i, children: a, transition: c } = e, u = t ? Gr(r || {}, t) : r, p = {
    __v_isVNode: !0,
    __v_skip: !0,
    type: e.type,
    props: u,
    key: u && gn(u),
    ref: t && t.ref ? (
      // #2078 in the case of <component :is="vnode" ref="extra"/>
      // if the vnode itself already has a ref, cloneVNode will need to merge
      // the refs so the single vnode can be set on multiple refs
      n && o ? y(o) ? o.concat(xe(t)) : [o, xe(t)] : xe(t)
    ) : o,
    scopeId: e.scopeId,
    slotScopeIds: e.slotScopeIds,
    children: process.env.NODE_ENV !== "production" && i === -1 && y(a) ? a.map(yn) : a,
    target: e.target,
    targetStart: e.targetStart,
    targetAnchor: e.targetAnchor,
    staticCount: e.staticCount,
    shapeFlag: e.shapeFlag,
    // if the vnode is cloned with extra props, we can no longer assume its
    // existing patch flag to be reliable and need to add the FULL_PROPS flag.
    // note: preserve flag for fragments since they use the flag for children
    // fast paths only.
    patchFlag: t && e.type !== pn ? i === -1 ? 16 : i | 16 : i,
    dynamicProps: e.dynamicProps,
    dynamicChildren: e.dynamicChildren,
    appContext: e.appContext,
    dirs: e.dirs,
    transition: c,
    // These should technically only be non-null on mounted VNodes. However,
    // they *should* be copied for kept-alive vnodes. So we just always copy
    // them since them being non-null during a mount doesn't affect the logic as
    // they will simply be overwritten.
    component: e.component,
    suspense: e.suspense,
    ssContent: e.ssContent && ke(e.ssContent),
    ssFallback: e.ssFallback && ke(e.ssFallback),
    placeholder: e.placeholder,
    el: e.el,
    anchor: e.anchor,
    ctx: e.ctx,
    ce: e.ce
  };
  return c && s && an(
    p,
    c.clone(p)
  ), p;
}
function yn(e) {
  const t = ke(e);
  return y(e.children) && (t.children = e.children.map(yn)), t;
}
function qr(e = " ", t = 0) {
  return yt(zr, null, e, t);
}
function hs(e = "", t = !1) {
  return t ? (Kr(), Ur(st, null, e)) : yt(st, null, e);
}
function Fe(e, t) {
  let n = 0;
  const { shapeFlag: s } = e;
  if (t == null)
    t = null;
  else if (y(t))
    n = 16;
  else if (typeof t == "object")
    if (s & 65) {
      const r = t.default;
      r && (r._c && (r._d = !1), Fe(e, r()), r._c && (r._d = !0));
      return;
    } else {
      n = 32;
      const r = t._;
      !r && !fn(t) ? t._ctx = V : r === 3 && V && (V.slots._ === 1 ? t._ = 1 : (t._ = 2, e.patchFlag |= 1024));
    }
  else if (E(t)) {
    if (s & 65) {
      Fe(e, { default: t });
      return;
    }
    t = { default: t, _ctx: V }, n = 32;
  } else
    t = String(t), s & 64 ? (n = 16, t = [qr(t)]) : n = 8;
  e.children = t, e.shapeFlag |= n;
}
function Gr(...e) {
  const t = {};
  for (let n = 0; n < e.length; n++) {
    const s = e[n];
    for (const r in s)
      if (r === "class")
        t.class !== s.class && (t.class = ut([t.class, s.class]));
      else if (r === "style")
        t.style = lt([t.style, s.style]);
      else if (On(r)) {
        const o = t[r], i = s[r];
        i && o !== i && !(y(o) && o.includes(i)) ? t[r] = o ? [].concat(o, i) : i : i == null && o == null && // mergeProps({ 'onUpdate:modelValue': undefined }) should not retain
        // the model listener.
        !Sn(r) && (t[r] = i);
      } else r !== "" && (t[r] = s[r]);
  }
  return t;
}
let we = null;
const Qr = () => we || V;
let ot;
{
  const e = He(), t = (n, s) => {
    let r;
    return (r = e[n]) || (r = e[n] = []), r.push(s), (o) => {
      r.length > 1 ? r.forEach((i) => i(o)) : r[0](o);
    };
  };
  ot = t(
    "__VUE_INSTANCE_SETTERS__",
    (n) => we = n
  ), t(
    "__VUE_SSR_SETTERS__",
    (n) => it = n
  );
}
const Zr = (e) => {
  const t = we;
  return ot(e), e.scope.on(), () => {
    e.scope.off(), ot(t);
  };
};
function Xr(e) {
  return e.vnode.shapeFlag & 4;
}
let it = !1;
process.env.NODE_ENV;
function wn(e) {
  return e.exposed ? e.exposeProxy || (e.exposeProxy = new Proxy(ir(rr(e.exposed)), {
    get(t, n) {
      if (n in t)
        return t[n];
      if (n in Ge)
        return Ge[n](e);
    },
    has(t, n) {
      return n in t || n in Ge;
    }
  })) : e.proxy;
}
const es = /(?:^|[-_])\w/g, ts = (e) => e.replace(es, (t) => t.toUpperCase()).replace(/[-_]/g, "");
function wt(e, t = !0) {
  return E(e) ? e.displayName || e.name : e.name || t && e.__name;
}
function vn(e, t, n = !1) {
  let s = wt(t);
  if (!s && t.__file) {
    const r = t.__file.match(/([^/\\]+)\.\w+$/);
    r && (s = r[1]);
  }
  if (!s && e) {
    const r = (o) => {
      for (const i in o)
        if (o[i] === t)
          return i;
    };
    s = r(e.components) || e.parent && r(
      e.parent.type.components
    ) || r(e.appContext.components);
  }
  return s ? ts(s) : n ? "App" : "Anonymous";
}
function En(e) {
  return E(e) && "__vccOpts" in e;
}
function ns() {
  if (process.env.NODE_ENV === "production" || typeof window > "u")
    return;
  const e = { style: "color:#3ba776" }, t = { style: "color:#1677ff" }, n = { style: "color:#f5222d" }, s = { style: "color:#eb2f96" }, r = {
    __vue_custom_formatter: !0,
    header(l) {
      if (!b(l))
        return null;
      if (l.__isVue)
        return ["div", e, "VueInstance"];
      if (/* @__PURE__ */ x(l)) {
        me();
        const f = l.value;
        return ye(), [
          "div",
          {},
          ["span", e, p(l)],
          "<",
          a(f),
          ">"
        ];
      } else {
        if (/* @__PURE__ */ B(l))
          return [
            "div",
            {},
            ["span", e, /* @__PURE__ */ S(l) ? "ShallowReactive" : "Reactive"],
            "<",
            a(l),
            `>${/* @__PURE__ */ M(l) ? " (readonly)" : ""}`
          ];
        if (/* @__PURE__ */ M(l))
          return [
            "div",
            {},
            ["span", e, /* @__PURE__ */ S(l) ? "ShallowReadonly" : "Readonly"],
            "<",
            a(l),
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
    const f = [];
    l.type.props && l.props && f.push(i("props", /* @__PURE__ */ _(l.props))), l.setupState !== oe && f.push(i("setup", l.setupState)), l.data !== oe && f.push(i("data", /* @__PURE__ */ _(l.data)));
    const d = c(l, "computed");
    d && f.push(i("computed", d));
    const w = c(l, "inject");
    return w && f.push(i("injected", w)), f.push([
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
    ]), f;
  }
  function i(l, f) {
    return f = D({}, f), Object.keys(f).length ? [
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
        ...Object.keys(f).map((d) => [
          "div",
          {},
          ["span", s, d + ": "],
          a(f[d], !1)
        ])
      ]
    ] : ["span", {}];
  }
  function a(l, f = !0) {
    return typeof l == "number" ? ["span", t, l] : typeof l == "string" ? ["span", n, JSON.stringify(l)] : typeof l == "boolean" ? ["span", s, l] : b(l) ? ["object", { object: f ? /* @__PURE__ */ _(l) : l }] : ["span", n, String(l)];
  }
  function c(l, f) {
    const d = l.type;
    if (E(d))
      return;
    const w = {};
    for (const C in l.ctx)
      u(d, C, f) && (w[C] = l.ctx[C]);
    return w;
  }
  function u(l, f, d) {
    const w = l[d];
    if (y(w) && w.includes(f) || b(w) && f in w || l.extends && u(l.extends, f, d) || l.mixins && l.mixins.some((C) => u(C, f, d)))
      return !0;
  }
  function p(l) {
    return /* @__PURE__ */ S(l) ? "ShallowRef" : l.effect ? "ComputedRef" : "Ref";
  }
  window.devtoolsFormatters ? window.devtoolsFormatters.push(r) : window.devtoolsFormatters = [r];
}
const gs = process.env.NODE_ENV !== "production" ? v : ne;
process.env.NODE_ENV;
process.env.NODE_ENV;
/**
* vue v3.5.40
* (c) 2018-present Yuxi (Evan) You and Vue contributors
* @license MIT
**/
function rs() {
  ns();
}
process.env.NODE_ENV !== "production" && rs();
const ss = window.__etamusic.axios, h = ss.create({ baseURL: "", timeout: 3e4 });
async function _s(e, t = 1, n = 20, s = "create_date", r = "desc", o = 0) {
  return (await h.get("/api/asmr/search", {
    params: { keyword: e, page: t, page_size: n, order_by: s, sort: r, subtitle: o }
  })).data;
}
async function ms(e = 1, t = 20, n = "create_date", s = "desc", r = 0) {
  return (await h.get("/api/asmr/works", {
    params: { page: e, page_size: t, order_by: n, sort: s, subtitle: r }
  })).data;
}
async function ys(e, t = 1, n = 20, s = "create_date", r = "desc", o = 0) {
  return (await h.get(`/api/asmr/tags/${e}/works`, {
    params: { page: t, page_size: n, order_by: s, sort: r, subtitle: o }
  })).data;
}
async function ws(e, t = 1, n = 20, s = "create_date", r = "desc", o = 0) {
  return (await h.get(`/api/asmr/vas/${e}/works`, {
    params: { page: t, page_size: n, order_by: s, sort: r, subtitle: o }
  })).data;
}
async function vs(e, t = 1, n = 20, s = "create_date", r = "desc", o = 0) {
  return (await h.get(`/api/asmr/circles/${e}/works`, {
    params: { page: t, page_size: n, order_by: s, sort: r, subtitle: o }
  })).data;
}
async function Es() {
  return (await h.get("/api/asmr/auth/status")).data;
}
async function bs(e, t) {
  return (await h.post("/api/asmr/auth/login", { name: e, password: t })).data;
}
async function Ns(e, t, n = null) {
  return (await h.post("/api/asmr/auth/register", {
    name: e,
    password: t,
    recommender_uuid: n
  })).data;
}
async function Os() {
  return (await h.post("/api/asmr/auth/logout")).data;
}
async function Ss(e = "create_date", t = "desc", n = 1, s = "") {
  return (await h.get("/api/asmr/reviews", {
    params: { order: e, sort: t, page: n, filter: s }
  })).data;
}
async function xs(e, t, n = "", s = "") {
  return (await h.put("/api/asmr/reviews", {
    work_id: e,
    rating: t,
    review_text: n,
    progress: s
  })).data;
}
async function Ds(e) {
  return (await h.delete("/api/asmr/reviews", { params: { work_id: e } })).data;
}
async function Vs(e = 1, t = 50, n = "") {
  return (await h.get("/api/asmr/playlists", {
    params: { page: e, page_size: t, filter_by: n }
  })).data;
}
async function Rs(e) {
  return (await h.delete(`/api/asmr/playlists/${e}`)).data;
}
async function Ts() {
  return (await h.get("/api/asmr/playlists/default")).data;
}
async function Cs(e) {
  return (await h.get(`/api/asmr/playlists/${e}`)).data;
}
async function Is(e, t = 1, n = 50) {
  return (await h.get(`/api/asmr/playlists/${e}/works`, {
    params: { page: t, page_size: n }
  })).data;
}
async function $s(e) {
  return (await h.get(`/api/asmr/works/${e}/in-playlists`)).data;
}
async function Ps(e, t = 0, n = "", s = []) {
  return (await h.post("/api/asmr/playlists", {
    name: e,
    privacy: t,
    description: n,
    works: s
  })).data;
}
async function As(e, t) {
  return (await h.post("/api/asmr/playlists/add", { id: e, works: t })).data;
}
async function Ms(e, t) {
  return (await h.post("/api/asmr/playlists/remove", { id: e, works: t })).data;
}
async function ks(e = 1, t = 20, n = "") {
  return (await h.get("/api/asmr/popular", {
    params: { page: e, page_size: t, keyword: n }
  })).data;
}
async function Fs(e = 1, t = 20, n = "") {
  return (await h.get("/api/asmr/recommendations", {
    params: { page: e, page_size: t, keyword: n }
  })).data;
}
async function js(e) {
  return (await h.get(`/api/asmr/works/${e}/neighbors`)).data;
}
async function Hs(e) {
  return (await h.get(`/api/asmr/works/${e}`)).data;
}
async function Ws(e) {
  return (await h.get(`/api/asmr/works/${e}/tracks`)).data;
}
function Ls(e, t = "main") {
  return `/api/asmr/cover/${e}?type=${t}`;
}
async function zs(e) {
  return (await h.get("/api/asmr/preview/text", { params: { url: e } })).data;
}
async function Ks() {
  return (await h.get("/api/asmr/target-nodes")).data;
}
async function Us(e) {
  return (await h.post("/api/asmr/downloads", e, { timeout: 6e4 })).data;
}
async function Bs(e) {
  return (await h.get("/api/asmr/downloads", { params: { status: e } })).data;
}
async function Js(e) {
  return (await h.get(`/api/asmr/downloads/${e}`)).data;
}
async function Ys(e) {
  return (await h.post(`/api/asmr/downloads/${e}/cancel`)).data;
}
async function qs(e) {
  await h.delete(`/api/asmr/downloads/${e}`);
}
async function Gs(e, t, n = "embed") {
  return (await h.post(`/api/asmr/downloads/${e}/apply-cover`, {
    cover_type: t,
    cover_mode: n
  }, { timeout: 12e4 })).data;
}
export {
  Fs as $,
  Ws as A,
  Ks as B,
  Ms as C,
  Ts as D,
  Ps as E,
  pn as F,
  As as G,
  zs as H,
  Us as I,
  xs as J,
  Ds as K,
  Bs as L,
  fs as M,
  Gs as N,
  Js as O,
  Ys as P,
  qs as Q,
  Vs as R,
  Is as S,
  Cs as T,
  Rs as U,
  os as V,
  as as W,
  y as X,
  is as Y,
  gs as Z,
  ks as _,
  _n as a,
  Os as a0,
  Ns as a1,
  bs as a2,
  Es as a3,
  yt as b,
  ds as c,
  qr as d,
  hs as e,
  Ur as f,
  ws as g,
  vs as h,
  x as i,
  ms as j,
  Ls as k,
  ys as l,
  us as m,
  ut as n,
  Kr as o,
  lt as p,
  js as q,
  ps as r,
  _s as s,
  An as t,
  sr as u,
  $s as v,
  cs as w,
  Ss as x,
  ls as y,
  Hs as z
};
