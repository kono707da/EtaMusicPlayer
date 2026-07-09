import axios from 'axios'

/**
 * 插件管理 API
 * 直接调用访问端骨架的 /api/plugins，不依赖任何插件
 */

const client = axios.create({
  baseURL: '',
  timeout: 15000
})

// 列出所有插件
export async function listPlugins() {
  const resp = await client.get('/api/plugins')
  return resp.data
}

// 同步注册表（扫描文件系统）
export async function syncRegistry() {
  const resp = await client.post('/api/plugins/sync')
  return resp.data
}

// 启用插件
export async function enablePlugin(name) {
  const resp = await client.post(`/api/plugins/${name}/enable`)
  return resp.data
}

// 禁用插件
export async function disablePlugin(name) {
  const resp = await client.post(`/api/plugins/${name}/disable`)
  return resp.data
}

// 删除插件（文件 + 数据库记录）
export async function deletePlugin(name) {
  const resp = await client.delete(`/api/plugins/${name}`)
  return resp.data
}

// 触发服务器重启（用于应用插件变更）
export async function restartServer() {
  const resp = await client.post('/api/plugins/restart', null, { timeout: 5000 })
  return resp.data
}

// 分析待保存的变更是否需要重启服务器
// payload: { changes: { plugin_name: true/false, ... } }
export async function analyzeChanges(changes) {
  const resp = await client.post('/api/plugins/analyze-changes', { changes }, { timeout: 5000 })
  return resp.data
}

// 查询本地节点插件状态
export async function getLocalNodeStatus() {
  const resp = await client.get('/api/plugins/local-node/status', { timeout: 5000 })
  return resp.data
}

// ===== 在线插件注册表 =====

// 获取在线插件列表（合并本地安装状态）
export async function listOnlinePlugins() {
  const resp = await client.get('/api/plugins/online', { timeout: 30000 })
  return resp.data
}

// 检查在线注册表连接状态
export async function getOnlineRegistryStatus() {
  const resp = await client.get('/api/plugins/online/status', { timeout: 15000 })
  return resp.data
}

// 强制刷新在线注册表缓存
export async function refreshOnlineRegistry() {
  const resp = await client.post('/api/plugins/online/refresh', null, { timeout: 30000 })
  return resp.data
}

// 从在线注册表安装插件
export async function installOnlinePlugin(name) {
  const resp = await client.post(`/api/plugins/online/${name}/install`, null, { timeout: 120000 })
  return resp.data
}

// 从在线注册表更新插件
export async function updateOnlinePlugin(name) {
  const resp = await client.post(`/api/plugins/online/${name}/update`, null, { timeout: 120000 })
  return resp.data
}
