"""客户端播放列表模块

存储不属于任何节点的播放列表，可跨节点添加曲目。
曲目元数据会缓存，节点失效后仍可显示（置灰）。
"""
from eta_web.client_playlists.models import ClientPlaylist, ClientPlaylistItem
from eta_web.client_playlists.routers import router

__all__ = ["ClientPlaylist", "ClientPlaylistItem", "router"]
