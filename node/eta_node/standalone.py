"""EtaMusic Node 独立运行入口

当节点不作为访问端的插件加载时，可独立运行。
独立运行时，节点服务挂载在根路径 / 而非 /local_node。
"""
from __future__ import annotations

import logging
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eta_node.plugin import bootstrap, create_local_node_app

logger = logging.getLogger("eta_node.standalone")


def create_standalone_app() -> FastAPI:
    app = FastAPI(
        title="EtaMusic Node",
        description="EtaMusic 本地音乐库节点（独立运行模式）",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
    )

    bootstrap()

    # 启动任务执行器（单线程任务队列）
    from eta_node.task_executor import start_executor

    start_executor()
    logger.info("任务执行器已启动")

    local_app = create_local_node_app()
    app.mount("/", local_app)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "mode": "standalone", "node": "local_node"}

    return app


app = create_standalone_app()


if __name__ == "__main__":
    from eta_node.config import settings

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
    )
