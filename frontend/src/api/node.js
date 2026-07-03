import axios from 'axios'
import { createNodeClient } from './client'

/**
 * 节点 API 封装
 * 所有方法均接受 node 配置对象，内部创建/复用 client
 * 路径与后端 routers/ 严格对齐
 */

// ============ 认证 ============

// 登录：返回 {access_token, token_type, user}
export async function login(node, payload) {
  // payload: {username, password}
  const resp = await axios.post(`${node.baseUrl}/api/auth/login`, payload)
  return resp.data
}

// 刷新 token
export async function refreshToken(node) {
  const client = createNodeClient(node)
  const resp = await client.post('/api/auth/refresh')
  return resp.data
}

// 当前用户信息
export async function getCurrentUser(node) {
  const client = createNodeClient(node)
  const resp = await client.get('/api/auth/me')
  return resp.data
}

// ============ 曲目 ============

// 获取曲目列表（分页 + 搜索 + 过滤）
// params: {page, size, q, playlist_id, artist, album}
export async function getTracks(node, params = {}) {
  const client = createNodeClient(node)
  const resp = await client.get('/api/tracks', { params })
  return resp.data
}

// 获取单首曲目
export async function getTrack(node, trackId) {
  const client = createNodeClient(node)
  const resp = await client.get(`/api/tracks/${trackId}`)
  return resp.data
}

/**
 * 构造流式播放 URL
 * 后端 /api/tracks/{id}/stream 支持 Range，token 通过 query 参数传递
 */
export function getStreamUrl(node, trackId) {
  if (!node || !node.baseUrl) return ''
  const base = node.baseUrl.replace(/\/$/, '')
  const token = node.token ? `?token=${encodeURIComponent(node.token)}` : ''
  return `${base}/api/tracks/${trackId}/stream${token}`
}

// 获取封面图 URL
export function getCoverUrl(node, trackId) {
  if (!node || !node.baseUrl) return ''
  const base = node.baseUrl.replace(/\/$/, '')
  const token = node.token ? `?token=${encodeURIComponent(node.token)}` : ''
  return `${base}/api/tracks/${trackId}/cover${token}`
}

// 获取歌词文本
export async function getLyrics(node, trackId) {
  const client = createNodeClient(node)
  const resp = await client.get(`/api/tracks/${trackId}/lyrics`)
  return resp.data
}

// ============ 播放列表 ============

// 当前用户可见的播放列表
export async function getPlaylists(node) {
  const client = createNodeClient(node)
  const resp = await client.get('/api/playlists')
  return resp.data
}

// 播放列表详情（含曲目 items）
export async function getPlaylistDetail(node, playlistId) {
  const client = createNodeClient(node)
  const resp = await client.get(`/api/playlists/${playlistId}`)
  return resp.data
}

// 创建播放列表
export async function createPlaylist(node, payload) {
  // payload: {name, description}
  const client = createNodeClient(node)
  const resp = await client.post('/api/playlists', payload)
  return resp.data
}

// 更新播放列表
export async function updatePlaylist(node, playlistId, payload) {
  // payload: {name?, description?}
  const client = createNodeClient(node)
  const resp = await client.put(`/api/playlists/${playlistId}`, payload)
  return resp.data
}

// 删除播放列表（系统列表禁止删除）
export async function deletePlaylist(node, playlistId) {
  const client = createNodeClient(node)
  const resp = await client.delete(`/api/playlists/${playlistId}`)
  return resp.data
}

// 向播放列表批量添加曲目
export async function addTracksToPlaylist(node, playlistId, trackIds) {
  const client = createNodeClient(node)
  const resp = await client.post(`/api/playlists/${playlistId}/tracks`, {
    track_ids: trackIds
  })
  return resp.data
}

// 从播放列表批量移除曲目
export async function removeTracksFromPlaylist(node, playlistId, trackIds) {
  const client = createNodeClient(node)
  const resp = await client.delete(`/api/playlists/${playlistId}/tracks`, {
    data: { track_ids: trackIds }
  })
  return resp.data
}

// 调整曲目顺序
export async function reorderPlaylistTrack(node, playlistId, trackId, newPosition) {
  const client = createNodeClient(node)
  const resp = await client.post(`/api/playlists/${playlistId}/reorder`, {
    track_id: trackId,
    new_position: newPosition
  })
  return resp.data
}

// ============ 监控目录（admin） ============

export async function getWatchDirs(node) {
  const client = createNodeClient(node)
  const resp = await client.get('/api/watch-dirs')
  return resp.data
}

// 浏览目录结构（用于路径选择器）
// path 为空字符串/null 时返回盘符列表
export async function browseDirectories(node, path = '') {
  const client = createNodeClient(node)
  const resp = await client.get('/api/watch-dirs/browse', {
    params: path ? { path } : {}
  })
  return resp.data
}

export async function addWatchDir(node, payload) {
  // payload: {path, recursive?, enabled?}
  const client = createNodeClient(node)
  const resp = await client.post('/api/watch-dirs', payload)
  return resp.data
}

