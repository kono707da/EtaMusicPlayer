/**
 * 网易云 API 封装
 *
 * 不打包 axios，运行时从 window.__etamusic.axios 取用。
 * 所有端点前缀 /api/netease，由主应用后端转发。
 */
const axios = window.__etamusic.axios

const client = axios.create({ baseURL: '', timeout: 30000 })
const BASE = '/api/netease'

// ===== 错误处理 =====
function handleError(e, context = '') {
  const detail = e.response?.data?.detail || e.message || '未知错误'
  const msg = context ? `${context}: ${detail}` : detail
  throw new Error(msg)
}

// ===== 多账号管理 =====
export async function listAccounts() {
  try {
    const r = await client.get(`${BASE}/accounts`)
    return r.data
  } catch (e) { handleError(e, '获取账号列表失败') }
}

export async function switchAccount(ncmUid) {
  try {
    const r = await client.post(`${BASE}/accounts/switch`, null, { params: { ncm_uid: ncmUid } })
    return r.data
  } catch (e) { handleError(e, '切换账号失败') }
}

export async function deleteAccount(ncmUid) {
  try {
    const r = await client.delete(`${BASE}/accounts/${ncmUid}`)
    return r.data
  } catch (e) { handleError(e, '删除账号失败') }
}

// ===== 登录 =====
export async function getQrcodeKey() {
  try {
    const r = await client.get(`${BASE}/login/qrcode/key`)
    return r.data
  } catch (e) { handleError(e, '获取二维码 key 失败') }
}

export async function getQrcodeUrl(unikey) {
  try {
    const r = await client.get(`${BASE}/login/qrcode/url`, { params: { unikey } })
    return r.data
  } catch (e) { handleError(e, '获取二维码 URL 失败') }
}

export async function getQrcodeImage(unikey) {
  // 返回 SVG 图片 URL，直接用作 <img :src>
  return `${BASE}/login/qrcode/image?unikey=${encodeURIComponent(unikey)}&_t=${Date.now()}`
}

export async function pollQrcodeStatus(unikey) {
  try {
    const r = await client.get(`${BASE}/login/qrcode/poll`, { params: { unikey } })
    return r.data
  } catch (e) { handleError(e, '查询扫码状态失败') }
}

export async function getLoginStatus() {
  try {
    const r = await client.get(`${BASE}/login/status`)
    return r.data
  } catch (e) { handleError(e, '查询登录状态失败') }
}

export async function refreshLogin() {
  try {
    const r = await client.post(`${BASE}/login/refresh`)
    return r.data
  } catch (e) { handleError(e, '刷新登录状态失败') }
}

// ===== 搜索 =====
export async function search(keyword, type = 1, limit = 30, offset = 0) {
  try {
    const r = await client.get(`${BASE}/search`, { params: { keyword, type, limit, offset } })
    return r.data
  } catch (e) { handleError(e, '搜索失败') }
}

export async function searchHot() {
  try {
    const r = await client.get(`${BASE}/search/hot`)
    return r.data
  } catch (e) { handleError(e, '获取热搜失败') }
}

export async function searchSuggest(keywords) {
  try {
    const r = await client.get(`${BASE}/search/suggest`, { params: { keywords } })
    return r.data
  } catch (e) { handleError(e, '搜索建议失败') }
}

// ===== 歌曲 =====
export async function getSongDetail(ids) {
  try {
    const idsStr = Array.isArray(ids) ? ids.join(',') : String(ids)
    const r = await client.get(`${BASE}/song/detail`, { params: { ids: idsStr } })
    return r.data
  } catch (e) { handleError(e, '获取歌曲详情失败') }
}

export async function getSongUrl(ids, level = 'standard') {
  try {
    const idsStr = Array.isArray(ids) ? ids.join(',') : String(ids)
    const r = await client.get(`${BASE}/song/url`, { params: { ids: idsStr, level } })
    return r.data
  } catch (e) { handleError(e, '获取播放 URL 失败') }
}

export async function getSongLyric(id, isNew = false) {
  try {
    const r = await client.get(`${BASE}/song/lyric`, { params: { id, new: isNew } })
    return r.data
  } catch (e) { handleError(e, '获取歌词失败') }
}

// ===== 推荐 =====
export async function getPersonalized(limit = 30, offset = 0) {
  try {
    const r = await client.get(`${BASE}/recommend/personalized`, { params: { limit, offset } })
    return r.data
  } catch (e) { handleError(e, '获取推荐歌单失败') }
}

export async function getRecommendSongs() {
  try {
    const r = await client.get(`${BASE}/recommend/songs`)
    return r.data
  } catch (e) { handleError(e, '获取每日推荐失败') }
}

