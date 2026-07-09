# EtaMusic 网页端

EtaMusic 多节点音乐系统的访问端，聚合多个节点（每个节点是一个 FastAPI 服务）的资源进行统一播放。

## 技术栈

- Vue 3 (Composition API, `<script setup>`)
- Vite 5
- Vue Router 4
- Pinia
- Element Plus（全量引入）
- Axios
- Howler.js（音频播放）

## 目录结构

```
frontend/
  index.html
  package.json
  vite.config.js
  README.md
  src/
    main.js                # 入口，挂载 Pinia/Router/ElementPlus
    App.vue                # 根组件，含布局
    router/
      index.js             # 路由表，含登录守卫
    stores/
      auth.js              # 当前激活节点的登录态
      nodes.js             # 节点列表管理
      player.js            # 播放器状态
      library.js           # 聚合曲库
    api/
      client.js            # axios 工厂
      node.js              # 节点 API 封装
    views/                 # 视图页面
    components/            # 公共组件
```

## 启动方式

```bash
# 安装依赖
npm install

# 启动开发服务器（默认端口 5173）
npm run dev

# 构建生产包
npm run build

# 预览生产包
npm run preview
```

## 功能说明

### 节点管理
- 添加节点：填名称、baseUrl、用户名、密码 → 自动登录拿 token → 保存
- 编辑/删除节点
- 节点列表持久化到 localStorage（key: `etamusic_nodes`）
- 切换当前激活节点

### 曲库浏览
- 左侧树：节点 > 播放列表
- 右侧表格：曲目列表（双击播放、右键加入队列）
- 跨节点搜索：对所有节点并发调 `/api/tracks?q=`，合并结果

### 播放器
- 底部固定栏：封面、标题、艺术家、进度条、播放控制、音量
- Howler.js 加载流式 URL（带 token query 参数）
- 显示当前播放的来源节点

### 管理功能（需 is_admin）
- 扫描管理、元数据批量编辑、去重检测、音质升级、播放列表授权、用户管理

## 路由表

| 路径 | 说明 | 权限 |
| --- | --- | --- |
| `/login` | 登录页 | 公开 |
| `/library` | 曲库浏览（默认首页） | 已登录 |
| `/playlists` | 播放列表管理 | 已登录 |
| `/nodes` | 节点管理 | 已登录 |
| `/admin/scan` | 扫描管理 | 管理员 |
| `/admin/metadata` | 元数据批量编辑 | 管理员 |
| `/admin/dedup` | 去重检测 | 管理员 |
| `/admin/quality` | 音质升级 | 管理员 |
| `/admin/permissions` | 播放列表授权 | 管理员 |
| `/admin/users` | 用户管理 | 管理员 |

## 开发代理

`vite.config.js` 已配置 `/api` 代理到 `http://127.0.0.1:8000`，开发时如默认节点也运行在该地址可直接访问。其他节点需填写完整 baseUrl。
