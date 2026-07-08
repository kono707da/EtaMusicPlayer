# EtaMusic 节点后端

多节点联邦音乐系统的节点端服务，基于 FastAPI + SQLite 实现。

## 功能概览

- 用户与权限管理（JWT 鉴权、播放列表粒度授权）
- 监控目录管理与音频元数据扫描（mutagen）
- 曲目流式分发（支持 HTTP Range 断点续传）
- 播放列表 CRUD（含系统列表 "全部音乐"）
- 去重检测（字段可配置）
- 音质升级检测与替换
- 元数据批量编辑与文件重命名

## 环境要求

- Python 3.10+
- Windows / Linux / macOS

## 安装

```bash
cd backend
pip install -r requirements.txt
```

## 启动

```bash
cd backend
python run.py
```

启动后访问：

- OpenAPI 文档: http://127.0.0.1:8000/docs
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 默认账号

- 用户名: `admin`
- 密码: `admin123`

**首次启动后请尽快修改密码。**

## 配置文件

`backend/config.yaml` 主要字段：

| 字段 | 说明 |
|------|------|
| host / port | 监听地址与端口 |
| jwt_secret | JWT 签名密钥（首次启动自动生成，存储在 data/settings.json） |
| jwt_expire_minutes | Token 有效期（分钟） |
| scan_workers | 扫描线程数 |
| db_path | SQLite 数据库相对路径 |
| default_admin_password | 默认管理员密码 |

## 数据文件

- `backend/data/etamusic.db`：SQLite 数据库，自动创建，**不可删除**
- `backend/data/settings.json`：运行时密钥（JWT 密钥等），自动生成，**不可删除**
- `backend/config.yaml`：配置文件

## 主要 API

所有接口统一前缀 `/api`：

- `POST /api/auth/login` 登录获取 token
- `GET /api/tracks` 曲目列表
- `GET /api/tracks/{id}/stream?token=` 流式播放
- `GET/POST/PUT/DELETE /api/playlists` 播放列表管理
- `GET/POST/PUT/DELETE /api/watch-dirs` 监控目录（管理员）
- `POST /api/scan` 触发扫描（管理员）
- `GET/POST/PUT/DELETE /api/users` 用户管理（管理员）
- `*/api/permissions*` 授权管理（管理员）
- `*/api/dedup*` 去重检测
- `*/api/quality*` 音质升级
- `*/api/metadata*` 元数据编辑（管理员）

详细参数见 `/docs`。

## 流式鉴权说明

音频流接口 `GET /api/tracks/{id}/stream` 通过 query 参数 `?token=xxx` 传递 JWT，避免 HTML `<audio>` 标签无法设置请求头。
