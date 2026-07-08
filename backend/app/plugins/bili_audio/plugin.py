PLUGIN_META = {
    "name": "bili_audio",
    "description": "从B站视频提取音频，自动写入标签并入库到本地节点",
    "version": "1.0.0",
    "author": "EtaMusic",
}


def register(app) -> None:
    from app.plugins.bili_audio.database import init_db
    from app.plugins.bili_audio.routers import router

    init_db()
    app.include_router(router)
    import logging
    logger = logging.getLogger("etamusic.plugins.bili_audio")
    logger.info("bili_audio 插件已加载，路由前缀 /api/bili")
