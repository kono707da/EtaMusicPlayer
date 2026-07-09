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

  const hasNodePlugin = computed(() => enabledNames.value.length > 0)

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
   * 返回本地节点状态
   */
  async function syncLocalNode(nodesStore) {
    try {
      const status = await getLocalNodeStatus()
      localNode.value = status

      const existing = nodesStore.nodes.find((n) => n.baseUrl === '/local_node')

      if (status.available && status.access_token) {
        // 插件可用且有 token：自动写入/更新
        const token = status.access_token
        const userInfo = status.user_info
        if (existing) {
          // 更新 token（若变化）
          if (existing.token !== token) {
            nodesStore.updateNode(existing.id, { token, userInfo })
          }
        } else {
          // 新增本地节点记录
          const added = nodesStore.addNode({
            name: '本地节点',
            baseUrl: '/local_node',
            username: 'admin',
            password: 'admin123'
          })
          nodesStore.updateNode(added.id, { token, userInfo })
        }
        // 若当前没有激活节点，激活本地节点
        if (!nodesStore.activeNodeId) {
          const target = nodesStore.nodes.find((n) => n.baseUrl === '/local_node')
          if (target) nodesStore.setActive(target.id)
        }
      } else if (!status.available && existing) {
        // 插件不可用：移除本地节点记录
        nodesStore.removeNode(existing.id)
      }

      return status
    } catch (e) {
      localNode.value = { available: false, message: '无法获取本地节点状态' }
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
