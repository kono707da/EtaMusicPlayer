"""EtaMusic Web 访问端

不包含节点功能（扫描/流式/播放列表等），仅提供：
- 插件加载器（从外部目录发现并加载插件）
- 健康检查
- CORS 中间件
- 前端静态文件托管（生产模式）

节点功能通过加载 eta_node 等插件获得。
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

from eta_web.plugins import load_plugins
from eta_web.plugins_manager.routers import router as plugins_router, set_loaded_plugins

logger = logging.getLogger("eta_web")
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

FRONTEND_DIST = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
)

_loaded_plugins: list[str] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时加载插件"""
    global _loaded_plugins
    _loaded_plugins = load_plugins(app)
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
    title="EtaMusic Web",
    description="多节点联邦音乐系统 - 访问端（节点功能通过插件加载）",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
)

app.include_router(plugins_router)


@app.get("/health", tags=["root"])
def health() -> dict:
    """健康检查"""
    return {"status": "ok", "plugins": _loaded_plugins}


if os.path.isdir(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.exception_handler(StarletteHTTPException)
    async def spa_fallback(request: Request, exc: StarletteHTTPException):
        path = request.url.path
        plugin_prefixes = tuple(f"/{name}/" for name in _loaded_plugins)
        if path.startswith(("/api/", "/docs", "/openapi.json", "/health") + plugin_prefixes):
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        if exc.status_code == 404:
            file_path = os.path.join(FRONTEND_DIST, path.lstrip("/"))
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
else:
    @app.get("/", tags=["root"])
    def root() -> dict:
        """根路径：访问端信息"""
        return {
            "name": "EtaMusic Web",
            "version": "2.0.0",
            "plugins": _loaded_plugins,
            "docs": "/docs",
            "warning": "前端未构建，请先运行 npm run build",
        }
