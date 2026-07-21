/**
 * B站音频插件前端入口
 *
 * 导出 routes / navItems 供主应用动态注册。
 *
 * 注意：本插件不打包 vue/pinia/reka-ui/ui 组件库等主应用依赖，
 * 运行时通过 window.__etamusic 取用。所有 import 必须从相对路径或
 * window.__etamusic 获取，不能从 'vue'、'pinia' 等裸模块名导入。
 *
 * 视图组件使用动态 import，让 Vite 拆分独立 chunk，避免被 tree-shake。
 */
const { Music, Download, BookmarkIcon, Settings } = window.__etamusic.icons

export const routes = [
  {
    path: '/bili',
    name: 'bili-download',
    component: () => import('./views/BiliDownloadView.vue'),
    meta: { title: 'B站音频' }
  },
  {
    path: '/bili/tasks',
    name: 'bili-tasks',
    component: () => import('./views/BiliTasksView.vue'),
    meta: { title: '下载任务' }
  },
  {
    path: '/bili/subscriptions',
    name: 'bili-subscriptions',
    component: () => import('./views/BiliSubscriptionView.vue'),
    meta: { title: '订阅管理' }
  },
  {
    path: '/bili/settings',
    name: 'bili-settings',
    component: () => import('./views/BiliSettingsView.vue'),
    meta: { title: 'B站设置' }
  }
]

export const navItems = [
  {
    label: 'B站音频',
    icon: Music,
    children: [
      { path: '/bili', label: '下载音频', icon: Music },
      { path: '/bili/tasks', label: '下载任务', icon: Download },
      { path: '/bili/subscriptions', label: '订阅管理', icon: BookmarkIcon },
      { path: '/bili/settings', label: '设置', icon: Settings }
    ]
  }
]
