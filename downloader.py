"""
下載核心模組
處理影片/音訊下載邏輯
"""

import os
import yt_dlp
from typing import Dict, Callable, Optional
from threading import Event
from constants import (
  DOWNLOAD_TYPE_VIDEO,
  DOWNLOAD_TYPE_AUDIO,
  VIDEO_FORMATS,
  AUDIO_FORMATS,
  ERROR_MESSAGES,
  DOWNLOAD_TIMEOUT,
  RETRY_ATTEMPTS,
)
from utils import (
  Logger,
  sanitize_filename,
  validate_url,
  check_disk_space,
  convert_to_traditional_chinese,
)


class DownloadTask:
  """下載任務類"""

  def __init__(
      self,
      url: str,
      download_type: str,
      output_path: str,
      format_option: str,
      progress_callback: Optional[Callable] = None,
      complete_callback: Optional[Callable] = None,
      error_callback: Optional[Callable] = None,
  ):
    self.url = url
    self.download_type = download_type
    self.output_path = output_path
    self.format_option = format_option
    self.progress_callback = progress_callback
    self.complete_callback = complete_callback
    self.error_callback = error_callback

    self.cancel_event = Event()
    self.logger = Logger()
    self.downloaded_file = None
    self.info = None

  def cancel(self):
    """取消下載"""
    self.cancel_event.set()
    self.logger.info(f"取消下載: {self.url}")

  def is_cancelled(self) -> bool:
    """檢查是否已取消"""
    return self.cancel_event.is_set()

  def _progress_hook(self, d: Dict):
    """下載進度回調"""
    if self.is_cancelled():
      raise Exception("下載已被使用者取消")

    if self.progress_callback:
      status = d.get('status')

      if status == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        speed = d.get('speed', 0)
        eta = d.get('eta', 0)

        progress_data = {
          'status': 'downloading',
          'downloaded': downloaded,
          'total': total,
          'percentage': (downloaded / total * 100) if total > 0 else 0,
          'speed': speed,
          'eta': eta,
        }
        self.progress_callback(progress_data)

      elif status == 'finished':
        self.progress_callback({'status': 'finished'})

  def _get_ydl_options(self) -> Dict:
    """取得 yt-dlp 選項"""
    base_options = {
      'outtmpl': os.path.join(self.output_path, '%(title)s.%(ext)s'),
      'progress_hooks': [self._progress_hook],
      'socket_timeout': DOWNLOAD_TIMEOUT,
      'retries': RETRY_ATTEMPTS,
      'quiet': False,
      'no_warnings': False,
    }

    if self.download_type == DOWNLOAD_TYPE_VIDEO:
      video_format = VIDEO_FORMATS.get(self.format_option,
                                       VIDEO_FORMATS["最高畫質"])
      base_options.update({
        'format': video_format,
        'merge_output_format': 'mp4',
      })

    elif self.download_type == DOWNLOAD_TYPE_AUDIO:
      audio_config = AUDIO_FORMATS.get(
          self.format_option,
          AUDIO_FORMATS["MP3 (192kbps)"]
      )
      base_options.update({
        'format': 'bestaudio/best',
        'postprocessors': [{
          'key': 'FFmpegExtractAudio',
          'preferredcodec': audio_config['codec'],
          'preferredquality': audio_config['quality'],
        }],
      })

    return base_options

  def execute(self) -> bool:
    """
    執行下載任務

    Returns:
        bool: 是否成功
    """
    try:
      # 驗證 URL
      if not validate_url(self.url):
        raise ValueError(ERROR_MESSAGES['invalid_url'])

      # 確保輸出目錄存在
      os.makedirs(self.output_path, exist_ok=True)

      # 取得下載選項
      options = self._get_ydl_options()

      # 執行下載
      with yt_dlp.YoutubeDL(options) as ydl:
        # 先取得資訊
        self.info = ydl.extract_info(self.url, download=False)

        # 檢查磁碟空間
        estimated_size = self.info.get('filesize', 0) or self.info.get(
          'filesize_approx', 0)
        if estimated_size > 0:
          if not check_disk_space(self.output_path, estimated_size * 1.5):
            raise Exception(ERROR_MESSAGES['disk_space_error'])

        # 開始下載
        if not self.is_cancelled():
          self.info = ydl.extract_info(self.url, download=True)
          self.downloaded_file = ydl.prepare_filename(self.info)

          # 嘗試轉換檔名為繁體中文
          self._convert_filename()

          self.logger.info(f"下載完成: {self.downloaded_file}")

          if self.complete_callback:
            self.complete_callback(self.downloaded_file, self.info)

          return True

      return False

    except Exception as e:
      error_msg = str(e)
      self.logger.error(f"下載失敗: {error_msg}")

      if self.error_callback:
        self.error_callback(error_msg)

      return False

  def _convert_filename(self):
    """轉換檔名為繁體中文"""
    if not self.downloaded_file or not os.path.exists(self.downloaded_file):
      return

    try:
      base_name = os.path.basename(self.downloaded_file)
      converted_name = convert_to_traditional_chinese(base_name)

      if converted_name and converted_name != base_name:
        # 清理檔名
        converted_name = sanitize_filename(converted_name)
        new_path = os.path.join(
            os.path.dirname(self.downloaded_file),
            converted_name
        )

        # 避免檔名衝突
        counter = 1
        original_new_path = new_path
        while os.path.exists(new_path):
          name, ext = os.path.splitext(original_new_path)
          new_path = f"{name}_{counter}{ext}"
          counter += 1

        os.rename(self.downloaded_file, new_path)
        self.downloaded_file = new_path
        self.logger.info(f"檔名已轉換為繁體: {converted_name}")

    except Exception as e:
      self.logger.warning(f"檔名轉換失敗（非致命）: {e}")


class DownloadManager:
  """下載管理器"""

  def __init__(self):
    self.active_tasks: Dict[str, DownloadTask] = {}
    self.logger = Logger()

  def create_task(
      self,
      url: str,
      download_type: str,
      output_path: str,
      format_option: str,
      **callbacks
  ) -> DownloadTask:
    """
    建立下載任務

    Args:
        url: 下載 URL
        download_type: 下載類型 (video/audio)
        output_path: 輸出路徑
        format_option: 格式選項
        **callbacks: 回調函式

    Returns:
        DownloadTask: 下載任務物件
    """
    task = DownloadTask(
        url=url,
        download_type=download_type,
        output_path=output_path,
        format_option=format_option,
        progress_callback=callbacks.get('progress_callback'),
        complete_callback=callbacks.get('complete_callback'),
        error_callback=callbacks.get('error_callback'),
    )

    task_id = f"{download_type}_{id(task)}"
    self.active_tasks[task_id] = task

    return task

  def remove_task(self, task: DownloadTask):
    """移除任務"""
    task_id = f"{task.download_type}_{id(task)}"
    if task_id in self.active_tasks:
      del self.active_tasks[task_id]

  def cancel_all(self):
    """取消所有任務"""
    for task in self.active_tasks.values():
      task.cancel()
    self.active_tasks.clear()

  def get_active_count(self) -> int:
    """取得活躍任務數量"""
    return len(self.active_tasks)