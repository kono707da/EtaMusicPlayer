# EtaMusicPlayer

基于 FastAPI + Vue 3 的自托管音乐管理与播放系统，支持本地音频库扫描、流式播放、播放列表管理、去重 / 音质升级检测，并通过插件系统接入 asmr.one 等外部资源。

## 功能特性

### 核心音乐库（local_node 插件）
- **目录扫描**：监控目录管理（支持可视化路径选择器）、递归扫描、音频元数据提取（基于 mutagen）
- **流式播放**：HTTP Range 断点续传，HTML `<audio>` 标签直接播放，JWT query 鉴权
- **播放列表**：CRUD、系统列表「全部音乐」、播放列表粒度授权
- **曲目管理**：搜索、过滤、批量元数据编辑、文件重命名
- **去重检测**：基于可配置字段（标题 / 艺术家 / 时长 / 文件指纹等）
- **音质升级**：检测低码率文件并支持替换
- **用户与权限**：JWT 鉴权、管理员 / 普通用户、播放列表级访问控制

### asmr.one 插件
- 浏览 asmr.one 作品（搜索 / 热门 / 评论 / 收藏夹）
- 文件树展示与预览（图片 / 文本 / 在线音视频播放）
- 一键下载到本地节点（支持 HTTP 代理）

### 系统特性
- **单进程模式**：FastAPI 同时托管 API 与前端静态文件，一个端口、一个进程
- **插件架构**：核心是轻量骨架，节点功能通过插件加载，运行时动态注册路由
- **多节点联邦**：前端支持同时连接多个节点，可切换活跃节点
- **LAN 访问**：默认监听 `0.0.0.0`，局域网设备可直接访问

### 节点自治架构
- **单线程任务队列**：所有写操作（扫描、上传等）通过 NodeTask 队列串行执行，避免并发 SQLite 写入冲突
- **审计日志**：记录何时哪个访问端用哪个用户做了什么重要操作（用户管理、目录管理、扫描、上传等）
- **播放统计**：TrackStats（曲目级）+ UserPlayStats（用户级），支持播放/跳过/完成事件上报
- **数据看板**：总曲目数、播放统计、热门曲目、最近播放、活跃用户
- **SQLite WAL 模式**：读写并发，busy_timeout 5s，外键约束已开启

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10+、FastAPI、SQLAlchemy 2.x、Pydantic 2.x、uvicorn、mutagen、python-jose |
| 前端 | Vue 3、Vite 5、Vue Router 4、Pinia、Tailwind CSS、reka UI (Shadcn Vue)、Howler.js、Axios |
| 数据库 | SQLite（每个插件独立数据库文件） |
| 启动器 | Windows .bat（含端口冲突自动清理） |

## 项目结构

```
EtaMusicPlayer/
├── backend/                    # 后端
│   ├── app/
│   │   ├── main.py             # FastAPI 入口（骨架 + 前端托管 + SPA 回退）
│   │   ├── config.py           # 配置加载
│   │   ├── security.py         # JWT 与密码哈希
│   │   ├── plugins/            # 插件目录
│   │   │   ├── asmr_one/       # asmr.one 浏览/下载插件
│   │   │   └── local_node/     # 本地节点插件（扫描/流式/播放列表/用户/权限等）
│   │   └── plugins_manager/    # 插件管理 API
│   ├── data/                   # 数据库文件（不入库，自动创建）
│   ├── config.yaml             # 配置文件
│   ├── requirements.txt
│   └── run.py                  # 开发模式启动入口
├── frontend/                   # 前端
│   ├── src/
│   │   ├── api/                # API 封装层
│   │   ├── components/         # 通用组件（含 Shadcn Vue UI 组件）
│   │   ├── composables/        # 组合式函数
│   │   ├── plugins/            # 前端插件（与后端插件一一对应）
│   │   │   ├── asmr_one/
│   │   │   └── local_node/
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── views/              # 页面组件
│   │   ├── App.vue
│   │   └── router/
│   ├── vite.config.js
│   └── package.json
├── kill_stale_port.ps1         # 端口占用清理脚本（被 start.bat 调用）
├── start.bat                   # Windows 一键启动入口
└── README.md
```

## 快速开始

