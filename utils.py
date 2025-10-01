"""
工具函式模組
提供各種輔助功能函式
"""

import re
import os
import platform
import subprocess
import logging
from datetime import datetime
from typing import Optional
from constants import URL_PATTERN, LOG_FILE, LOG_LEVEL


class Logger:
  """日誌管理器"""

  _instance = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
      cls._instance._setup_logger()
    return cls._instance

  def _setup_logger(self):
    """設定日誌"""
    self.logger = logging.getLogger("VideoDownloader")
    self.logger.setLevel(getattr(logging, LOG_LEVEL))

    # 檔案處理器
    fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # 控制台處理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # 格式設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    self.logger.addHandler(fh)
    self.logger.addHandler(ch)

  def info(self, message: str):
    self.logger.info(message)

  def error(self, message: str):
    self.logger.error(message)

  def warning(self, message: str):
    self.logger.warning(message)

  def debug(self, message: str):
    self.logger.debug(message)


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


def sanitize_filename(filename: str) -> str:
  """
  清理檔名，移除不合法字元

  Args:
      filename: 原始檔名

  Returns:
      str: 清理後的檔名
  """
  # 移除不合法字元
  illegal_chars = r'[<>:"/\\|?*]'
  filename = re.sub(illegal_chars, '_', filename)

  # 移除開頭結尾的空白和點
  filename = filename.strip('. ')

  # 限制長度
  if len(filename) > 200:
    name, ext = os.path.splitext(filename)
    filename = name[:200 - len(ext)] + ext

  return filename


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


def get_timestamp() -> str:
  """
  取得當前時間戳記

  Returns:
      str: 格式化的時間戳記
  """
  return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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


def convert_to_traditional_chinese(text: str) -> Optional[str]:
  """
  將簡體中文轉換為繁體中文

  Args:
      text: 要轉換的文字

  Returns:
      Optional[str]: 轉換後的文字，失敗則返回 None
  """
  try:
    import opencc
    from constants import OPENCC_CONFIG, OPENCC_FALLBACK_CONFIGS

    # 嘗試使用主要設定
    try:
      converter = opencc.OpenCC(OPENCC_CONFIG)
      return converter.convert(text)
    except:
      # 嘗試備用設定
      for config in OPENCC_FALLBACK_CONFIGS:
        try:
          converter = opencc.OpenCC(config)
          return converter.convert(text)
        except:
          continue

    Logger().warning("所有 OpenCC 設定檔都無法使用")
    return None
  except ImportError:
    Logger().warning("OpenCC 未安裝，無法進行繁簡轉換")
    return None
  except Exception as e:
    Logger().error(f"繁簡轉換失敗: {e}")
    return None


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