// ===== 排行榜 =====
export async function getToplist() {
  try {
    const r = await client.get(`${BASE}/toplist`)
    return r.data
  } catch (e) { handleError(e, '获取排行榜失败') }
}

// ===== 歌单 =====
export async function getPlaylistDetail(id) {
  try {
    const r = await client.get(`${BASE}/playlist/detail`, { params: { id } })
    return r.data
  } catch (e) { handleError(e, '获取歌单详情失败') }
}

export async function getPlaylistTrackAll(id, limit = 300, offset = 0) {
  try {
    const r = await client.get(`${BASE}/playlist/track/all`, { params: { id, limit, offset } })
    return r.data
  } catch (e) { handleError(e, '获取歌单曲目失败') }
}

export async function getMyPlaylists() {
  try {
    const r = await client.get(`${BASE}/user/self/playlists`)
    return r.data
  } catch (e) { handleError(e, '获取我的歌单失败') }
}

// ===== 工具函数 =====
/**
 * 把网易云歌曲对象转成 player store 可用的 track 对象
 * 带 __streamUrl 的曲目会被 player store 识别为外部源播放
 */
export async function buildPlayableTrack(song, level = 'standard') {
  const urlResp = await getSongUrl([song.id], level)
  const urlItem = urlResp?.data?.[0]
  if (!urlItem || !urlItem.url) {
    throw new Error(`歌曲「${song.name}」无可用播放 URL（可能需 VIP 或版权限制）`)
  }
  return {
    id: song.id,
    name: song.name,
    artist: (song.ar || []).map((a) => a.name).join(' / ') || '未知艺术家',
    album: song.al?.name || '',
    duration: Math.floor((song.dt || 0) / 1000),
    cover: song.al?.picUrl || '',
    __streamUrl: urlItem.url,
    __nodeName: '网易云',
    __source: 'netease'
  }
}

/**
 * 批量获取播放 URL 并构建 track 数组
 * 网易云 API 支持批量获取，减少请求数
 */
export async function buildPlayableTracks(songs, level = 'standard') {
  if (!songs || songs.length === 0) return []
  const ids = songs.map((s) => s.id)
  const urlResp = await getSongUrl(ids, level)
  const urlMap = new Map()
  for (const item of urlResp?.data || []) {
    if (item.url) urlMap.set(item.id, item.url)
  }
  return songs.map((song) => ({
    id: song.id,
    name: song.name,
    artist: (song.ar || []).map((a) => a.name).join(' / ') || '未知艺术家',
    album: song.al?.name || '',
    duration: Math.floor((song.dt || 0) / 1000),
    cover: song.al?.picUrl || '',
    __streamUrl: urlMap.get(song.id) || null,
    __nodeName: '网易云',
    __source: 'netease'
  })).filter((t) => t.__streamUrl)
}

// ===== 下载 =====
export async function downloadSongs(songIds, opts = {}) {
  try {
    const r = await client.post(`${BASE}/download/songs`, {
      song_ids: songIds,
      level: opts.level || 'exhigh',
      target_base_url: opts.target_base_url || 'local_node',
      target_watch_dir_id: opts.target_watch_dir_id || 1,
      target_subdir: opts.target_subdir || null
    }, { timeout: 30000 })
    return r.data
  } catch (e) { handleError(e, '创建下载任务失败') }
}

export async function downloadPlaylist(playlistId, opts = {}) {
  try {
    const r = await client.post(`${BASE}/download/playlist`, {
      playlist_id: playlistId,
      level: opts.level || 'exhigh',
      target_base_url: opts.target_base_url || 'local_node',
      target_watch_dir_id: opts.target_watch_dir_id || 1,
      target_subdir: opts.target_subdir || null,
      song_ids: opts.song_ids || null
    }, { timeout: 30000 })
    return r.data
  } catch (e) { handleError(e, '创建下载任务失败') }
}

export async function getDownloadTasks(params = {}) {
  try {
    const r = await client.get(`${BASE}/download/tasks`, { params })
    return r.data
  } catch (e) { handleError(e, '获取下载任务失败') }
}

export async function getDownloadTaskDetail(taskId) {
  try {
    const r = await client.get(`${BASE}/download/tasks/${taskId}`)
    return r.data
  } catch (e) { handleError(e, '获取任务详情失败') }
}

export async function cancelDownloadTask(taskId) {
  try {
    const r = await client.post(`${BASE}/download/tasks/${taskId}/cancel`)
    return r.data
  } catch (e) { handleError(e, '取消任务失败') }
}
