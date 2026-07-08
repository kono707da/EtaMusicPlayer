"""B站 API 客户端：获取视频信息、音频流地址、封面等"""
from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger("etamusic.plugins.bili_audio")

_API_BASE = "https://api.bilibili.com"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com",
}

AUDIO_QUALITY_MAP = {
    30216: "64kbps",
    30232: "132kbps",
    30280: "192kbps",
    30250: "Dolby Atmos",
    30251: "Hi-Res无损",
}

_BVID_RE = re.compile(r"(BV[\w]{10})")
_AVID_RE = re.compile(r"av(\d+)", re.IGNORECASE)


class BiliClient:
    def __init__(self, sessdata: Optional[str] = None, proxy_url: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update(_HEADERS)
        if sessdata:
            self.session.cookies.set("SESSDATA", sessdata, domain=".bilibili.com")
        if proxy_url:
            self.session.proxies = {"http": proxy_url, "https": proxy_url}
        self.sessdata = sessdata

    def parse_bvid(self, url_or_bvid: str) -> Optional[str]:
        m = _BVID_RE.search(url_or_bvid)
        if m:
            return m.group(1)
        m = _AVID_RE.search(url_or_bvid)
        if m:
            return self._avid_to_bvid(int(m.group(1)))
        return None

    def _avid_to_bvid(self, aid: int) -> Optional[str]:
        try:
            resp = self.session.get(
                f"{_API_BASE}/x/web-interface/view",
                params={"aid": aid},
                timeout=15,
            )
            data = resp.json()
            if data.get("code") == 0:
                return data["data"]["bvid"]
        except Exception as e:
            logger.warning("avid→bvid 转换失败: %s", e)
        return None

    def get_video_info(self, bvid: str) -> dict:
        resp = self.session.get(
            f"{_API_BASE}/x/web-interface/view",
            params={"bvid": bvid},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ValueError(f"B站API错误: {data.get('message', 'unknown')}")
        return data["data"]

    def get_pages(self, bvid: str) -> list[dict]:
        info = self.get_video_info(bvid)
        return info.get("pages", [])

    def get_audio_url(
        self, bvid: str, cid: int, quality: int = 30280
    ) -> tuple[Optional[str], Optional[str]]:
        resp = self.session.get(
            f"{_API_BASE}/x/player/playurl",
            params={
                "bvid": bvid,
                "cid": cid,
                "qn": 0,
                "fnver": 0,
                "fnval": 16,
                "fourk": 1,
                "otype": "json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ValueError(f"获取播放地址失败: {data.get('message', 'unknown')}")

        resp_data = data.get("data", {})
        dash = resp_data.get("dash", {})
        if dash:
            audio_streams = dash.get("audio", [])
            target = None
            for s in audio_streams:
                if s.get("id") == quality:
                    target = s
                    break
            if target is None and audio_streams:
                target = audio_streams[0]

            audio_url = target.get("baseUrl") or target.get("base_url") if target else None
            audio_mime = target.get("mimeType", "audio/mp4") if target else "audio/mp4"
            return audio_url, audio_mime

        durl_list = resp_data.get("durl", [])
        if durl_list:
            video_url = durl_list[0].get("url")
            if video_url:
                return video_url, "video/mp4"

        return None, None

    def download_audio_stream(
        self, audio_url: str, output_path: str, on_progress=None
    ) -> int:
        headers = {**_HEADERS, "Referer": "https://www.bilibili.com"}
        resp = self.session.get(audio_url, headers=headers, stream=True, timeout=60)
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        done = 0
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
                done += len(chunk)
                if on_progress:
                    on_progress(done, total)
        return done

    def download_cover(self, cover_url: str) -> Optional[bytes]:
        try:
            resp = self.session.get(cover_url, timeout=30)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            logger.warning("下载封面失败: %s", e)
            return None

    def get_upper_info(self, mid: int) -> Optional[dict]:
        try:
            resp = self.session.get(
                f"{_API_BASE}/x/web-interface/card",
                params={"mid": mid},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                card = data["data"].get("card", {})
                return {"name": card.get("name", ""), "mid": card.get("mid", mid)}
        except Exception as e:
            logger.warning("获取UP主信息失败: %s", e)
        return None

    def get_collection_videos(self, mid: int, season_id: int, page_num: int = 1, page_size: int = 30) -> dict:
        resp = self.session.get(
            f"{_API_BASE}/x/polymer/web-space/seasons_archives_list",
            params={
                "mid": mid,
                "season_id": season_id,
                "sort_reverse": "false",
                "page_num": page_num,
                "page_size": page_size,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            raise ValueError(f"获取合集视频列表失败: {data.get('message', 'unknown')}")
        return data.get("data", {})

    def parse_collection_url(self, url: str) -> Optional[tuple]:
        m = re.search(r"space\.bilibili\.com/(\d+)/lists/(\d+)", url)
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.search(r"space\.bilibili\.com/(\d+)/channel/seriesdetail\?sid=(\d+)", url)
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.search(r"space\.bilibili\.com/(\d+)/channel/collectiondetail\?sid=(\d+)", url)
        if m:
            return int(m.group(1)), int(m.group(2))
        return None
