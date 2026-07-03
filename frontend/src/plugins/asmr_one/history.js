/**
 * asmr_one 浏览历史工具
 *
 * 由于 asmr.one 的 /api/tags /api/vas /api/circles 列表端点需要登录，
 * 我们无法在客户端列出所有可选标签/声优/社团。
 * 因此采用「最近访问」+「预设热门」混合策略：
 * - 预设一批常见标签 ID
 * - 用户在作品详情页点击 tag/va/circle 时，记录到 localStorage
 * - 下次浏览时显示「最近访问」快捷入口
 */

const KEY_RECENT_TAGS = 'asmr_one:recent_tags'
const KEY_RECENT_VAS = 'asmr_one:recent_vas'
const KEY_RECENT_CIRCLES = 'asmr_one:recent_circles'
const MAX_RECENT = 12

// 预设热门标签（ID 来自 asmr.one 实测，可扩展）
// 这些是从常见作品中提取的高频标签
export const PRESET_TAGS = [
  { id: 497, name: 'ASMR' },
  { id: 496, name: '双声道/人头麦' },
  { id: 1576, name: '舔耳' },
  { id: 399, name: '治愈' },
  { id: 2415, name: '低语' },
  { id: 1627, name: '男性受' },
  { id: 1564, name: '女性主导' },
  { id: 876, name: '亲热/甜蜜' },
  { id: 1305, name: '自慰辅助' },
  { id: 2246, name: '催眠' },
  { id: 1282, name: '哦吼淫叫' },
  { id: 648, name: '内射/中出' },
  { id: 2342, name: '言语刺激' },
  { id: 2154, name: '乳头刺激' },
  { id: 2477, name: '手交' },
  { id: 2476, name: '乳交' },
  { id: 2241, name: '呻吟/喘息' },
  { id: 1566, name: '呼唤主人' },
  { id: 1293, name: '妹妹' },
  { id: 1291, name: '姐姐' },
  { id: 1288, name: '女仆' },
  { id: 2405, name: '魔法少女' },
  { id: 2150, name: '魅魔/淫魔' },
  { id: 1284, name: '人外娘/魔物娘' },
  { id: 2240, name: '双子' },
  { id: 1614, name: '反转世界' },
  { id: 1578, name: '连续高潮' },
  { id: 1322, name: '常识改变' },
  { id: 2422, name: '深喉口交' },
  { id: 2407, name: '吞精/食精' }
]

function read(key) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

function write(key, arr) {
  try {
    localStorage.setItem(key, JSON.stringify(arr.slice(0, MAX_RECENT)))
  } catch {
    /* ignore */
  }
}

function pushUnique(arr, item, max = MAX_RECENT) {
  const filtered = arr.filter((x) => x.id !== item.id)
  return [item, ...filtered].slice(0, max)
}

export function getRecentTags() {
  return read(KEY_RECENT_TAGS)
}

export function addRecentTag(tag) {
  if (!tag || !tag.id) return
  const next = pushUnique(read(KEY_RECENT_TAGS), { id: tag.id, name: tag.name })
  write(KEY_RECENT_TAGS, next)
}

export function getRecentVas() {
  return read(KEY_RECENT_VAS)
}

export function addRecentVa(va) {
  if (!va || !va.id) return
  const next = pushUnique(read(KEY_RECENT_VAS), { id: va.id, name: va.name })
  write(KEY_RECENT_VAS, next)
}

export function getRecentCircles() {
  return read(KEY_RECENT_CIRCLES)
}

export function addRecentCircle(circle) {
  if (!circle || !circle.id) return
  const next = pushUnique(read(KEY_RECENT_CIRCLES), { id: circle.id, name: circle.name })
  write(KEY_RECENT_CIRCLES, next)
}
