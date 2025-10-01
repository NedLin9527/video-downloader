"""
設定管理模組
負責讀取、儲存、管理應用程式設定
"""

import json
import os
from typing import Dict, Any
from constants import (
  CONFIG_FILE,
  DEFAULT_DOWNLOAD_PATH,
  VIDEO_FORMATS,
  AUDIO_FORMATS,
)


class ConfigManager:
  """設定管理器"""

  def __init__(self, config_file: str = CONFIG_FILE):
    self.config_file = config_file
    self.config = self.load_config()

  def load_config(self) -> Dict[str, Any]:
    """載入設定檔"""
    if os.path.exists(self.config_file):
      try:
        with open(self.config_file, 'r', encoding='utf-8') as f:
          return json.load(f)
      except Exception as e:
        print(f"載入設定檔失敗: {e}")
        return self.get_default_config()
    return self.get_default_config()

  def save_config(self) -> bool:
    """儲存設定檔"""
    try:
      with open(self.config_file, 'w', encoding='utf-8') as f:
        json.dump(self.config, f, ensure_ascii=False, indent=2)
      return True
    except Exception as e:
      print(f"儲存設定檔失敗: {e}")
      return False

  def get_default_config(self) -> Dict[str, Any]:
    """取得預設設定"""
    return {
      "download_path": DEFAULT_DOWNLOAD_PATH,
      "video_format": list(VIDEO_FORMATS.keys())[0],
      "audio_format": list(AUDIO_FORMATS.keys())[0],
      "auto_convert_filename": True,
      "auto_open_directory": True,
      "theme": "light",
      "max_concurrent_downloads": 3,
      "proxy": "",
      "language": "zh_TW",
    }

  def get(self, key: str, default: Any = None) -> Any:
    """取得設定值"""
    return self.config.get(key, default)

  def set(self, key: str, value: Any) -> None:
    """設定值"""
    self.config[key] = value
    self.save_config()

  def update(self, updates: Dict[str, Any]) -> None:
    """批次更新設定"""
    self.config.update(updates)
    self.save_config()

  def reset(self) -> None:
    """重置為預設設定"""
    self.config = self.get_default_config()
    self.save_config()

  def get_download_path(self) -> str:
    """取得下載路徑"""
    path = self.get("download_path", DEFAULT_DOWNLOAD_PATH)
    if not os.path.exists(path):
      os.makedirs(path, exist_ok=True)
    return path

  def set_download_path(self, path: str) -> None:
    """設定下載路徑"""
    if os.path.exists(path) and os.path.isdir(path):
      self.set("download_path", path)
    else:
      raise ValueError(f"路徑不存在或非目錄: {path}")