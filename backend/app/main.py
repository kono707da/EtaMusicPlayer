"""EtaMusic 访问端 - 轻量骨架

不包含节点功能（扫描/流式/播放列表等），仅提供：
- 插件加载器
- 健康检查
- CORS 中间件
- 前端静态文件托管（生产模式）

节点功能通过加载 local_node 等插件获得。
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.plugins import load_plugins
from app.plugins_manager.routers import router as plugins_router, set_loaded_plugins

logger = logging.getLogger("etamusic")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# 前端构建产物目录（backend/app/../../frontend/dist = frontend/dist）
FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/dist")
)

_loaded_plugins: list[str] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时加载插件"""
    global _loaded_plugins
    _loaded_plugins = load_plugins(app)
    # 把加载结果同步给插件管理路由，用于展示运行时状态
    set_loaded_plugins(_loaded_plugins)
    if _loaded_plugins:
        logger.info("已加载插件: %s", ", ".join(_loaded_plugins))
    else:
        logger.warning("未加载任何插件，访问端不具备节点功能")
    if os.path.isdir(FRONTEND_DIST):
        logger.info("前端静态文件托管已启用: %s", FRONTEND_DIST)
    else:
        logger.warning(
            "前端 dist 目录不存在（%s），请先运行 npm run build；当前仅提供 API",
            FRONTEND_DIST,
        )
    yield


app = FastAPI(
    title="EtaMusic 访问端",
    description="多节点联邦音乐系统 - 访问端（轻量骨架，节点功能通过插件加载）",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 允许所有源（开发期）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
)

# 访问端骨架自带的路由（不依赖任何插件）
app.include_router(plugins_router)


@app.get("/health", tags=["root"])
def health() -> dict:
    """健康检查"""
    return {"status": "ok", "plugins": _loaded_plugins}


# ===== 前端静态文件托管（生产模式）=====
# 注意：插件路由在 lifespan 中注册（晚于此处），所以不能用 catch-all 路由，
# 否则会拦截 /api/* 请求。改用：挂载 /assets + 根路径 + 404 异常处理回退。
if os.path.isdir(FRONTEND_DIST):
    # 挂载 /assets 静态资源目录（JS/CSS/图片等）
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # 根路径返回 index.html
    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    # SPA 回退：未匹配的路径（404）返回对应静态文件或 index.html
    # 通过 exception_handler 捕获 404，这样 /api/* 的 404 不会被拦截
    # （只有真正未匹配的路径才走这里）
    @app.exception_handler(StarletteHTTPException)
    async def spa_fallback(request: Request, exc: StarletteHTTPException):
        path = request.url.path
        # API / 文档路径的 404 原样返回 JSON
        if path.startswith(("/api/", "/local_node/", "/docs", "/openapi.json", "/health")):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        # 其他 404：尝试返回对应静态文件，否则回退 index.html
        if exc.status_code == 404:
            file_path = os.path.join(FRONTEND_DIST, path.lstrip("/"))
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
else:
    # dist 不存在时，根路径返回访问端信息
    @app.get("/", tags=["root"])
    def root() -> dict:
        """根路径：访问端信息"""
        return {
            "name": "EtaMusic 访问端",
            "version": "2.0.0",
            "plugins": _loaded_plugins,
            "docs": "/docs",
            "warning": "前端未构建，请先运行 npm run build",
        }
