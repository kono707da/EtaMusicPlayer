import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './styles/main.css'

import { setupRuntime } from './lib/runtime'
import { usePluginsStore } from './stores/plugins'
import { useNodesStore } from './stores/nodes'
import { loadEnabledPlugins } from './plugins'

/**
 * 启动流程：
 * 1. 创建 app，安装 pinia + router
 * 2. 暴露运行时到 window.__etamusic（必须在插件加载前完成）
 * 3. 从后端获取已启用插件列表
 * 4. 同步本地节点：插件启用即自动连接，无需用户手动登录
 * 5. 动态加载已启用插件的前端模块（动态 import）并注册路由
 * 6. 挂载 app
 *
 * 后端不可达时仍可挂载（仅核心功能可用）
 */
;(async () => {
  const app = createApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)

  // 1. 暴露运行时依赖（插件通过 window.__etamusic 取用）
  setupRuntime()

  // 2. 获取已启用插件
  const pluginsStore = usePluginsStore(pinia)
  await pluginsStore.load()

  // 3. 同步本地节点到 nodes store（插件启用即自动连接）
  const nodesStore = useNodesStore(pinia)
  await nodesStore.load()
  await pluginsStore.syncLocalNode(nodesStore)

  // 4. 动态加载已启用插件的前端模块并注册路由
  // local_node 的 manifest 已在主应用内静态导入，其余插件走动态加载
  const { routes: pluginRoutes } = await loadEnabledPlugins(pluginsStore.enabledNames)
  pluginRoutes.forEach((route) => router.addRoute(route))

  app.mount('#app')
})()
