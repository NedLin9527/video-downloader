"""
系統工具
"""

import os
import platform
import subprocess
from utils.logger import Logger


def open_directory(path: str) -> bool:
    """
    跨平台開啟目錄
    
    Args:
        path: 目錄路徑
        
    Returns:
        bool: 是否成功開啟
    """
    try:
        if not os.path.exists(path):
            return False
        
        system = platform.system()
        
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":  # macOS
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])
        
        return True
    except Exception as e:
        Logger().error(f"開啟目錄失敗: {e}")
        return False


def format_size(size_bytes: int) -> str:
    """
    格式化檔案大小
    
    Args:
        size_bytes: 位元組大小
        
    Returns:
        str: 格式化後的大小字串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_time(seconds: int) -> str:
    """
    格式化時間
    
    Args:
        seconds: 秒數
        
    Returns:
        str: 格式化後的時間字串
    """
    if seconds < 60:
        return f"{seconds} 秒"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes} 分 {secs} 秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} 小時 {minutes} 分"


def check_disk_space(path: str, required_bytes: int) -> bool:
    """
    檢查磁碟空間是否足夠
    
    Args:
        path: 檢查的路徑
        required_bytes: 需要的位元組數
        
    Returns:
        bool: 空間是否足夠
    """
    try:
        stat = os.statvfs(path) if hasattr(os, 'statvfs') else None
        if stat:
            free_bytes = stat.f_bavail * stat.f_frsize
            return free_bytes >= required_bytes
        # Windows fallback
        import shutil
        total, used, free = shutil.disk_usage(path)
        return free >= required_bytes
    except Exception as e:
        Logger().warning(f"無法檢查磁碟空間: {e}")
        return True  # 無法檢查時假設足夠


def is_ffmpeg_installed() -> bool:
    """
    檢查 FFmpeg 是否已安裝
    
    Returns:
        bool: FFmpeg 是否可用
    """
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False