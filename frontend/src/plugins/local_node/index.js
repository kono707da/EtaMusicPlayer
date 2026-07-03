/**
 * local_node 插件前端 manifest
 *
 * 本地节点是本机固有的唯一节点，不通过"添加"流程创建。
 * 访问端节点页直接展示本地节点卡片（通过 GET /api/plugins/local-node/status 获取状态）。
 *
 * 本插件对前端 UI 的贡献：
 * - 不贡献 nodeFormPresets（本地节点不是"添加"来的）
 * - 不贡献独立路由/导航（节点功能复用核心页面）
 */
export default {
  name: 'local_node',

  // 本地节点直接展示在节点页，不走预设添加流程
  nodeFormPresets: [],

  routes: [],

  navItems: []
}
