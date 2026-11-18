"""
下載核心模組
"""

import os
import shutil
import yt_dlp
from typing import Dict, Callable, Optional
from threading import Event

from src.core.constants import (
    DOWNLOAD_TYPE_VIDEO,
    DOWNLOAD_TYPE_AUDIO,
    VIDEO_FORMATS,
    AUDIO_FORMATS,
    ERROR_MESSAGES,
    DOWNLOAD_TIMEOUT,
    RETRY_ATTEMPTS,
)
from src.utils.logger import Logger
from src.utils.file_utils import sanitize_filename, convert_to_traditional_chinese
from src.utils.validators import validate_download_format, validate_url
from src.utils.system_utils import check_disk_space


def get_js_runtimes() -> Dict[str, Dict[str, str]]:
    """回傳系統中可供 yt-dlp 使用的 JavaScript runtime。

    近期 YouTube 的驗證程序需要 JavaScript runtime。yt-dlp 預設只會啟用
    Deno；即使系統已安裝 Node.js，也必須明確傳入設定才會使用。
    """
    runtimes = {}
    for runtime in ("deno", "node", "quickjs", "bun"):
        runtime_path = shutil.which(runtime)
        if runtime_path:
            runtimes[runtime] = {"path": runtime_path}

    # Chocolatey 的 Node.js MSI 會安裝到這裡。PyCharm 在 Node 安裝前就已
    # 啟動時，程序繼承的 PATH 還沒有更新；直接使用標準安裝位置即可。
    if "node" not in runtimes and os.name == "nt":
        node_candidates = (
            os.path.join(os.environ.get("ProgramFiles", r"C:\\Program Files"), "nodejs", "node.exe"),
            os.path.join(os.environ.get("ProgramW6432", r"C:\\Program Files"), "nodejs", "node.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs", "node.exe"),
        )
        for node_path in node_candidates:
            if os.path.isfile(node_path):
                runtimes["node"] = {"path": node_path}
                break
    return runtimes


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
        self.downloaded_files = []
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
            'post_hooks': [self._record_final_path],
            'socket_timeout': DOWNLOAD_TIMEOUT,
            'retries': RETRY_ATTEMPTS,
            'fragment_retries': RETRY_ATTEMPTS,
            # YouTube 的媒體網址有時效。不要從舊 .part 檔以過期網址續傳，
            # 否則很容易收到 HTTP 403；完整下載檔仍不會被覆寫。
            'continuedl': False,
            'quiet': False,
            'no_warnings': False,
        }

        js_runtimes = get_js_runtimes()
        if js_runtimes:
            base_options['js_runtimes'] = js_runtimes
        else:
            self.logger.warning(
                "找不到 JavaScript runtime（Node.js 或 Deno）。"
                "YouTube 可能無法取得所有格式，建議安裝 Node.js LTS。"
            )

        if self.download_type == DOWNLOAD_TYPE_VIDEO:
            video_format = VIDEO_FORMATS[self.format_option]
            base_options.update({
                'format': video_format,
                'merge_output_format': 'mp4',
            })

        elif self.download_type == DOWNLOAD_TYPE_AUDIO:
            audio_config = AUDIO_FORMATS[self.format_option]
            base_options.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_config['codec'],
                    'preferredquality': audio_config['quality'],
                }],
            })

        return base_options

    def _record_final_path(self, file_path: str):
        """記錄 yt-dlp 完成合併、轉檔及移動後的路徑。"""
        self.downloaded_file = file_path
        self.downloaded_files.append(file_path)

    def execute(self) -> bool:
        """執行下載任務"""
        self.downloaded_file = None
        self.downloaded_files = []
        try:
            if self.is_cancelled():
                return False
            if not validate_url(self.url):
                raise ValueError(ERROR_MESSAGES['invalid_url'])
            validate_download_format(self.download_type, self.format_option)
            self.url = self.url.strip()

            os.makedirs(self.output_path, exist_ok=True)
            options = self._get_ydl_options()

            with yt_dlp.YoutubeDL(options) as ydl:
                if self.is_cancelled():
                    return False
                raw_info = ydl.extract_info(self.url, download=False, process=False)
                if not raw_info:
                    raise RuntimeError("無法取得影片資訊")
                is_playlist = raw_info.get('_type') in {'playlist', 'multi_video', 'compat_list'}

                if is_playlist:
                    # Python API 預設遇到不可用項目會中止；播放清單應繼續處理其他項目。
                    ydl.params['ignoreerrors'] = True
                    self.info = ydl.process_ie_result(raw_info, download=True)
                else:
                    preview = ydl.process_ie_result(raw_info, download=False)
                    if not preview:
                        raise RuntimeError("無法取得影片資訊")
                    estimated_size = preview.get('filesize', 0) or preview.get('filesize_approx') or 0
                    if estimated_size > 0 and not check_disk_space(self.output_path, estimated_size * 1.5):
                        raise Exception(ERROR_MESSAGES['disk_space_error'])
                    if self.is_cancelled():
                        return False
                    self.info = ydl.extract_info(self.url, download=True)

                if self.is_cancelled():
                    return False
                if not self.downloaded_files:
                    raise RuntimeError("播放清單沒有成功下載的檔案" if is_playlist else "找不到下載後的最終檔案")

                converted_files = []
                for file_path in self.downloaded_files:
                    if not os.path.isfile(file_path):
                        raise RuntimeError(f"找不到下載後的最終檔案: {file_path}")
                    self.downloaded_file = file_path
                    self._convert_filename()
                    converted_files.append(self.downloaded_file)
                self.downloaded_files = converted_files
                self.downloaded_file = converted_files[-1]
                self.info = self.info or {}

                if is_playlist:
                    self.info['downloaded_files'] = list(converted_files)
                    self.logger.info(f"播放清單下載完成：{len(converted_files)} 個檔案")

                self.logger.info(f"下載完成: {self.downloaded_file}")
                if self.complete_callback:
                    self.complete_callback(self.downloaded_file, self.info)
                return True

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

        # 檢查是否啟用自動轉換
        from src.core.config import ConfigManager
        config = ConfigManager()
        if not config.get("auto_convert_filename", True):
            return

        try:
            base_name = os.path.basename(self.downloaded_file)
            converted_name = convert_to_traditional_chinese(base_name)

            if converted_name and converted_name != base_name:
                converted_name = sanitize_filename(converted_name)
                new_path = os.path.join(
                    os.path.dirname(self.downloaded_file),
                    converted_name
                )

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
        """建立下載任務"""
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
