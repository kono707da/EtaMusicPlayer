import { createRouter, createWebHistory } from 'vue-router'
import { useNodesStore } from '../stores/nodes'
import { useAuthStore } from '../stores/auth'

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
  // 管理功能路由（需要当前激活节点管理员权限）
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
    path: '/admin/tasks',
    name: 'admin-tasks',
    component: () => import('../views/TasksView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/audit',
    name: 'admin-audit',
    component: () => import('../views/AuditLogView.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/dashboard',
    name: 'admin-dashboard',
    component: () => import('../views/DashboardView.vue'),
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
  // 需要管理员权限：检查当前激活节点是否已登录且为 admin
  const nodesStore = useNodesStore()
  const authStore = useAuthStore()
  authStore.restoreFromNode(nodesStore.activeNode)
  if (!authStore.isLoggedIn) {
    next({ path: '/nodes', query: { redirect: to.fullPath } })
    return
  }
  if (!authStore.isAdmin) {
    next('/library')
    return
  }
  next()
})

export default router
