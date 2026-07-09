"""asmr.one API 客户端

所有请求经配置的代理发出；代理失败时自动回退到直连。
API 文档：https://api.asmr.one
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_BASE = "https://api.asmr.one/api"

DEFAULT_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 60
STREAM_CHUNK = 64 * 1024

logger = logging.getLogger("etamusic.plugins.asmr_one")


class AsmrError(Exception):
    pass


class _SSLAdapter(HTTPAdapter):
    """自定义 HTTPAdapter，支持禁用 SSL 验证和自动重试。"""

    def __init__(self, verify_ssl: bool = True, **kwargs):
        self._verify_ssl = verify_ssl
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        if not self._verify_ssl:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


# 代理失败时自动回退到直连的异常类型
_FALLBACK_EXC = (
    requests.exceptions.SSLError,
    requests.exceptions.ProxyError,
    requests.exceptions.ConnectTimeout,
    ConnectionError,
)


class _ProxyFallbackSession:
    """Session 包装器：代理请求失败时自动切换到直连。

    对外暴露与 requests.Session 相同的接口（get/post/put/delete/head），
    内部维护两个真实 Session：一个走代理，一个直连。
    首次代理失败后自动标记，后续请求全部走直连。
    """

    def __init__(
        self,
        proxy_session: requests.Session,
        direct_session: requests.Session,
        proxy_url: Optional[str],
    ) -> None:
        self._proxy_session = proxy_session
        self._direct_session = direct_session
        self._proxy_url = proxy_url
        self._proxy_failed = False

    @property
    def _active(self) -> requests.Session:
        if self._proxy_failed or not self._proxy_url:
            return self._direct_session
        return self._proxy_session

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        try:
            return self._active.request(method, url, **kwargs)
        except _FALLBACK_EXC as e:
            if not self._proxy_failed and self._proxy_url:
                logger.warning(
                    "代理 %s 请求 %s 失败 (%s)，自动切换到直连",
                    self._proxy_url, url, e,
                )
                self._proxy_failed = True
                return self._direct_session.request(method, url, **kwargs)
            raise

    def get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self._request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self._request("DELETE", url, **kwargs)

    def head(self, url, **kwargs):
        return self._request("HEAD", url, **kwargs)

    def __getattr__(self, name):
        return getattr(self._active, name)


class AsmrClient:
    """asmr.one API 客户端

    Args:
        proxy_url: HTTP 代理地址，为空则直连
        verify_ssl: 是否验证 SSL 证书
    """

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        verify_ssl: bool = True,
    ) -> None:
        self.proxy_url = proxy_url
        self.verify_ssl = verify_ssl
        self.session = self._build_session()

    def _build_session(self) -> _ProxyFallbackSession:
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD"],
            raise_on_status=False,
        )

        def _make_session() -> requests.Session:
            s = requests.Session()
            adapter = _SSLAdapter(verify_ssl=self.verify_ssl, max_retries=retry)
            s.mount("https://", adapter)
            s.mount("http://", adapter)
            s.verify = self.verify_ssl
            return s

        proxy_sess = _make_session()
        if self.proxy_url:
            proxy_sess.proxies = {"http": self.proxy_url, "https": self.proxy_url}

        direct_sess = _make_session()

        return _ProxyFallbackSession(proxy_sess, direct_sess, self.proxy_url)

    def search(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "create_date",
        sort: str = "desc",
        subtitle: int = 0,
    ) -> dict:
        """关键词搜索作品

        subtitle: 1=仅含字幕, 0=不筛选（asmr.one 要求整数，传字符串会 400）
        """
        url = f"{API_BASE}/search/{keyword}"
        params: dict = {
            "page": page,
            "pageSize": page_size,
            "orderBy": order_by,
            "sort": sort,
        }
        if subtitle:
            params["subtitle"] = int(subtitle)
        r = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def list_works(
        self,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "create_date",
        sort: str = "desc",
        subtitle: int = 0,
    ) -> dict:
        """列出全部作品（不带关键词），支持排序

        asmr.one 的 /api/works 端点。orderBy 可选：
        create_date / dl_count / release / rate_average_2dp / review_count / price / random
        sort 可选：asc / desc
        subtitle: 1=仅含字幕, 0=不筛选
        """
        url = f"{API_BASE}/works"
        params: dict = {
            "page": page,
            "pageSize": page_size,
            "orderBy": order_by,
            "sort": sort,
        }
        if subtitle:
            params["subtitle"] = int(subtitle)
        r = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def list_by_tag(
        self,
        tag_id: int,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "create_date",
        sort: str = "desc",
        subtitle: int = 0,
    ) -> dict:
        """按标签筛选作品

        asmr.one 的 /api/tags/{id}/works 端点。
        注意：该端点 orderBy 实测不生效，结果顺序固定（按收录时间倒序）。
        subtitle: 1=仅含字幕, 0=不筛选
        """
        url = f"{API_BASE}/tags/{tag_id}/works"
        params: dict = {
            "page": page,
            "pageSize": page_size,
            "orderBy": order_by,
            "sort": sort,
        }
        if subtitle:
            params["subtitle"] = int(subtitle)
        r = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def list_by_va(
        self,
        va_id: str,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "create_date",
        sort: str = "desc",
        subtitle: int = 0,
    ) -> dict:
        """按声优筛选作品

        asmr.one 的 /api/vas/{id}/works 端点。va_id 为 UUID 字符串。
        subtitle: 1=仅含字幕, 0=不筛选
        """
        url = f"{API_BASE}/vas/{va_id}/works"
        params: dict = {
            "page": page,
            "pageSize": page_size,
            "orderBy": order_by,
            "sort": sort,
        }
        if subtitle:
            params["subtitle"] = int(subtitle)
        r = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def list_by_circle(
        self,
        circle_id: int,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "create_date",
        sort: str = "desc",
        subtitle: int = 0,
    ) -> dict:
        """按社团筛选作品

        asmr.one 的 /api/circles/{id}/works 端点。
        subtitle: 1=仅含字幕, 0=不筛选
        """
        url = f"{API_BASE}/circles/{circle_id}/works"
        params: dict = {
            "page": page,
            "pageSize": page_size,
            "orderBy": order_by,
            "sort": sort,
        }
        if subtitle:
            params["subtitle"] = int(subtitle)
        r = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def get_work(self, work_id: int) -> dict:
        """获取作品详情"""
        url = f"{API_BASE}/work/{work_id}"
        r = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def get_work_info(self, work_id: int) -> dict:
        """获取作品额外信息（workInfo）"""
        url = f"{API_BASE}/workInfo/{work_id}"
        r = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    # ===== 认证 =====

    def check_auth(self) -> dict:
        """检查登录状态 / 是否允许注册

        GET /api/auth/me 返回 {user: {loggedIn: bool, ...}, auth: bool, reg: bool}
        """
        r = self.session.get(f"{API_BASE}/auth/me", timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def check_reg_enabled(self) -> dict:
        """检查是否允许注册"""
        r = self.session.get(f"{API_BASE}/auth/reg", timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def login(self, name: str, password: str) -> dict:
        """登录

        POST /api/auth/me body {name, password} headers {Authorization: null}
        成功返回 {token: "...", user: {...}}
        """
        r = self.session.post(
            f"{API_BASE}/auth/me",
            json={"name": name, "password": password},
            headers={"Authorization": None},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            try:
                err = r.json()
            except Exception:
                err = {"error": r.text}
            raise AsmrError(err.get("error", "登录失败"))
        r.raise_for_status()
        return r.json()

    def register(self, name: str, password: str, recommender_uuid: str = None) -> dict:
        """注册"""
        body: dict = {"name": name, "password": password}
        if recommender_uuid:
            body["recommenderUuid"] = recommender_uuid
        r = self.session.post(
            f"{API_BASE}/auth/reg",
            json=body,
            headers={"Authorization": None},
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code >= 400:
            try:
                err = r.json()
            except Exception:
                err = {"error": r.text}
            raise AsmrError(err.get("error", f"注册失败 ({r.status_code})"))
        return r.json()

    def _auth_headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"} if token else {}

    # ===== 评价 / 评分 =====

    def list_reviews(
        self,
        token: str,
        order: str = "create_date",
        sort: str = "desc",
        page: int = 1,
        filter: str = "",
    ) -> dict:
        """获取我的评价列表"""
        params: dict = {"order": order, "sort": sort, "page": page}
        if filter:
            params["filter"] = filter
        r = self.session.get(
            f"{API_BASE}/review",
            params=params,
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def upsert_review(
        self,
        token: str,
        work_id: int,
        rating: int,
        review_text: str = "",
        progress: str = "",
    ) -> dict:
        """提交/更新评价"""
        r = self.session.put(
            f"{API_BASE}/review",
            json={
                "work_id": work_id,
                "rating": rating,
                "review_text": review_text,
                "progress": progress,
            },
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def delete_review(self, token: str, work_id: int) -> dict:
        """删除评价"""
        r = self.session.delete(
            f"{API_BASE}/review",
            params={"work_id": work_id},
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json() if r.text else {"ok": True}

    # ===== 播放列表 / 收藏 =====

    def list_playlists(
        self, token: str, page: int = 1, page_size: int = 20, filter_by: str = ""
    ) -> dict:
        """列出我的所有播放列表"""
        params: dict = {"page": page, "pageSize": page_size}
        if filter_by:
            params["filterBy"] = filter_by
        r = self.session.get(
            f"{API_BASE}/playlist/get-playlists",
            params=params,
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def delete_playlist(self, token: str, playlist_id) -> dict:
        """删除播放列表"""
        r = self.session.post(
            f"{API_BASE}/playlist/delete-playlist",
            json={"id": playlist_id},
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json() if r.text else {"ok": True}

    def get_default_playlist(self, token: str) -> dict:
        """获取默认收藏目标播放列表"""
        r = self.session.get(
            f"{API_BASE}/playlist/get-default-mark-target-playlist",
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def get_playlist_metadata(self, token: str, playlist_id) -> dict:
        """获取播放列表元数据（不含作品列表，asmr.one 此接口 works 字段为 null）"""
        r = self.session.get(
            f"{API_BASE}/playlist/get-playlist-metadata",
            params={"id": playlist_id},
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def list_playlist_works(
        self, token: str, playlist_id, page: int = 1, page_size: int = 50
    ) -> dict:
        """获取播放列表内的作品列表（分页）"""
        r = self.session.get(
            f"{API_BASE}/playlist/get-playlist-works",
            params={"id": playlist_id, "page": page, "pageSize": page_size},
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def get_work_in_my_playlists(
        self, token: str, work_id: int, page: int = 1, page_size: int = 50
    ) -> dict:
        """查询作品在我的播放列表中的存在状态"""
        r = self.session.get(
            f"{API_BASE}/playlist/get-work-exist-status-in-my-playlists",
            params={"workID": work_id, "page": page, "pageSize": page_size, "version": 2},
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def create_playlist(
        self,
        token: str,
        name: str,
        privacy: int = 0,
        locale: str = "zh-cn",
        description: str = "",
        works: list = None,
    ) -> dict:
        """创建播放列表"""
        r = self.session.post(
            f"{API_BASE}/playlist/create-playlist",
            json={
                "name": name,
                "privacy": privacy,
                "locale": locale,
                "description": description,
                "works": works or [],
            },
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def add_works_to_playlist(self, token: str, playlist_id, works: list) -> dict:
        """添加作品到播放列表"""
        r = self.session.post(
            f"{API_BASE}/playlist/add-works-to-playlist",
            json={"id": playlist_id, "works": works},
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def remove_works_from_playlist(self, token: str, playlist_id, works: list) -> dict:
        """从播放列表移除作品"""
        r = self.session.post(
            f"{API_BASE}/playlist/remove-works-from-playlist",
            json={"id": playlist_id, "works": works},
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    # ===== 推荐 =====

    def popular_works(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: str = "",
        subtitle: bool = False,
        token: str = None,
    ) -> dict:
        """热门作品（无需登录）"""
        body: dict = {"page": page, "pageSize": page_size}
        if keyword:
            body["keyword"] = keyword
        if subtitle:
            body["subtitle"] = subtitle
        r = self.session.post(
            f"{API_BASE}/recommender/popular",
            json=body,
            headers=self._auth_headers(token) if token else {},
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()

    def recommend_for_user(
        self,
        token: str,
        page: int = 1,
        page_size: int = 20,
        keyword: str = "",
        recommender_uuid: str = None,
        subtitle: bool = False,
    ) -> dict:
        """个性化推荐（需登录）"""
        body: dict = {"page": page, "pageSize": page_size}
        if keyword:
            body["keyword"] = keyword
        if recommender_uuid:
            body["recommenderUuid"] = recommender_uuid
        if subtitle:
            body["subtitle"] = subtitle
        r = self.session.post(
            f"{API_BASE}/recommender/recommend-for-user",
            json=body,
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json()

    def item_neighbors(self, item_id: int, token: str = None) -> dict:
        """相似作品推荐"""
        r = self.session.post(
            f"{API_BASE}/recommender/item-neighbors",
            json={"itemId": item_id},
            headers=self._auth_headers(token) if token else {},
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()
        return r.json()

    def recommender_feedback(
        self, token: str, feedback_type: str, recommender_uuid: str, item_id: int
    ) -> dict:
        """推荐反馈（type: 'like'/'dislike'/'unlike'/'undislike'）"""
        r = self.session.post(
            f"{API_BASE}/recommender/feedback",
            json={
                "type": feedback_type,
                "recommenderUuid": recommender_uuid,
                "itemId": item_id,
            },
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json() if r.text else {"ok": True}

    # ===== 标签投票 =====

    def vote_work_tag(
        self, token: str, work_id: int, tag_id: int, status: int
    ) -> dict:
        """给作品标签投票（status: 1=赞同, -1=反对, 0=取消）"""
        r = self.session.post(
            f"{API_BASE}/vote/vote-work-tag",
            json={"workID": work_id, "tagID": tag_id, "status": status},
            headers=self._auth_headers(token),
            timeout=DEFAULT_TIMEOUT,
        )
        if r.status_code == 401:
            raise AsmrError("未登录或 token 已失效")
        r.raise_for_status()
        return r.json() if r.text else {"ok": True}

    def get_tracks(self, work_id: int) -> list[dict]:
        """获取作品文件树（递归结构）"""
        url = f"{API_BASE}/tracks/{work_id}"
        r = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.json()

    def get_cover_bytes(self, work_id: int, cover_type: str = "main") -> bytes:
        """获取封面图字节"""
        url = f"{API_BASE}/cover/{work_id}.jpg"
        params = {"type": cover_type}
        r = self.session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.content

    def stream_download(self, url: str, chunk_size: int = STREAM_CHUNK):
        """流式下载，yield 字节块"""
        with self.session.get(
            url, stream=True, timeout=DOWNLOAD_TIMEOUT
        ) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    yield chunk

    def head(self, url: str) -> dict:
        """HEAD 请求，返回 headers"""
        r = self.session.head(
            url,
            allow_redirects=True,
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()
        return dict(r.headers)


def flatten_file_tree(tree: list[dict], parent_path: str = "") -> list[dict]:
    """把 asmr.one 的递归文件树拍平成路径列表

    返回 [{type, title, path, url, size, duration, ...}, ...]
    其中 type 为 audio / file / folder；folder 不出现在最终列表中（仅作为路径前缀）。
    url 仅对 audio/file 有值（mediaDownloadUrl）。
    """
    out: list[dict] = []
    for node in tree or []:
        t = node.get("type")
        title = node.get("title", "")
        path = f"{parent_path}/{title}" if parent_path else title

        if t == "folder":
            out.extend(flatten_file_tree(node.get("children", []), path))
        elif t in ("audio", "file"):
            out.append(
                {
                    "type": t,
                    "title": title,
                    "path": path,
                    "url": node.get("mediaDownloadUrl"),
                    "stream_url": node.get("mediaStreamUrl"),
                    "size": node.get("size", 0),
                    "duration": node.get("duration"),
                    "hash": node.get("hash"),
                }
            )
    return out
