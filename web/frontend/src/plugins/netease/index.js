import { Music, Search, ListMusic, User } from 'lucide-vue-next'

export default {
  name: 'netease_music',

  routes: [
    {
      path: '/netease',
      name: 'netease-account',
      component: () => import('./views/NeteaseAccountView.vue'),
      meta: { title: '网易云账号' }
    },
    {
      path: '/netease/search',
      name: 'netease-search',
      component: () => import('./views/NeteaseSearchView.vue'),
      meta: { title: '网易云搜索' }
    },
    {
      path: '/netease/playlists',
      name: 'netease-playlists',
      component: () => import('./views/NeteasePlaylistsView.vue'),
      meta: { title: '网易云歌单' }
    },
    {
      path: '/netease/playlist/:id',
      name: 'netease-playlist-detail',
      component: () => import('./views/NeteasePlaylistDetailView.vue'),
      meta: { title: '歌单详情' }
    }
  ],

  navItems: [
    {
      label: '网易云',
      icon: Music,
      children: [
        { path: '/netease', label: '账号', icon: User },
        { path: '/netease/search', label: '搜索', icon: Search },
        { path: '/netease/playlists', label: '我的歌单', icon: ListMusic }
      ]
    }
  ]
}
