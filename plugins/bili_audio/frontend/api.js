const axios = window.__etamusic.axios

const client = axios.create({ baseURL: '', timeout: 30000 })

const BASE = '/api/bili'

export function parseVideo(url) {
  return client.post(`${BASE}/parse`, { url }).then(r => r.data)
}

export function createDownload(data) {
  return client.post(`${BASE}/downloads`, data).then(r => r.data)
}

export function listDownloads(page = 1, pageSize = 20) {
  return client.get(`${BASE}/downloads`, { params: { page, page_size: pageSize } }).then(r => r.data)
}

export function getDownload(taskId) {
  return client.get(`${BASE}/downloads/${taskId}`).then(r => r.data)
}

export function cancelDownload(taskId) {
  return client.post(`${BASE}/downloads/${taskId}/cancel`).then(r => r.data)
}

export function deleteDownload(taskId) {
  return client.delete(`${BASE}/downloads/${taskId}`).then(r => r.data)
}

export function getSettings() {
  return client.get(`${BASE}/settings`).then(r => r.data)
}

export function updateSettings(updates) {
  return client.put(`${BASE}/settings`, updates).then(r => r.data)
}

export function getTargetNodes() {
  return client.get(`${BASE}/target-nodes`).then(r => r.data)
}

export function createSubscription(data) {
  return client.post(`${BASE}/subscriptions`, data).then(r => r.data)
}

export function listSubscriptions() {
  return client.get(`${BASE}/subscriptions`).then(r => r.data)
}

export function getSubscription(subId) {
  return client.get(`${BASE}/subscriptions/${subId}`).then(r => r.data)
}

export function checkSubscription(subId) {
  return client.post(`${BASE}/subscriptions/${subId}/check`).then(r => r.data)
}

export function deleteSubscription(subId) {
  return client.delete(`${BASE}/subscriptions/${subId}`).then(r => r.data)
}

export function updateSubscription(subId, updates) {
  return client.put(`${BASE}/subscriptions/${subId}`, updates).then(r => r.data)
}
