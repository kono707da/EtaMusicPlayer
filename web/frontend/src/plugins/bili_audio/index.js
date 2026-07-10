import { Music, Download, BookmarkIcon } from 'lucide-vue-next'

export default {
  name: 'bili_audio',

  routes: [
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
    }
  ],

  navItems: [
    {
      label: 'B站音频',
      icon: Music,
      children: [
        { path: '/bili', label: '下载音频', icon: Music },
        { path: '/bili/tasks', label: '下载任务', icon: Download },
        { path: '/bili/subscriptions', label: '订阅管理', icon: BookmarkIcon }
      ]
    }
  ]
}
