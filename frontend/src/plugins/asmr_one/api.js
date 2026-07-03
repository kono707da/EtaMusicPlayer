import axios from 'axios'

const client = axios.create({ baseURL: '', timeout: 30000 })

// ===== 设置 =====
export async function getSettings() {
  const r = await client.get('/api/asmr/settings')
  return r.data
}

export async function updateSettings(data) {
  const r = await client.put('/api/asmr/settings', data)
  return r.data
}

// ===== 搜索 / 作品 =====
export async function searchWorks(keyword, page = 1, pageSize = 20, orderBy = 'create_date', sort = 'desc', subtitle = 0) {
  const r = await client.get('/api/asmr/search', {
    params: { keyword, page, page_size: pageSize, order_by: orderBy, sort, subtitle }
  })
  return r.data
}

export async function listWorks(page = 1, pageSize = 20, orderBy = 'create_date', sort = 'desc', subtitle = 0) {
  const r = await client.get('/api/asmr/works', {
    params: { page, page_size: pageSize, order_by: orderBy, sort, subtitle }
  })
  return r.data
}

export async function listByTag(tagId, page = 1, pageSize = 20, orderBy = 'create_date', sort = 'desc', subtitle = 0) {
  const r = await client.get(`/api/asmr/tags/${tagId}/works`, {
    params: { page, page_size: pageSize, order_by: orderBy, sort, subtitle }
  })
  return r.data
}

export async function listByVa(vaId, page = 1, pageSize = 20, orderBy = 'create_date', sort = 'desc', subtitle = 0) {
  const r = await client.get(`/api/asmr/vas/${vaId}/works`, {
    params: { page, page_size: pageSize, order_by: orderBy, sort, subtitle }
  })
  return r.data
}

export async function listByCircle(circleId, page = 1, pageSize = 20, orderBy = 'create_date', sort = 'desc', subtitle = 0) {
  const r = await client.get(`/api/asmr/circles/${circleId}/works`, {
    params: { page, page_size: pageSize, order_by: orderBy, sort, subtitle }
  })
  return r.data
}

// ===== 作品额外信息 =====
export async function getWorkInfo(id) {
  const r = await client.get(`/api/asmr/works/${id}/info`)
  return r.data
}

// ===== 认证 =====
export async function getAuthStatus() {
  const r = await client.get('/api/asmr/auth/status')
  return r.data
}

export async function login(name, password) {
  const r = await client.post('/api/asmr/auth/login', { name, password })
  return r.data
}

export async function register(name, password, recommenderUuid = null) {
  const r = await client.post('/api/asmr/auth/register', {
    name,
    password,
    recommender_uuid: recommenderUuid
  })
  return r.data
}

export async function logout() {
  const r = await client.post('/api/asmr/auth/logout')
  return r.data
}

// ===== 评价 / 评分 =====
export async function listReviews(order = 'create_date', sort = 'desc', page = 1, filter = '') {
  const r = await client.get('/api/asmr/reviews', {
    params: { order, sort, page, filter }
  })
  return r.data
}

export async function upsertReview(workId, rating, reviewText = '', progress = '') {
  const r = await client.put('/api/asmr/reviews', {
    work_id: workId,
    rating,
    review_text: reviewText,
    progress
  })
  return r.data
}

export async function deleteReview(workId) {
  const r = await client.delete('/api/asmr/reviews', { params: { work_id: workId } })
  return r.data
}

// ===== 播放列表 / 收藏 =====
export async function listPlaylists(page = 1, pageSize = 50, filterBy = '') {
  const r = await client.get('/api/asmr/playlists', {
    params: { page, page_size: pageSize, filter_by: filterBy }
  })
  return r.data
}

export async function deletePlaylist(id) {
  const r = await client.delete(`/api/asmr/playlists/${id}`)
  return r.data
}

export async function getDefaultPlaylist() {
  const r = await client.get('/api/asmr/playlists/default')
  return r.data
}

export async function getPlaylistMetadata(id) {
  const r = await client.get(`/api/asmr/playlists/${id}`)
  return r.data
}

export async function getPlaylistWorks(id, page = 1, pageSize = 50) {
  const r = await client.get(`/api/asmr/playlists/${id}/works`, {
    params: { page, page_size: pageSize }
  })
  return r.data
}

export async function getWorkInPlaylists(workId) {
  const r = await client.get(`/api/asmr/works/${workId}/in-playlists`)
  return r.data
}

export async function createPlaylist(name, privacy = 0, description = '', works = []) {
  const r = await client.post('/api/asmr/playlists', {
    name,
    privacy,
    description,
    works
  })
  return r.data
}

export async function addToPlaylist(playlistId, works) {
  const r = await client.post('/api/asmr/playlists/add', { id: playlistId, works })
  return r.data
}

export async function removeFromPlaylist(playlistId, works) {
  const r = await client.post('/api/asmr/playlists/remove', { id: playlistId, works })
  return r.data
}

// ===== 推荐 =====
export async function getPopular(page = 1, pageSize = 20, keyword = '') {
  const r = await client.get('/api/asmr/popular', {
    params: { page, page_size: pageSize, keyword }
  })
  return r.data
}

export async function getRecommendations(page = 1, pageSize = 20, keyword = '') {
  const r = await client.get('/api/asmr/recommendations', {
    params: { page, page_size: pageSize, keyword }
  })
  return r.data
}

export async function getWorkNeighbors(workId) {
  const r = await client.get(`/api/asmr/works/${workId}/neighbors`)
  return r.data
}

export async function sendFeedback(type, recommenderUuid, itemId) {
  const r = await client.post('/api/asmr/feedback', {
    type,
    recommender_uuid: recommenderUuid,
    item_id: itemId
  })
  return r.data
}

// ===== 标签投票 =====
export async function voteWorkTag(workId, tagId, status) {
  const r = await client.post('/api/asmr/vote', {
    work_id: workId,
    tag_id: tagId,
    status
  })
  return r.data
}

export async function getWork(id) {
  const r = await client.get(`/api/asmr/works/${id}`)
  return r.data
}

export async function getWorkTracks(id) {
  const r = await client.get(`/api/asmr/works/${id}/tracks`)
  return r.data
}

export function coverUrl(id, type = 'main') {
  return `/api/asmr/cover/${id}?type=${type}`
}

// 预览文本文件（通过后端代理避免 CORS）
export async function previewText(url) {
  const r = await client.get('/api/asmr/preview/text', { params: { url } })
  return r.data
}

// ===== 目标节点 =====
export async function listTargetNodes() {
  const r = await client.get('/api/asmr/target-nodes')
  return r.data
}

// ===== 下载任务 =====
export async function createDownload(payload) {
  const r = await client.post('/api/asmr/downloads', payload, { timeout: 60000 })
  return r.data
}

export async function listDownloads(status) {
  const r = await client.get('/api/asmr/downloads', { params: { status } })
  return r.data
}

export async function getDownload(taskId) {
  const r = await client.get(`/api/asmr/downloads/${taskId}`)
  return r.data
}

export async function cancelDownload(taskId) {
  const r = await client.post(`/api/asmr/downloads/${taskId}/cancel`)
  return r.data
}

export async function deleteDownload(taskId) {
  await client.delete(`/api/asmr/downloads/${taskId}`)
}

export async function applyCover(taskId, coverType) {
  const r = await client.post(`/api/asmr/downloads/${taskId}/apply-cover`, {
    cover_type: coverType
  }, { timeout: 120000 })
  return r.data
}
