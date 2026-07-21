/**
 * 客户端版本与功能能力定义
 *
 * 与 node 端 eta_node/version.py 对应。
 * 客户端通过 GET /api/version 获取 node 的版本信息后，
 * 使用此处的常量进行兼容性校验。
 */

// 客户端软件版本号
export const CLIENT_VERSION = '1.4.0'

// 客户端支持的 API 协议主版本
// 与 node 的 API_VERSION 不一致时，视为完全不兼容
export const CLIENT_API_VERSION = 1

// 客户端要求的最低 node 版本
// 低于此版本的 node 将被拒绝连接
// 1.2.0 起：节点需支持 data_sync 功能（曲库/播放列表增量同步与离线缓存）
// 1.2.1 起：节点需支持曲目删除与软删除一致性（track_delete 任务、真 SHA-256 file_hash）
export const MIN_NODE_VERSION = '1.2.0'

/**
 * 客户端功能到 node feature 的映射
 *
 * key: 功能标识（与 node 的 features 列表对应）
 * value: 功能的 UI 元信息，用于在界面展示提示
 *   - label: 功能中文名
 *   - routes: 该功能对应的前端路由（用于在管理页面禁用/提示）
 *   - required: 是否为核心功能（缺失则拒绝连接）
 *   - description: 功能描述（用于提示文案）
 */
export const FEATURE_REGISTRY = {
  auth: {
    label: '认证',
    required: true,
    description: '登录与身份验证'
  },
  tracks: {
    label: '曲目浏览',
    required: true,
    description: '曲目列表、流式播放、封面、歌词'
  },
  playlists: {
    label: '播放列表',
    required: true,
    description: '播放列表创建与管理'
  },
  watch_dirs: {
    label: '监控目录',
    routes: ['/admin/scan'],
    description: '监控目录配置与浏览'
  },
  scan: {
    label: '扫描入库',
    routes: ['/admin/scan'],
    description: '扫描本地音乐文件入库'
  },
  upload: {
    label: '文件上传',
    description: '上传音频文件到节点'
  },
  metadata: {
    label: '元数据编辑',
    routes: ['/admin/metadata'],
    description: '批量编辑曲目元数据'
  },
  dedup: {
    label: '去重检测',
    routes: ['/admin/dedup'],
    description: '检测并处理重复曲目'
  },
  quality: {
    label: '音质升级',
    routes: ['/admin/quality'],
    description: '检测并替换为更高音质版本'
  },
  users: {
    label: '用户管理',
    routes: ['/admin/users'],
    description: '节点用户账号管理'
  },
  permissions: {
    label: '播放列表授权',
    routes: ['/admin/permissions'],
    description: '播放列表访问授权管理'
  },
  tasks: {
    label: '任务管理',
    routes: ['/admin/tasks'],
    description: '查看与管理异步任务队列'
  },
  audit: {
    label: '审计日志',
    routes: ['/admin/audit'],
    description: '查看操作审计日志'
  },
  stats: {
    label: '数据看板',
    routes: ['/admin/dashboard'],
    description: '播放统计与数据看板'
  },
  inbox: {
    label: '收集箱',
    description: '系统收集箱播放列表'
  },
  import_m3u: {
    label: 'm3u 导入',
    description: '从 m3u 文件批量导入播放列表'
  },
  data_sync: {
    label: '离线缓存同步',
    description: '曲库/播放列表版本号与增量同步，节点离线时访问端可读缓存'
  }
}

// 客户端期望的所有功能标识列表（用于与 node features 对比）
export const CLIENT_FEATURES = Object.keys(FEATURE_REGISTRY)

// 核心功能（缺失则拒绝连接）
export const REQUIRED_FEATURES = CLIENT_FEATURES.filter(
  (f) => FEATURE_REGISTRY[f].required
)
