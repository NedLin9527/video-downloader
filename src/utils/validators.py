"""
驗證工具
"""

import re
from core.constants import URL_PATTERN


def validate_url(url: str) -> bool:
    """
    驗證 URL 格式
    
    Args:
        url: 要驗證的 URL
        
    Returns:
        bool: URL 是否有效
    """
    if not url or not url.strip():
        return False
    return bool(re.match(URL_PATTERN, url.strip()))