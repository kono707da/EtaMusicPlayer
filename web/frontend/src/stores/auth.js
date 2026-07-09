import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 当前激活节点的登录态
 * token / userInfo 都来自当前激活节点，切换节点时由 restoreFromNode 同步
 *
 * 登录动作由 nodesStore.loginNode(id) 完成，本 store 仅维护当前激活节点的登录态快照
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref('')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => !!userInfo.value?.is_admin)
  const username = computed(() => userInfo.value?.username || '')

  /**
   * 从节点配置恢复登录态（用于切换激活节点、刷新页面、进入 admin 路由前校验）
   */
  function restoreFromNode(node) {
    if (!node) {
      clear()
      return
    }
    token.value = node.token || ''
    userInfo.value = node.userInfo || null
  }

  function setAuth(t, info) {
    token.value = t
    userInfo.value = info
  }

  function clear() {
    token.value = ''
    userInfo.value = null
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    username,
    restoreFromNode,
    setAuth,
    clear
  }
})
