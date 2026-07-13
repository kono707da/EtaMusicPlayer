import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNodesStore } from '../stores/nodes'

/**
 * 包裹动态 import：chunk 加载失败时（通常是部署后旧 hash 失效）自动刷新一次
 * 用 sessionStorage 防止无限刷新循环
 */
function lazy(loader) {
  return () =>
    loader().catch((err) => {
      const key = 'chunk-reloaded'
      if (!sessionStorage.getItem(key)) {
        sessionStorage.setItem(key, '1')
        window.location.reload()
        return new Promise(() => {})
      }
      sessionStorage.removeItem(key)
      throw err
    })
}

const routes = [
  {
    path: '/',
    redirect: '/library'
  },
  {
    path: '/library',
    name: 'library',
    component: lazy(() => import('../views/LibraryView.vue'))
  },
  {
    path: '/playlists',
    redirect: '/library'
  },
  {
    path: '/nodes',
    name: 'nodes',
    component: lazy(() => import('../views/NodesView.vue'))
  },
  {
    path: '/plugins',
    name: 'plugins',
    component: lazy(() => import('../views/PluginsView.vue'))
  },
  {
    path: '/settings',
    name: 'settings',
    component: lazy(() => import('../views/SettingsView.vue'))
  },
  // 管理功能路由（需要当前激活节点管理员权限）
  {
    path: '/admin/scan',
    name: 'admin-scan',
    component: lazy(() => import('../views/ScanView.vue')),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/metadata',
    name: 'admin-metadata',
    component: lazy(() => import('../views/MetadataView.vue')),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/dedup',
    name: 'admin-dedup',
    component: lazy(() => import('../views/DedupView.vue')),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/quality',
    name: 'admin-quality',
    component: lazy(() => import('../views/QualityView.vue')),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/permissions',
    name: 'admin-permissions',
    component: lazy(() => import('../views/PermissionsView.vue')),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: lazy(() => import('../views/UsersView.vue')),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/tasks',
    name: 'admin-tasks',
    component: lazy(() => import('../views/TasksView.vue')),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/audit',
    name: 'admin-audit',
    component: lazy(() => import('../views/AuditLogView.vue')),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/dashboard',
    name: 'admin-dashboard',
    component: lazy(() => import('../views/DashboardView.vue')),
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
router.beforeEach((to, _from, next) => {
  if (!to.meta.requiresAdmin) {
    return next()
  }
  const nodesStore = useNodesStore()
  const authStore = useAuthStore()

  const nodeId = to.query.nodeId
  if (nodeId) {
    // 指定节点：检查该节点是否已登录且为 admin
    const node = nodesStore.getNode(String(nodeId))
    if (!node || !node.token) {
      next({ path: '/nodes', query: { redirect: to.fullPath } })
      return
    }
    if (!node.userInfo?.is_admin) {
      next('/library')
      return
    }
  } else {
    // 未指定节点：回退到本地节点
    if (!authStore.isLoggedIn) {
      next({ path: '/nodes', query: { redirect: to.fullPath } })
      return
    }
    if (!authStore.isAdmin) {
      next('/library')
      return
    }
  }
  next()
})

export default router
