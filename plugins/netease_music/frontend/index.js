/**
 * 网易云音乐插件前端入口
 *
 * 导出 routes / navItems 供主应用动态注册。
 *
 * 注意：本插件不打包 vue/pinia/reka-ui/ui 组件库等主应用依赖，
 * 运行时通过 window.__etamusic 取用。所有 import 必须从相对路径或
 * window.__etamusic 获取，不能从 'vue'、'pinia' 等裸模块名导入。
 *
 * 视图组件使用动态 import，让 Vite 拆分独立 chunk，避免被 tree-shake。
 */
const { Music, Search, ListMusic, User } = window.__etamusic.icons

export const routes = [
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
]

export const navItems = [
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
