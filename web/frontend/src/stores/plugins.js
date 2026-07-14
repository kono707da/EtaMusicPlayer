import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { listPlugins, getLocalNodeStatus } from '../api/plugin'

/**
 * 插件状态 store
 * - 启动时从后端获取已启用插件列表
 * - 自动同步本地节点到 nodes store（插件启用即自动连接，无需手动登录）
 */
export const usePluginsStore = defineStore('plugins', () => {
  const plugins = ref([])
  const loaded = ref(false)
  const localNode = ref(null) // 本地节点状态

  const enabledNames = computed(() =>
    plugins.value.filter((p) => p.enabled).map((p) => p.name)
  )

  const hasNodePlugin = computed(() =>
    plugins.value.some((p) => p.enabled && p.loaded && p.name.includes('node'))
  )

  async function load() {
    try {
      plugins.value = await listPlugins()
    } catch (e) {
      plugins.value = []
      console.error('加载插件列表失败:', e)
    } finally {
      loaded.value = true
    }
  }

  async function refresh() {
    await load()
  }

  /**
   * 同步本地节点到 nodes store
   * - 插件可用且已加载：自动写入/更新本地节点记录（含 token）
   * - 插件不可用：清除 nodes store 中的本地节点记录
   * - 版本校验：不兼容时清除 token 不使用该节点；部分兼容时保留但记录缺失功能
   * 返回本地节点状态
   */
  async function syncLocalNode(nodesStore) {
    try {
      const status = await getLocalNodeStatus()
      localNode.value = status

      if (!status.available) {
        const existing = nodesStore.nodes.find((n) => n.baseUrl === '/local_node')
        if (existing) {
          nodesStore.removeNode(existing.id)
        }
        return status
      }

      const existing = nodesStore.nodes.find((n) => n.baseUrl === '/local_node')

      if (status.access_token) {
        const token = status.access_token
        const userInfo = status.user_info
        let nodeId
        if (existing) {
          nodeId = existing.id
          if (existing.token !== token) {
            nodesStore.updateNode(existing.id, { token, userInfo })
          }
        } else {
          const added = nodesStore.addNode({
            name: '本地节点',
            baseUrl: '/local_node',
            username: 'admin',
            password: 'admin123'
          })
          nodeId = added.id
          nodesStore.updateNode(added.id, { token, userInfo })
        }

        // 版本校验
        try {
          const compat = await nodesStore.checkNodeVersion(nodeId)
          if (compat.result === 'incompatible') {
            // 不兼容：清除 token，不使用本地节点
            nodesStore.updateNode(nodeId, { token: '', userInfo: null })
            console.warn(`本地节点版本不兼容：${compat.reason}`)
          }
        } catch (e) {
          // 版本校验失败，静默处理（保留 token，避免阻断旧版 node）
        }
      }

      return status
    } catch (e) {
      localNode.value = { available: false }
      return localNode.value
    }
  }

  return {
    plugins,
    enabledNames,
    hasNodePlugin,
    localNode,
    loaded,
    load,
    refresh,
    syncLocalNode
  }
})
