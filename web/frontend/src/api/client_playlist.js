import axios from 'axios'

/**
 * 客户端播放列表 API
 * 直接调用访问端 eta_web 的 /api/client-playlists，不依赖任何节点。
 * 客户端播放列表存储在 eta_web 后端 SQLite，可跨节点聚合曲目。
 */

const client = axios.create({
  baseURL: '',
  timeout: 15000
})

// ===== 播放列表 CRUD =====

// 列出所有客户端播放列表（含系统列表）
export async function listClientPlaylists() {
  const resp = await client.get('/api/client-playlists')
  return resp.data
}

// 创建客户端播放列表
export async function createClientPlaylist(name, description = '') {
  const resp = await client.post('/api/client-playlists', { name, description })
  return resp.data
}

// 更新播放列表信息（系统列表名称不可改）
export async function updateClientPlaylist(id, data) {
  const resp = await client.put(`/api/client-playlists/${id}`, data)
  return resp.data
}

// 删除播放列表（系统列表不可删）
export async function deleteClientPlaylist(id) {
  const resp = await client.delete(`/api/client-playlists/${id}`)
  return resp.data
}

// ===== 曲目管理 =====

// 获取播放列表曲目（按 position 排序）
export async function listClientPlaylistItems(id) {
  const resp = await client.get(`/api/client-playlists/${id}/items`)
  return resp.data
}

/**
 * 批量添加曲目到播放列表末尾
 * 已存在的（同 track_id + node_id）会跳过。
 * @param {Number} playlistId
 * @param {Array} items [{track_id, node_id, title, artist, album, duration}]
 */
export async function addClientPlaylistItems(playlistId, items) {
  const resp = await client.post(`/api/client-playlists/${playlistId}/items`, { items })
  return resp.data
}

// 批量移除曲目并重排顺序
export async function removeClientPlaylistItems(playlistId, itemIds) {
  const resp = await client.delete(`/api/client-playlists/${playlistId}/items`, {
    data: { item_ids: itemIds }
  })
  return resp.data
}

/**
 * 1.2.1：按 (node_id, track_id) 跨所有客户端播放列表删除条目
 * 在节点曲目删除任务完成后调用，清理全局引用。幂等。
 * @param {String} nodeId 客户端格式节点 ID（如 "remote-1"）
 * @param {Number} trackId 曲目 ID
 * @returns {Promise<Object>} { ok: true, removed: N }
 */
export async function removeClientPlaylistTrackReferences(nodeId, trackId) {
  const resp = await client.delete('/api/client-playlists/items/by-track', {
    data: { node_id: nodeId, track_id: trackId }
  })
  return resp.data
}

// 调整曲目顺序 { item_id, new_position }
export async function reorderClientPlaylistItem(playlistId, itemId, newPosition) {
  const resp = await client.put(`/api/client-playlists/${playlistId}/reorder`, {
    item_id: itemId,
    new_position: newPosition
  })
  return resp.data
}
