import { defineStore } from 'pinia'
import { computed } from 'vue'
import { useNodesStore } from './nodes'

/**
 * 认证状态（多节点聚合架构）
 *
 * 不再有"激活节点"概念。本 store 是 nodesStore 的派生视图：
 * - 本地节点（baseUrl === '/local_node'）的登录态决定 admin 路由访问权限
 * - 是否"已登录"= 本地节点已登录（admin 管理功能依赖本地节点）
 * - 库浏览/播放不依赖本 store，直接用 nodesStore.loggedInNodes
 *
 * 每个节点独立认证，token 存在 nodesStore.nodes 各节点对象上。
 */
export const useAuthStore = defineStore('auth', () => {
  const nodesStore = useNodesStore()

  // 本地节点对象（baseUrl === '/local_node'）
  const localNode = computed(() =>
    nodesStore.nodes.find((n) => n.baseUrl === '/local_node') || null
  )

  const token = computed(() => localNode.value?.token || '')
  const userInfo = computed(() => localNode.value?.userInfo || null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => !!userInfo.value?.is_admin)
  const username = computed(() => userInfo.value?.username || '')

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    username,
    localNode
  }
})
