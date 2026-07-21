/**
 * asmr_one 插件前端入口
 *
 * 导出 routes / navItems 供主应用动态注册。
 *
 * 注意：本插件不打包 vue/pinia/reka-ui/ui 组件库等主应用依赖，
 * 运行时通过 window.__etamusic 取用。所有 import 必须从相对路径或
 * window.__etamusic 获取，不能从 'vue'、'pinia' 等裸模块名导入。
 *
 * 视图组件使用动态 import，让 Vite 拆分独立 chunk，避免被 tree-shake。
 */
const { Headphones, User, Star, Heart, Flame, Download } = window.__etamusic.icons

export const routes = [
  {
    path: '/asmr',
    name: 'asmr-search',
    component: () => import('./views/AsmrSearchView.vue'),
    meta: { title: 'ASMR 资源' }
  },
  {
    path: '/asmr/work/:id',
    name: 'asmr-work',
    component: () => import('./views/AsmrWorkView.vue'),
    meta: { title: '作品详情' }
  },
  {
    path: '/asmr/downloads',
    name: 'asmr-downloads',
    component: () => import('./views/AsmrDownloadsView.vue'),
    meta: { title: '下载任务' }
  },
  {
    path: '/asmr/account',
    name: 'asmr-account',
    component: () => import('./views/AsmrAccountView.vue'),
    meta: { title: 'ASMR 账户' }
  },
  {
    path: '/asmr/reviews',
    name: 'asmr-reviews',
    component: () => import('./views/AsmrReviewsView.vue'),
    meta: { title: '我的评价' }
  },
  {
    path: '/asmr/favorites',
    name: 'asmr-favorites',
    component: () => import('./views/AsmrFavoritesView.vue'),
    meta: { title: '我的播放列表' }
  },
  {
    path: '/asmr/popular',
    name: 'asmr-popular',
    component: () => import('./views/AsmrPopularView.vue'),
    meta: { title: '热门推荐' }
  }
]

export const navItems = [
  {
    label: 'ASMR',
    icon: Headphones,
    children: [
      { path: '/asmr', label: '资源浏览', icon: Headphones },
      { path: '/asmr/popular', label: '热门推荐', icon: Flame },
      { path: '/asmr/favorites', label: '我的播放列表', icon: Heart },
      { path: '/asmr/reviews', label: '我的评价', icon: Star },
      { path: '/asmr/downloads', label: '下载任务', icon: Download },
      { path: '/asmr/account', label: '账户', icon: User }
    ]
  }
]
