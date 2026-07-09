import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin } from '../api/node'

const STORAGE_KEY = 'etamusic_nodes'
const ACTIVE_KEY = 'etamusic_active_node'

/**
 * 节点列表管理
 * - 增删改查节点配置
 * - 持久化到 localStorage
 * - 维护当前激活节点
 * - 节点登录/登出（登录后才会在工作台展示内容）
 *
 * 应用是"客户端优先"：启动直接进工作台，
 * 节点是后配置的，登录某节点后其内容才填充进来。
 */
export const useNodesStore = defineStore('nodes', () => {
  const nodes = ref([])
  const activeNodeId = ref(null)
  // 登录事件计数器：每次有节点登录/登出时递增，供 library store 监听刷新
  const authVersion = ref(0)

  // 当前激活节点对象
  const activeNode = computed(
    () => nodes.value.find((n) => n.id === activeNodeId.value) || null
  )

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
      nodes.value = raw ? JSON.parse(raw) : []
      const savedActive = localStorage.getItem(ACTIVE_KEY)
      if (savedActive && nodes.value.some((n) => n.id === Number(savedActive))) {
        activeNodeId.value = Number(savedActive)
      } else if (nodes.value.length > 0) {
        // 默认激活第一个已登录节点，没有则激活第一个
        const firstLoggedIn = nodes.value.find((n) => n.token)
        activeNodeId.value = firstLoggedIn ? firstLoggedIn.id : nodes.value[0].id
      } else {
        activeNodeId.value = null
      }
    } catch (e) {
      nodes.value = []
      activeNodeId.value = null
    }
  }

  /**
   * 持久化节点列表到 localStorage
   */
  function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nodes.value))
    if (activeNodeId.value != null) {
      localStorage.setItem(ACTIVE_KEY, String(activeNodeId.value))
    } else {
      localStorage.removeItem(ACTIVE_KEY)
    }
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
    if (activeNodeId.value == null) {
      activeNodeId.value = newNode.id
    }
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
    if (activeNodeId.value === id) {
      const firstLoggedIn = nodes.value.find((n) => n.token)
      activeNodeId.value = firstLoggedIn ? firstLoggedIn.id : (nodes.value[0]?.id ?? null)
    }
    persist()
    authVersion.value++
  }

  /**
   * 设置当前激活节点
   */
  function setActive(id) {
    if (nodes.value.some((n) => n.id === id)) {
      activeNodeId.value = id
      persist()
    }
  }

  /**
   * 登录节点：用保存的账号密码调 /api/auth/login，拿 token/userInfo
   * 登录成功后自动设为激活节点，并递增 authVersion 触发曲库刷新
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
    // 设为激活节点
    activeNodeId.value = id
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
    // 如果登出的是激活节点，切到第一个已登录节点
    if (activeNodeId.value === id) {
      const firstLoggedIn = nodes.value.find((n) => n.token)
      activeNodeId.value = firstLoggedIn ? firstLoggedIn.id : (nodes.value[0]?.id ?? null)
    }
    authVersion.value++
  }

  /**
   * 节点是否已登录
   */
  function isLoggedIn(id) {
    const node = nodes.value.find((n) => n.id === id)
    return !!node?.token
  }

  // 初始化时加载
  load()

  return {
    nodes,
    activeNodeId,
    activeNode,
    authVersion,
    loggedInNodes,
    load,
    persist,
    addNode,
    updateNode,
    removeNode,
    setActive,
    loginNode,
    logoutNode,
    isLoggedIn
  }
})
