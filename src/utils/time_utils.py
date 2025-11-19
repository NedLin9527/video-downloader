"""
時間工具
"""

from datetime import datetime


def get_timestamp() -> str:
    """
    取得當前時間戳記
    
    Returns:
        str: 格式化的時間戳記
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")