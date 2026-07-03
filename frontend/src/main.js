import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './styles/main.css'

import { usePluginsStore } from './stores/plugins'
import { useNodesStore } from './stores/nodes'
import { useAuthStore } from './stores/auth'
import { getPluginRoutes } from './plugins'

/**
 * 启动流程：
 * 1. 创建 app，安装 pinia + router
 * 2. 从后端获取已启用插件列表
 * 3. 同步本地节点：插件启用即自动连接，无需用户手动登录
 * 4. 动态注册插件贡献的路由
 * 5. 挂载 app
 *
 * 后端不可达时仍可挂载（仅核心功能可用）
 */
;(async () => {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)

  // 获取已启用插件
  const pluginsStore = usePluginsStore(pinia)
  await pluginsStore.load()

  // 同步本地节点到 nodes store（插件启用即自动连接）
  const nodesStore = useNodesStore(pinia)
  const authStore = useAuthStore(pinia)
  await nodesStore.load()
  await pluginsStore.syncLocalNode(nodesStore)

  // 恢复激活节点的认证状态
  if (nodesStore.activeNode) {
    authStore.restoreFromNode(nodesStore.activeNode)
  }

  // 动态注册插件路由
  const pluginRoutes = getPluginRoutes(pluginsStore.enabledNames)
  pluginRoutes.forEach((route) => router.addRoute(route))

  app.mount('#app')
})()
