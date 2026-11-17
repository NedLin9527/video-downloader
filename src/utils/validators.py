"""下載輸入驗證，不進行網路連線或站點支援檢查。"""

import ipaddress
import re
from urllib.parse import urlsplit

from src.core.constants import AUDIO_FORMATS, DOWNLOAD_TYPE_AUDIO, DOWNLOAD_TYPE_VIDEO, VIDEO_FORMATS


def validate_url(url: str) -> bool:
    """檢查完整 HTTP(S) URL 的語法，允許 DNS 名稱、IPv4、IPv6 與連接埠。"""
    if not isinstance(url, str):
        return False
    value = url.strip()
    if not value or any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in value):
        return False
    if '\\' in value or re.search(r'%(?![0-9a-fA-F]{2})', value):
        return False
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {'http', 'https'} or not parsed.netloc:
            return False
        authority = parsed.netloc.rsplit('@', 1)[-1]
        if parsed.netloc.count('@') > 1:
            return False
        if authority.startswith('['):
            close = authority.find(']')
            if close < 0 or (authority[close + 1:] and not authority[close + 1:].startswith(':')):
                return False
        host = parsed.hostname
        port = parsed.port  # 同時檢查連接埠是否為 0–65535 的整數
        if not host or port == 0 or parsed.netloc.endswith(':'):
            return False
        try:
            ipaddress.ip_address(host)
            return True
        except ValueError:
            pass
        if ':' in host or re.fullmatch(r'[0-9.]+', host):
            return False
        ascii_host = (host[:-1] if host.endswith('.') else host).encode('idna').decode('ascii')
        if not ascii_host or len(ascii_host) > 253:
            return False
        return all(re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?', label)
                   for label in ascii_host.split('.'))
    except (ValueError, UnicodeError):
        return False


def validate_download_format(download_type: str, format_option: str) -> None:
    """類型或格式無效時提出可供介面顯示的錯誤。"""
    formats = {DOWNLOAD_TYPE_VIDEO: VIDEO_FORMATS, DOWNLOAD_TYPE_AUDIO: AUDIO_FORMATS}
    if download_type not in formats:
        raise ValueError('下載類型必須為 video 或 audio')
    if format_option not in formats[download_type]:
        raise ValueError('格式選項不支援或與下載類型不相符')


def parse_batch_urls(urls_text: str) -> list[str]:
    """解析逗號分隔清單；任一非空項目無效即拒絕整批。"""
    if not isinstance(urls_text, str):
        raise ValueError('請輸入批次 URL 清單')
    urls = [url.strip() for url in urls_text.split(',') if url.strip()]
    if not urls:
        raise ValueError('請輸入批次 URL 清單')
    invalid = [str(index) for index, url in enumerate(urls, 1) if not validate_url(url)]
    if invalid:
        raise ValueError(f"批次 URL 第 {', '.join(invalid)} 項格式無效，請修正後再試")
    return urls
