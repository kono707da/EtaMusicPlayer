import axios from 'axios'

/**
 * 节点缓存 API
 * 调用访问端后端的 /api/cached-* 和 /api/library/refresh
 * 用于离线节点展示缓存数据（置灰），在线节点仍直调节点 API
 */

const client = axios.create({
  baseURL: '',
  timeout: 30000
})

// 触发所有在线节点的增量同步（进入工作台时调用）
export async function refreshLibrary() {
  const resp = await client.post('/api/library/refresh')
  return resp.data
}

// 读取节点曲库缓存
export async function getCachedTracks(params = {}) {
  const resp = await client.get('/api/cached-tracks', { params })
  return resp.data
}

// 读取节点播放列表缓存
export async function getCachedPlaylists(params = {}) {
  const resp = await client.get('/api/cached-playlists', { params })
  return resp.data
}

// 读取节点同步状态
export async function getSyncStates(params = {}) {
  const resp = await client.get('/api/node-sync-states', { params })
  return resp.data
}
