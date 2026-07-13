import { createRouter, createWebHistory } from 'vue-router'
import { useNodesStore } from '../stores/nodes'

const routes = [
  {
    path: '/',
    redirect: '/library'
  },
  {
    path: '/library',
    name: 'library',
    component: () => import('../views/LibraryView.vue')
  },
  {
    path: '/playlists',
    name: 'playlists',
    component: () => import('../views/PlaylistsView.vue')
  },
  {
    path: '/nodes',
    name: 'nodes',
    component: () => import('../views/NodesView.vue')
  },
  {
    path: '/plugins',
    name: 'plugins',
    component: () => import('../views/PluginsView.vue')
  },
  // 管理功能路由（需要 URL query nodeId 对应的节点已登录且为 admin）
  {
    path: '/admin/scan',
    name: 'admin-scan',
    component: () => import('../views/ScanView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/metadata',
    name: 'admin-metadata',
    component: () => import('../views/MetadataView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/dedup',
    name: 'admin-dedup',
    component: () => import('../views/DedupView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/quality',
    name: 'admin-quality',
    component: () => import('../views/QualityView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/permissions',
    name: 'admin-permissions',
    component: () => import('../views/PermissionsView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('../views/UsersView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/library'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫：仅拦截 admin 路由
// 检查 URL query 参数 nodeId 对应的节点是否已登录且是 admin
router.beforeEach((to, _from, next) => {
  if (!to.meta.requiresAdmin) {
    return next()
  }
  const nodesStore = useNodesStore()
  const nodeId = to.query.nodeId
  if (nodeId == null) {
    // 没有 nodeId query：重定向到 /nodes 并带 redirect
    next({ path: '/nodes', query: { redirect: to.fullPath } })
    return
  }
  const target = nodesStore.nodes.find((n) => n.id === Number(nodeId))
  if (!target || !target.token) {
    // 节点未登录：重定向到 /nodes 并带 redirect
    next({ path: '/nodes', query: { redirect: to.fullPath } })
    return
  }
  if (!target.userInfo?.is_admin) {
    // 非 admin：回工作台
    next('/library')
    return
  }
  next()
})

export default router
