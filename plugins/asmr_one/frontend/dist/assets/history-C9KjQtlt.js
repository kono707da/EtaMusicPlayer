const t = "asmr_one:recent_tags", d = "asmr_one:recent_vas", r = "asmr_one:recent_circles";
const u = [
  { id: 497, name: "ASMR" },
  { id: 496, name: "双声道/人头麦" },
  { id: 1576, name: "舔耳" },
  { id: 399, name: "治愈" },
  { id: 2415, name: "低语" },
  { id: 1627, name: "男性受" },
  { id: 1564, name: "女性主导" },
  { id: 876, name: "亲热/甜蜜" },
  { id: 1305, name: "自慰辅助" },
  { id: 2246, name: "催眠" },
  { id: 1282, name: "哦吼淫叫" },
  { id: 648, name: "内射/中出" },
  { id: 2342, name: "言语刺激" },
  { id: 2154, name: "乳头刺激" },
  { id: 2477, name: "手交" },
  { id: 2476, name: "乳交" },
  { id: 2241, name: "呻吟/喘息" },
  { id: 1566, name: "呼唤主人" },
  { id: 1293, name: "妹妹" },
  { id: 1291, name: "姐姐" },
  { id: 1288, name: "女仆" },
  { id: 2405, name: "魔法少女" },
  { id: 2150, name: "魅魔/淫魔" },
  { id: 1284, name: "人外娘/魔物娘" },
  { id: 2240, name: "双子" },
  { id: 1614, name: "反转世界" },
  { id: 1578, name: "连续高潮" },
  { id: 1322, name: "常识改变" },
  { id: 2422, name: "深喉口交" },
  { id: 2407, name: "吞精/食精" }
];
function a(n) {
  try {
    const e = localStorage.getItem(n);
    if (!e) return [];
    const i = JSON.parse(e);
    return Array.isArray(i) ? i : [];
  } catch {
    return [];
  }
}
function m(n, e) {
  try {
    localStorage.setItem(n, JSON.stringify(e.slice(0, 12)));
  } catch {
  }
}
function c(n, e, i = 12) {
  const s = n.filter((o) => o.id !== e.id);
  return [e, ...s].slice(0, i);
}
function E() {
  return a(t);
}
function f(n) {
  if (!n || !n.id) return;
  const e = c(a(t), { id: n.id, name: n.name });
  m(t, e);
}
function _() {
  return a(d);
}
function R(n) {
  if (!n || !n.id) return;
  const e = c(a(d), { id: n.id, name: n.name });
  m(d, e);
}
function T() {
  return a(r);
}
function C(n) {
  if (!n || !n.id) return;
  const e = c(a(r), { id: n.id, name: n.name });
  m(r, e);
}
export {
  u as P,
  _ as a,
  T as b,
  C as c,
  f as d,
  R as e,
  E as g
};
