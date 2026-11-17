"""批次下載佇列系統。"""

import threading
from dataclasses import dataclass
from enum import Enum
from queue import Empty, Queue
from typing import Callable, Dict, List, Optional

from src.core.downloader import DownloadManager
from src.utils.logger import Logger
from src.utils.validators import parse_batch_urls, validate_download_format


class TaskStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchTaskInfo:
    url: str
    download_type: str
    format_option: str
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    error_message: str = ""
    downloaded_file: str = ""


class BatchDownloadManager:
    """以單一背景工作依序處理批次；狀態與工作生命週期由鎖保護。"""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.task_queue = Queue()
        self.tasks: List[BatchTaskInfo] = []
        self.download_manager = DownloadManager()
        self.logger = Logger()
        self._lock = threading.RLock()
        self._stop_requested = False
        self._clear_requested = False
        self._current_download_task = None
        self.is_running = False
        self.worker_thread = None
        self.current_task_index = -1
        self.progress_callback: Optional[Callable] = None
        self.task_complete_callback: Optional[Callable] = None
        self.batch_complete_callback: Optional[Callable] = None

    def add_urls_from_text(self, urls_text: str, download_type: str,
                           format_option: str, output_path: str) -> int:
        urls = parse_batch_urls(urls_text)
        validate_download_format(download_type, format_option)
        with self._lock:
            if self.is_running:
                return 0
            for url in urls:
                task_info = BatchTaskInfo(url, download_type, format_option)
                self.tasks.append(task_info)
                self.task_queue.put((task_info, output_path))
        self.logger.info(f"新增 {len(urls)} 個下載任務")
        return len(urls)

    def start_batch_download(self):
        with self._lock:
            if self.is_running or self.task_queue.empty():
                return False
            self._stop_requested = False
            self._clear_requested = False
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            try:
                self.worker_thread.start()
            except Exception:
                self.is_running = False
                raise
        self.logger.info("開始批次下載")
        return True

    def _cancel_pending_locked(self):
        while True:
            try:
                task_info, _ = self.task_queue.get_nowait()
            except Empty:
                break
            task_info.status = TaskStatus.CANCELLED

    def stop_batch_download(self):
        """要求取消；執行中操作結束後才解除忙碌狀態。"""
        with self._lock:
            if not self.is_running:
                return
            self._stop_requested = True
            self._cancel_pending_locked()
            if self._current_download_task:
                self._current_download_task.cancel()
        self.logger.info("已要求停止批次下載，等待目前任務結束")

    def clear_tasks(self):
        """執行中先取消，等工作收尾後再清除，避免與工作執行緒競爭。"""
        with self._lock:
            if self.is_running:
                self._clear_requested = True
                self.stop_batch_download()
                return False
            self._clear_locked()
        self.logger.info("清除所有任務")
        return True

    def _clear_locked(self):
        self._cancel_pending_locked()
        self.tasks.clear()
        self.current_task_index = -1

    def get_task_summary(self) -> Dict:
        with self._lock:
            return {
                'total': len(self.tasks),
                'completed': sum(t.status == TaskStatus.COMPLETED for t in self.tasks),
                'failed': sum(t.status == TaskStatus.FAILED for t in self.tasks),
                'cancelled': sum(t.status == TaskStatus.CANCELLED for t in self.tasks),
                'pending': sum(t.status == TaskStatus.PENDING for t in self.tasks),
                'downloading': sum(t.status == TaskStatus.DOWNLOADING for t in self.tasks),
                'current_index': self.current_task_index + 1 if self.current_task_index >= 0 else 0,
            }

    def _worker_loop(self):
        try:
            while True:
                with self._lock:
                    if self._stop_requested:
                        break
                    try:
                        task_info, output_path = self.task_queue.get_nowait()
                    except Empty:
                        break
                    self.current_task_index = next(i for i, task in enumerate(self.tasks) if task is task_info)
                    task_info.status = TaskStatus.DOWNLOADING
                    try:
                        task = self.download_manager.create_task(
                            url=task_info.url, download_type=task_info.download_type,
                            output_path=output_path, format_option=task_info.format_option,
                            progress_callback=lambda data: self._on_task_progress(task_info, data),
                            complete_callback=lambda path, info: self._on_task_complete(task_info, path),
                            error_callback=lambda error: self._on_task_error(task_info, error),
                        )
                    except Exception as exc:
                        task_info.status = TaskStatus.FAILED
                        task_info.error_message = str(exc)
                        self.logger.error(f"建立批次任務失敗: {exc}")
                        continue
                    self._current_download_task = task
                try:
                    success = task.execute()
                except Exception as exc:
                    success = False
                    self._on_task_error(task_info, str(exc))
                    self.logger.error(f"批次下載工作執行緒錯誤: {exc}")
                finally:
                    self.download_manager.remove_task(task)
                with self._lock:
                    self._current_download_task = None
                    if success:
                        # 完成回呼已記錄檔案；停止發生在成功之後時保留完成狀態。
                        task_info.status = TaskStatus.COMPLETED
                    elif self._stop_requested or task.is_cancelled():
                        task_info.status = TaskStatus.CANCELLED
                    elif task_info.retry_count < self.max_retries:
                        task_info.retry_count += 1
                        task_info.status = TaskStatus.PENDING
                        self.task_queue.put((task_info, output_path))
                        self.logger.info(f"任務重試 ({task_info.retry_count}/{self.max_retries}): {task_info.url}")
                    else:
                        task_info.status = TaskStatus.FAILED
                        self.logger.error(f"任務最終失敗: {task_info.url}")
        finally:
            with self._lock:
                summary = self.get_task_summary()
                summary['stopped'] = self._stop_requested
                summary['cleared'] = self._clear_requested
                if self._clear_requested:
                    self._clear_locked()
                # 在鎖內先送出完成通知，避免新批次開始後才收到舊通知。
                try:
                    if self.batch_complete_callback:
                        self.batch_complete_callback(summary)
                finally:
                    self.is_running = False
            self.logger.info("批次下載已結束")

    def _on_task_progress(self, task_info: BatchTaskInfo, data: dict):
        if self.progress_callback:
            self.progress_callback({**data, 'task_info': task_info,
                                    'batch_summary': self.get_task_summary()})

    def _on_task_complete(self, task_info: BatchTaskInfo, file_path: str):
        with self._lock:
            task_info.status = TaskStatus.COMPLETED
            task_info.downloaded_file = file_path
            summary = self.get_task_summary()
        if self.task_complete_callback:
            self.task_complete_callback(task_info, summary)
        self.logger.info(f"任務完成: {task_info.url} -> {file_path}")

    def _on_task_error(self, task_info: BatchTaskInfo, error_message: str):
        with self._lock:
            task_info.error_message = error_message
