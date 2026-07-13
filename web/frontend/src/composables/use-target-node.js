import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useNodesStore } from '../stores/nodes'
import { useAuthStore } from '../stores/auth'

/**
 * 管理页面的目标节点解析
 *
 * 从 route.query.nodeId 读取目标节点 ID：
 * - 有 nodeId：从 nodesStore 查找对应节点（远程节点 ID 格式为 remote-{id}）
 * - 无 nodeId：回退到本地节点（兼容旧逻辑）
 *
 * 返回：
 * - targetNode：目标节点对象（可能为 null）
 * - nodeMissing：节点不存在或未登录
 * - nodeMissingMessage：缺失时的提示文本
 */
export function useTargetNode() {
  const route = useRoute()
  const nodesStore = useNodesStore()
  const authStore = useAuthStore()

  const targetNode = computed(() => {
    const nodeId = route.query.nodeId
    if (nodeId) {
      return nodesStore.getNode(String(nodeId)) || null
    }
    return authStore.localNode
  })

  const nodeMissing = computed(() => !targetNode.value || !targetNode.value.token)

  const nodeMissingMessage = computed(() => {
    if (!targetNode.value) return '节点不存在，请返回节点管理页面重新添加'
    if (!targetNode.value.token) return '节点未登录，请返回节点管理页面重新登录'
    return ''
  })

  return { targetNode, nodeMissing, nodeMissingMessage }
}
