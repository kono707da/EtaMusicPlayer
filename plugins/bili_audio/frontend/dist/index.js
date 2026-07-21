const { Music: i, Download: t, BookmarkIcon: n, Settings: o } = window.__etamusic.icons, e = [
  {
    path: "/bili",
    name: "bili-download",
    component: () => import("./assets/BiliDownloadView-B0-ehVlS.js"),
    meta: { title: "B站音频" }
  },
  {
    path: "/bili/tasks",
    name: "bili-tasks",
    component: () => import("./assets/BiliTasksView-CLW7jQ0X.js"),
    meta: { title: "下载任务" }
  },
  {
    path: "/bili/subscriptions",
    name: "bili-subscriptions",
    component: () => import("./assets/BiliSubscriptionView-TIljoTOd.js"),
    meta: { title: "订阅管理" }
  },
  {
    path: "/bili/settings",
    name: "bili-settings",
    component: () => import("./assets/BiliSettingsView-Begl--RH.js"),
    meta: { title: "B站设置" }
  }
], s = [
  {
    label: "B站音频",
    icon: i,
    children: [
      { path: "/bili", label: "下载音频", icon: i },
      { path: "/bili/tasks", label: "下载任务", icon: t },
      { path: "/bili/subscriptions", label: "订阅管理", icon: n },
      { path: "/bili/settings", label: "设置", icon: o }
    ]
  }
];
export {
  s as navItems,
  e as routes
};