export async function updateWatchDir(node, dirId, payload) {
  // payload: {recursive?, enabled?}
  const client = createNodeClient(node)
  const resp = await client.put(`/api/watch-dirs/${dirId}`, payload)
  return resp.data
}

export async function deleteWatchDir(node, dirId) {
  const client = createNodeClient(node)
  const resp = await client.delete(`/api/watch-dirs/${dirId}`)
  return resp.data
}

// ============ 扫描（admin） ============

// 触发扫描，返回 ScanTask
// payload: {watch_dir_id?}
export async function triggerScan(node, payload = {}) {
  const client = createNodeClient(node)
  const resp = await client.post('/api/scan', payload)
  return resp.data
}

// 查询扫描状态
export async function getScanStatus(node, taskId) {
  const client = createNodeClient(node)
  const resp = await client.get(`/api/scan/${taskId}`)
  return resp.data
}

// ============ 元数据批量编辑（admin） ============

// 看板预览
// payload: {track_ids: []}
export async function previewMetadata(node, trackIds) {
  const client = createNodeClient(node)
  const resp = await client.post('/api/metadata/preview', { track_ids: trackIds })
  return resp.data
}

// 批量改单字段
// payload: {track_ids: [], field, value}
export async function updateMetadataField(node, trackIds, field, value) {
  const client = createNodeClient(node)
  const resp = await client.post('/api/metadata/update-field', {
    track_ids: trackIds,
    field,
    value
  })
  return resp.data
}

// 重命名预览
// payload: {track_ids: [], template, exceptions: []}
export async function previewRename(node, trackIds, template, exceptions = []) {
  const client = createNodeClient(node)
  const resp = await client.post('/api/metadata/rename-preview', {
    track_ids: trackIds,
    template,
    exceptions
  })
  return resp.data
}

// 重命名执行
export async function executeRename(node, trackIds, template, exceptions = []) {
  const client = createNodeClient(node)
  const resp = await client.post('/api/metadata/rename-execute', {
    track_ids: trackIds,
    template,
    exceptions
  })
  return resp.data
}

// ============ 去重 ============

// 获取去重配置
export async function getDedupConfig(node) {
  const client = createNodeClient(node)
  const resp = await client.get('/api/dedup/config')
  return resp.data
}

// 更新去重配置（admin）
// payload: {fields?, duration_tolerance?, enabled?}
export async function updateDedupConfig(node, payload) {
  const client = createNodeClient(node)
  const resp = await client.put('/api/dedup/config', payload)
  return resp.data
}

// 立即检测，返回重复组
export async function detectDuplicates(node) {
  const client = createNodeClient(node)
  const resp = await client.post('/api/dedup/detect')
  return resp.data
}

// 上次检测结果（缓存）
export async function getDedupGroups(node) {
  const client = createNodeClient(node)
  const resp = await client.get('/api/dedup/groups')
  return resp.data
}

// ============ 音质升级 ============

// 检测某播放列表内的音质升级候选
export async function detectQualityUpgrades(node, playlistId) {
  const client = createNodeClient(node)
  const resp = await client.post(`/api/quality/upgrades/${playlistId}`)
  return resp.data
}

// 执行替换
// payload: {playlist_id, old_track_id, new_track_id}
export async function applyQualityReplace(node, playlistId, oldTrackId, newTrackId) {
  const client = createNodeClient(node)
  const resp = await client.post('/api/quality/replace', {
    playlist_id: playlistId,
    old_track_id: oldTrackId,
    new_track_id: newTrackId
  })
  return resp.data
}

// ============ 用户管理（admin） ============

export async function getUsers(node) {
  const client = createNodeClient(node)
  const resp = await client.get('/api/users')
  return resp.data
}

export async function createUser(node, payload) {
  // payload: {username, password, is_admin?}
  const client = createNodeClient(node)
  const resp = await client.post('/api/users', payload)
  return resp.data
}

export async function updateUser(node, userId, payload) {
  // payload: {password?, is_admin?, is_active?}
  const client = createNodeClient(node)
  const resp = await client.put(`/api/users/${userId}`, payload)
  return resp.data
}

export async function deleteUser(node, userId) {
  const client = createNodeClient(node)
  const resp = await client.delete(`/api/users/${userId}`)
  return resp.data
}

// ============ 播放列表授权（admin） ============

// 查询授权关系，可按 playlist_id 或 user_id 过滤
export async function getPermissions(node, params = {}) {
  // params: {playlist_id?, user_id?}
  const client = createNodeClient(node)
  const resp = await client.get('/api/permissions', { params })
  return resp.data
}

// 授权用户访问播放列表
export async function grantPermission(node, playlistId, userId) {
  const client = createNodeClient(node)
  const resp = await client.post('/api/permissions', {
    playlist_id: playlistId,
    user_id: userId
  })
  return resp.data
}

// 撤销授权（按权限记录 id）
export async function revokePermission(node, permissionId) {
  const client = createNodeClient(node)
  const resp = await client.delete(`/api/permissions/${permissionId}`)
  return resp.data
}

// 某用户被授权的播放列表
export async function getUserGrantedPlaylists(node, userId) {
  const client = createNodeClient(node)
  const resp = await client.get(`/api/users/${userId}/playlists`)
  return resp.data
}
