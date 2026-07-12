import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin } from '../api/node'

const STORAGE_KEY = 'etamusic_nodes'

/**
 * 节点列表管理
 * - 增删改查节点配置
 * - 持久化到 localStorage
 * - 节点登录/登出（登录后才会在工作台展示内容）
 *
 * 多节点聚合架构：本应用是"客户端优先"的多节点聚合客户端，
 * 不存在"切换到某一节点"的概念。所有已登录节点的内容同时可用。
 * 每个节点独立认证，token 存在节点对象上。
 */
export const useNodesStore = defineStore('nodes', () => {
  const nodes = ref([])
  // 登录事件计数器：每次有节点登录/登出/删除时递增，供 library store 监听刷新
  const authVersion = ref(0)

  // 所有已登录（有 token）的节点
  const loggedInNodes = computed(() => nodes.value.filter((n) => !!n.token))

  /**
   * 生成节点 id（简单递增）
   */
  function genId() {
    const maxId = nodes.value.reduce((m, n) => Math.max(m, n.id), 0)
    return maxId + 1
  }

  /**
   * 从 localStorage 加载节点
   */
  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      const loaded = raw ? JSON.parse(raw) : []
      // 兼容旧版本：清除可能残留的 activeNodeId 字段
      nodes.value = loaded
      // 清除旧版本的 active node 持久化键（如果存在）
      localStorage.removeItem('etamusic_active_node')
    } catch (e) {
      nodes.value = []
    }
  }

  /**
   * 持久化节点列表到 localStorage
   */
  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nodes.value))
  }

  /**
   * 添加节点（仅保存配置，不自动登录）
   */
  function addNode(node) {
    const newNode = {
      id: genId(),
      name: node.name,
      baseUrl: (node.baseUrl || '').replace(/\/$/, ''),
      username: node.username || '',
      password: node.password || '',
      token: '',
      userInfo: null
    }
    nodes.value.push(newNode)
    persist()
    return newNode
  }

  /**
   * 更新节点配置（不改动 token，除非显式传入）
   */
  function updateNode(id, patch) {
    const idx = nodes.value.findIndex((n) => n.id === id)
    if (idx === -1) return null
    nodes.value[idx] = { ...nodes.value[idx], ...patch, id }
    persist()
    return nodes.value[idx]
  }

  /**
   * 删除节点
   */
  function removeNode(id) {
    const idx = nodes.value.findIndex((n) => n.id === id)
    if (idx === -1) return
    nodes.value.splice(idx, 1)
    persist()
    authVersion.value++
  }

  /**
   * 登录节点：用保存的账号密码调 /api/auth/login，拿 token/userInfo
   * 登录成功后递增 authVersion 触发曲库刷新
   * @returns {Promise<{token, userInfo}>}
   */
  async function loginNode(id) {
    const node = nodes.value.find((n) => n.id === id)
    if (!node) throw new Error('节点不存在')
    if (!node.username || !node.password) {
      throw new Error('该节点未保存账号密码，请先编辑节点补全')
    }
    const data = await apiLogin(node, {
      username: node.username,
      password: node.password
    })
    const token = data.access_token || data.token || ''
    const userInfo = data.user || data.userInfo || null
    if (!token) throw new Error('登录未返回 token')
    node.token = token
    node.userInfo = userInfo
    persist()
    // 触发曲库刷新
    authVersion.value++
    return { token, userInfo }
  }

  /**
   * 登出节点：清除该节点的 token/userInfo，不删除配置
   */
  function logoutNode(id) {
    const node = nodes.value.find((n) => n.id === id)
    if (!node) return
    node.token = ''
    node.userInfo = null
    persist()
    authVersion.value++
  }

  /**
   * 节点是否已登录
   */
  function isLoggedIn(id) {
    const node = nodes.value.find((n) => n.id === id)
    return !!node?.token
  }

  /**
   * 根据 id 获取节点对象
   */
  function getNode(id) {
    return nodes.value.find((n) => n.id === id) || null
  }

  // 初始化时加载
  load()

  return {
    nodes,
    authVersion,
    loggedInNodes,
    load,
    persist,
    addNode,
    updateNode,
    removeNode,
    loginNode,
    logoutNode,
    isLoggedIn,
    getNode
  }
})
