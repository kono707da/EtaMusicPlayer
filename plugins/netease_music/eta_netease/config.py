"""网易云插件配置常量"""
from __future__ import annotations

# 域名
DOMAIN = 'https://music.163.com'
API_DOMAIN = 'https://interface.music.163.com'

# PC 客户端伪装配置（参照 NeteaseCloudMusicApiEnhanced osMap.pc）
OS_PC = {
    'os': 'pc',
    'appver': '3.1.17.204416',
    'osver': 'Microsoft-Windows-10-Professional-build-19045-64bit',
    'channel': 'netease',
}

# PC 客户端 UA
UA_API_PC = (
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Safari/537.36 Chrome/91.0.4472.164 NeteaseMusicDesktop/3.0.18.203152'
)
UA_WEAPI_PC = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0'
)

# 版本号
VERSION_CODE = '140'

# 账号数据目录（由 plugin.py 初始化时设置）
ACCOUNTS_DIR: str = ''
