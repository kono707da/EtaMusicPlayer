/**
 * asmr_one 插件前端 manifest
 *
 * 贡献：
 * - 路由：搜索、作品详情、下载任务、账户、我的评价、我的收藏、热门
 * - 侧边栏导航项（归到一个 ASMR 父项下，可折叠）
 * - 设置已统一到全局设置页
 */
import { Headphones, User, Star, Heart, Flame, Download } from 'lucide-vue-next'

export default {
  name: 'asmr_one',

  routes: [
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
  ],

  navItems: [
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
}
