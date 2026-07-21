/**
 * 前端插件注册表（动态加载版）
 *
 * 架构：
 * - local_node 保留在主应用内（无独立路由，仅贡献 nodeFormPresets）
 * - 其他插件通过后端 /api/plugins/frontend-manifests 获取 manifest，
 *   动态 import 插件前端 bundle（/plugins-assets/<name>/index.[hash].js）
 * - 插件前端通过 window.__etamusic 取用主应用暴露的依赖（vue/pinia/ui 等）
 *
 * 加载流程：
 * 1. main.js 启动时调用 loadEnabledPlugins()
 * 2. local_node 直接用内置 manifest
 * 3. 其他插件 fetch manifest → 动态 import → 注册路由
 * 4. App.vue 通过 getPluginNavItems() 响应式获取导航
 *
 * 错误容忍：
 * - 单个插件加载失败不影响其他插件
 * - 后端不可达时仅加载 local_node，其余插件不可用
 */
import { ref } from 'vue'
import local_node from './local_node'

// 已加载的插件列表（响应式，App.vue 通过 computed 感知变化）
const loadedPlugins = ref([])

/**
 * 启动时调用：加载所有已启用插件的前端模块
 *
 * @param {string[]} enabledNames 后端返回的已启用插件名
 * @returns {Promise<{routes: Array, navItems: Array, nodeFormPresets: Array}>}
 *          加载完成的路由、导航项、节点表单预设
 */
export async function loadEnabledPlugins(enabledNames) {
  const result = { routes: [], navItems: [], nodeFormPresets: [] }

  // 1. local_node：内置 manifest，不走动态加载
  if (enabledNames.includes('local_node') && local_node) {
    loadedPlugins.value.push(local_node)
    result.routes.push(...(local_node.routes || []))
    result.navItems.push(...(local_node.navItems || []))
    result.nodeFormPresets.push(...(local_node.nodeFormPresets || []))
  }

  // 2. 其他插件：通过后端 manifest 动态加载
  try {
    const resp = await fetch('/api/plugins/frontend-manifests')
    if (!resp.ok) {
      console.warn('[plugins] 获取插件 manifest 失败:', resp.status, resp.statusText)
      return result
    }
    const data = await resp.json()
    const manifests = data.manifests || []

    // 串行加载（并行加载在低端浏览器上可能资源争用）
    for (const m of manifests) {
      if (!m.entry) {
        console.warn(`[plugins] 插件 ${m.name} manifest 缺少 entry，跳过`)
        continue
      }
      try {
        // @vite-ignore 必须加，否则 Vite 构建时会尝试静态分析这个 import
        const mod = await import(/* @vite-ignore */ m.entry)
        const plugin = {
          name: m.name,
          version: m.version || '',
          routes: mod.routes || [],
          navItems: mod.navItems || [],
          nodeFormPresets: mod.nodeFormPresets || []
        }
        loadedPlugins.value.push(plugin)
        result.routes.push(...plugin.routes)
        result.navItems.push(...plugin.navItems)
        result.nodeFormPresets.push(...plugin.nodeFormPresets)
        console.info(`[plugins] 已加载插件前端: ${m.name} (${m.version || 'unknown'})`)
      } catch (e) {
        console.error(`[plugins] 插件 ${m.name} 前端加载失败:`, e)
      }
    }
  } catch (e) {
    console.error('[plugins] 加载插件 manifest 失败:', e)
  }

  return result
}

/**
 * 获取已加载插件贡献的导航项
 * 响应式：loadedPlugins 变化时自动重算
 */
export function getPluginNavItems(enabledNames) {
  return loadedPlugins.value
    .filter((p) => enabledNames.includes(p.name))
    .flatMap((p) => p.navItems || [])
}

/**
 * 获取已加载插件贡献给"节点管理"页的快速添加预设
 */
export function getPluginNodePresets(enabledNames) {
  return loadedPlugins.value
    .filter((p) => enabledNames.includes(p.name))
    .flatMap((p) => p.nodeFormPresets || [])
}

export { loadedPlugins }
