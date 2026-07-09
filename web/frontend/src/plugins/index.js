/**
 * 前端插件注册表
 *
 * 所有可用插件的前端 manifest 动态导入，
 * 运行时根据后端返回的 enabledNames 过滤，动态注册路由/导航/预设。
 * 插件模块缺失时不影响基础程序运行。
 */
import asmr_one from './asmr_one'
import bili_audio from './bili_audio'

let local_node = null
try {
  const modules = import.meta.glob('./local_node/index.js', { eager: true })
  const mod = modules['./local_node/index.js']
  if (mod) {
    local_node = mod.default || mod
  }
} catch (e) {
  // local_node 插件前端模块不存在，跳过
}

const allPlugins = [local_node, asmr_one, bili_audio].filter(Boolean)

/**
 * 获取已启用插件的 manifest 列表
 * @param {string[]} enabledNames 后端返回的已启用插件名
 */
export function getEnabledPlugins(enabledNames) {
  return allPlugins.filter((p) => enabledNames.includes(p.name))
}

/**
 * 聚合已启用插件的路由
 */
export function getPluginRoutes(enabledNames) {
  return getEnabledPlugins(enabledNames).flatMap((p) => p.routes || [])
}

/**
 * 聚合已启用插件的导航项
 */
export function getPluginNavItems(enabledNames) {
  return getEnabledPlugins(enabledNames).flatMap((p) => p.navItems || [])
}

/**
 * 聚合已启用插件贡献给"节点管理"页的快速添加预设
 */
export function getPluginNodePresets(enabledNames) {
  return getEnabledPlugins(enabledNames).flatMap((p) => p.nodeFormPresets || [])
}

export { allPlugins }