### 环境要求
- **Python** 3.10+（[下载](https://www.python.org/downloads/)）
- **Node.js** 18+（[下载](https://nodejs.org/)，用于构建前端）

### Windows 一键启动

双击 `start.bat` 即可。脚本会自动完成：
1. 检测 Python 与 npm（若系统 PATH 中缺失，会尝试使用 TRAE 自带 node 与 ComfyUI Python 作为兜底）
2. 清理 8000 端口上残留的旧 EtaMusic 进程（仅杀命令行匹配 `app.main:app` 的进程，不会误杀其他程序）
3. 若 `frontend/dist/` 不存在则自动 `npm run build` 构建前端
4. 启动 uvicorn 服务于 `http://0.0.0.0:8000`

启动后访问：
- 本机：http://127.0.0.1:8000
- 局域网：`http://<本机IP>:8000`

### 手动启动（开发模式）

```bash
# 1. 安装后端依赖
cd backend
pip install -r requirements.txt

# 2. 安装前端依赖并构建
cd ../frontend
npm install
npm run build        # 生产构建（生成 dist/）

# 3. 启动后端（同时托管前端）
cd ../backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前后端分进程开发（可选）

```bash
# 终端 1：启动后端
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 终端 2：启动 Vite 开发服务器（热更新）
cd frontend
npm run dev
# 访问 http://127.0.0.1:5173，/api 与 /local_node 自动代理到 8000
```

## 默认账号

- 用户名：`admin`
- 密码：`admin123`

**首次启动后请尽快修改密码**（前端「用户管理」或调用 `PUT /api/users/me`）。

## 配置

主配置文件 [backend/config.yaml](backend/config.yaml)：

| 字段 | 说明 | 默认值 |
|---|---|---|
| `host` | 监听地址 | `127.0.0.1` |
| `port` | 监听端口 | `8000` |
| `jwt_secret` | JWT 签名密钥（首次启动自动生成，存储在 `data/settings.json`） | 自动生成 |
| `jwt_expire_minutes` | Token 有效期（分钟） | `1440`（24h） |
| `scan_workers` | 扫描线程数 | `2` |
| `db_path` | SQLite 数据库相对路径 | `data/etamusic.db` |
| `default_admin_password` | 默认管理员密码 | `admin123` |
| `plugins_enabled` | 已启用的插件列表 | `[local_node]` |
| `self_url` | 节点对外可达地址 | `http://127.0.0.1:8000` |

> 注：`start.bat` 启动时通过 `--host 0.0.0.0 --port 8000` 命令行参数覆盖 `config.yaml` 的 `host`/`port`，以支持局域网访问。

## 主要 API

所有接口统一前缀 `/api`：

| 端点 | 说明 |
|---|---|
| `POST /api/auth/login` | 登录获取 JWT |
| `GET /api/tracks` | 曲目列表（分页 / 搜索 / 过滤） |
| `GET /api/tracks/{id}/stream?token=` | 流式播放（支持 Range） |
| `GET/POST/PUT/DELETE /api/playlists` | 播放列表管理 |
| `GET/POST/PUT/DELETE /api/watch-dirs` | 监控目录（管理员） |
| `GET /api/watch-dirs/browse?path=` | 目录浏览（用于路径选择器） |
| `POST /api/scan` | 触发扫描（管理员） |
| `GET/POST/PUT/DELETE /api/users` | 用户管理（管理员） |
| `*/api/permissions*` | 授权管理（管理员） |
| `*/api/dedup*` | 去重检测 |
| `*/api/quality*` | 音质升级 |
| `*/api/metadata*` | 元数据编辑（管理员） |

asmr.one 插件接口前缀 `/api/asmr`。完整文档见 `/docs`（Swagger UI）与 `/redoc`。

## 数据安全

- `backend/data/*.db` 包含用户数据、扫描记录、收藏等，**不可删除**
- `backend/data/uploads/` 存储用户上传的文件
- `backend/data/settings.json` 存储运行时密钥（JWT 密钥等），**不可删除**
- 这些路径已加入 `.gitignore`，不会进入版本库

## 部署建议

- **反向代理**：生产环境推荐用 Nginx 反向代理，配置 HTTPS
- **防火墙**：仅放行必要端口；如需局域网访问，添加 Windows 防火墙入站规则：
  ```powershell
  New-NetFirewallRule -DisplayName "EtaMusic 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Private,Domain
  ```
- **JWT 密钥**：首次启动自动生成并持久化到 `data/settings.json`，无需手动配置
- **进程守护**：Linux 可用 systemd，Windows 可用 NSSM 将 uvicorn 注册为服务

### Docker 部署

Docker 镜像不包含运行时依赖（ffmpeg、Python 包），由 `docker-entrypoint.sh` 在容器首次启动时自动下载到持久化卷 `/app/deps`：

| 卷 | 用途 |
|---|---|
| `etamusic-deps` → `/app/deps` | 运行时依赖（ffmpeg 二进制、Python 包），首次启动后持久化 |
| `etamusic-web-data` → `/app/web/backend/data` | Web 后端数据库与设置 |
| `etamusic-node-data` → `/app/node/data` | 节点数据库 |
| `etamusic-plugins-data` → `/app/data` | 插件数据 |

首次启动会下载 ffmpeg 静态二进制和所有 pip 依赖（约 1-2 分钟），后续启动直接复用已持久化的依赖。如需强制重装依赖，删除 `etamusic-deps` 卷后重启容器即可。

## 许可证

本项目为个人自用，未声明开源许可证。
