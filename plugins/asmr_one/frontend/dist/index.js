const { Headphones: a, User: t, Star: e, Heart: o, Flame: m, Download: r } = window.__etamusic.icons, n = [
  {
    path: "/asmr",
    name: "asmr-search",
    component: () => import("./assets/AsmrSearchView-CrDX26Es.js"),
    meta: { title: "ASMR 资源" }
  },
  {
    path: "/asmr/work/:id",
    name: "asmr-work",
    component: () => import("./assets/AsmrWorkView-BqX9-o2E.js"),
    meta: { title: "作品详情" }
  },
  {
    path: "/asmr/downloads",
    name: "asmr-downloads",
    component: () => import("./assets/AsmrDownloadsView-B-JjelHj.js"),
    meta: { title: "下载任务" }
  },
  {
    path: "/asmr/account",
    name: "asmr-account",
    component: () => import("./assets/AsmrAccountView-e_yrMi__.js"),
    meta: { title: "ASMR 账户" }
  },
  {
    path: "/asmr/reviews",
    name: "asmr-reviews",
    component: () => import("./assets/AsmrReviewsView-D1Mn28gc.js"),
    meta: { title: "我的评价" }
  },
  {
    path: "/asmr/favorites",
    name: "asmr-favorites",
    component: () => import("./assets/AsmrFavoritesView-BwFptAoS.js"),
    meta: { title: "我的播放列表" }
  },
  {
    path: "/asmr/popular",
    name: "asmr-popular",
    component: () => import("./assets/AsmrPopularView-CQFiFlTz.js"),
    meta: { title: "热门推荐" }
  }
], s = [
  {
    label: "ASMR",
    icon: a,
    children: [
      { path: "/asmr", label: "资源浏览", icon: a },
      { path: "/asmr/popular", label: "热门推荐", icon: m },
      { path: "/asmr/favorites", label: "我的播放列表", icon: o },
      { path: "/asmr/reviews", label: "我的评价", icon: e },
      { path: "/asmr/downloads", label: "下载任务", icon: r },
      { path: "/asmr/account", label: "账户", icon: t }
    ]
  }
];
export {
  s as navItems,
  n as routes
};
