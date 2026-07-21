const { Music: e, Search: t, ListMusic: a, User: n } = window.__etamusic.icons, s = [
  {
    path: "/netease",
    name: "netease-account",
    component: () => import("./assets/NeteaseAccountView-IWMZjmMq.js"),
    meta: { title: "网易云账号" }
  },
  {
    path: "/netease/search",
    name: "netease-search",
    component: () => import("./assets/NeteaseSearchView-BYeNNOsY.js"),
    meta: { title: "网易云搜索" }
  },
  {
    path: "/netease/playlists",
    name: "netease-playlists",
    component: () => import("./assets/NeteasePlaylistsView-LRVXfecN.js"),
    meta: { title: "网易云歌单" }
  },
  {
    path: "/netease/playlist/:id",
    name: "netease-playlist-detail",
    component: () => import("./assets/NeteasePlaylistDetailView-Ck3qEW9c.js"),
    meta: { title: "歌单详情" }
  }
], i = [
  {
    label: "网易云",
    icon: e,
    children: [
      { path: "/netease", label: "账号", icon: n },
      { path: "/netease/search", label: "搜索", icon: t },
      { path: "/netease/playlists", label: "我的歌单", icon: a }
    ]
  }
];
export {
  i as navItems,
  s as routes
};
