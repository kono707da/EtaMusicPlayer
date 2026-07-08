import { Music, Download, Settings } from 'lucide-vue-next'

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
      path: '/bili/settings',
      name: 'bili-settings',
      component: () => import('./views/BiliSettingsView.vue'),
      meta: { title: 'B站设置' }
    }
  ],

  navItems: [
    {
      label: 'B站音频',
      icon: Music,
      children: [
        { path: '/bili', label: '下载音频', icon: Music },
        { path: '/bili/tasks', label: '下载任务', icon: Download },
        { path: '/bili/settings', label: '设置', icon: Settings }
      ]
    }
  ]
}
