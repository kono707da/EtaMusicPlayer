import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getNodeVersion as apiGetNodeVersion } from '../api/node'
import { checkCompatibility, COMPAT_RESULT } from '../utils/version-check'
import {
  CLIENT_VERSION,
  CLIENT_API_VERSION,
  MIN_NODE_VERSION,
  CLIENT_FEATURES,
  REQUIRED_FEATURES,
  FEATURE_REGISTRY
} from '../config/version'

const STORAGE_KEY = 'etamusic_nodes'

/**
 * 节点列表管理
 * - 增删改查节点配置
 * - 持久化到 localStorage
 * - 节点登录/登出（登录后才会在工作台展示内容）
 * - 版本校验：登录前检查 node 版本与功能兼容性
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
   * 生成节点 id（简单递增，仅对数字 ID 计算）
   */
  function genId() {
    const maxId = nodes.value.reduce((m, n) => {
      return typeof n.id === 'number' ? Math.max(m, n.id) : m
    }, 0)
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
   * 添加节点
   * 如果传入 id（远程节点格式 remote-{id}）则保留，否则生成数字 id
   * 如果传入 token/userInfo（远程节点登录后同步）则保留
   */
  function addNode(node) {
    const newNode = {
      id: node.id != null ? node.id : genId(),
      name: node.name,
      baseUrl: (node.baseUrl || '').replace(/\/$/, ''),
      username: node.username || '',
      password: node.password || '',
      token: node.token || '',
      userInfo: node.userInfo || null,
      // 版本校验结果
      versionInfo: node.versionInfo || null,
      compatibility: node.compatibility || null
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

  /**
   * 对指定节点执行版本校验
   * 获取 node /api/version 并与客户端版本配置对比
   *
   * @param {string|number} id - 节点 ID
   * @returns {Promise<Object>} 校验结果
   *   { result, reason, versionInfo, missingFeatures, unsupportedFeatures }
   *   result: 'ok' | 'incompatible' | 'partial'
   */
  async function checkNodeVersion(id) {
    const node = nodes.value.find((n) => n.id === id)
    if (!node) throw new Error('节点不存在')

    let versionInfo
    try {
      versionInfo = await apiGetNodeVersion(node)
    } catch (e) {
      // 无法获取版本信息：可能是 node 版本过低（没有 /api/version），视为不兼容
      const compat = {
        result: COMPAT_RESULT.INCOMPATIBLE,
        reason: '无法获取版本信息，node 版本过低或不可达',
        versionInfo: null,
        missingFeatures: [],
        unsupportedFeatures: []
      }
      updateNode(id, { versionInfo: null, compatibility: compat })
      return compat
    }

    const compat = checkCompatibility(versionInfo, {
      clientVersion: CLIENT_VERSION,
      clientApiVersion: CLIENT_API_VERSION,
      minNodeVersion: MIN_NODE_VERSION,
      clientFeatures: CLIENT_FEATURES,
      requiredFeatures: REQUIRED_FEATURES,
      featureRegistry: FEATURE_REGISTRY
    })

    const result = {
      result: compat.result,
      reason: compat.reason,
      versionInfo,
      missingFeatures: compat.missingFeatures,
      unsupportedFeatures: compat.unsupportedFeatures
    }
    updateNode(id, { versionInfo, compatibility: result })
    return result
  }

  /**
   * 检查指定节点是否支持某功能
   * 未做过版本校验的节点默认视为支持（兼容旧逻辑）
   */
  function hasFeature(id, feature) {
    const node = nodes.value.find((n) => n.id === id)
    if (!node) return false
    if (!node.compatibility || !node.versionInfo) return true
    if (node.compatibility.result === COMPAT_RESULT.INCOMPATIBLE) return false
    return !node.compatibility.missingFeatures.includes(feature)
  }

  /**
   * 获取节点不支持的功能列表（含中文标签）
   * 返回 [{ feature, label, description }] 数组
   */
  function getMissingFeatures(id) {
    const node = nodes.value.find((n) => n.id === id)
    if (!node || !node.compatibility) return []
    return node.compatibility.missingFeatures
      .map((f) => ({
        feature: f,
        label: FEATURE_REGISTRY[f]?.label || f,
        description: FEATURE_REGISTRY[f]?.description || ''
      }))
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
    getNode,
    checkNodeVersion,
    hasFeature,
    getMissingFeatures
  }
})
