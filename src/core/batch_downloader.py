"""
批次下載佇列系統
"""

import threading
import time
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
from enum import Enum
from queue import Queue

from core.downloader import DownloadTask, DownloadManager
from utils.logger import Logger


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchTaskInfo:
    """批次任務資訊"""
    url: str
    download_type: str
    format_option: str
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    error_message: str = ""
    downloaded_file: str = ""


class BatchDownloadManager:
    """批次下載管理器"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.task_queue = Queue()
        self.tasks: List[BatchTaskInfo] = []
        self.download_manager = DownloadManager()
        self.logger = Logger()
        
        self.is_running = False
        self.worker_thread = None
        self.current_task_index = -1
        
        # 回調函數
        self.progress_callback: Optional[Callable] = None
        self.task_complete_callback: Optional[Callable] = None
        self.batch_complete_callback: Optional[Callable] = None
        
    def add_urls_from_text(self, urls_text: str, download_type: str, 
                          format_option: str, output_path: str) -> int:
        """從文字新增URL清單（逗號分隔）"""
        urls = [url.strip() for url in urls_text.split(',') if url.strip()]
        
        for url in urls:
            task_info = BatchTaskInfo(
                url=url,
                download_type=download_type,
                format_option=format_option
            )
            self.tasks.append(task_info)
            self.task_queue.put((task_info, output_path))
            
        self.logger.info(f"新增 {len(urls)} 個下載任務")
        return len(urls)
    
    def start_batch_download(self):
        """開始批次下載"""
        if self.is_running:
            return False
            
        if not self.tasks:
            return False
            
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        self.logger.info("開始批次下載")
        return True
    
    def stop_batch_download(self):
        """停止批次下載"""
        self.is_running = False
        
        # 取消當前任務
        if hasattr(self, '_current_download_task') and self._current_download_task:
            self._current_download_task.cancel()
            
        self.logger.info("停止批次下載")
    
    def clear_tasks(self):
        """清除所有任務"""
        self.stop_batch_download()
        self.tasks.clear()
        
        # 清空佇列
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except:
                break
                
        self.current_task_index = -1
        self.logger.info("清除所有任務")
    
    def get_task_summary(self) -> Dict:
        """取得任務摘要"""
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task.status == TaskStatus.COMPLETED)
        failed = sum(1 for task in self.tasks if task.status == TaskStatus.FAILED)
        pending = sum(1 for task in self.tasks if task.status == TaskStatus.PENDING)
        downloading = sum(1 for task in self.tasks if task.status == TaskStatus.DOWNLOADING)
        
        return {
            'total': total,
            'completed': completed,
            'failed': failed,
            'pending': pending,
            'downloading': downloading,
            'current_index': self.current_task_index + 1 if self.current_task_index >= 0 else 0
        }
    
    def _worker_loop(self):
        """工作執行緒主迴圈"""
        while self.is_running and not self.task_queue.empty():
            try:
                task_info, output_path = self.task_queue.get(timeout=1)
                self.current_task_index = self.tasks.index(task_info)
                
                if task_info.status == TaskStatus.CANCELLED:
                    continue
                    
                self._process_single_task(task_info, output_path)
                
            except Exception as e:
                self.logger.error(f"批次下載工作執行緒錯誤: {e}")
                
        self.is_running = False
        
        # 批次完成回調
        if self.batch_complete_callback:
            self.batch_complete_callback(self.get_task_summary())
            
        self.logger.info("批次下載完成")
    
    def _process_single_task(self, task_info: BatchTaskInfo, output_path: str):
        """處理單一任務"""
        task_info.status = TaskStatus.DOWNLOADING
        
        # 建立下載任務
        self._current_download_task = self.download_manager.create_task(
            url=task_info.url,
            download_type=task_info.download_type,
            output_path=output_path,
            format_option=task_info.format_option,
            progress_callback=lambda data: self._on_task_progress(task_info, data),
            complete_callback=lambda file_path, info: self._on_task_complete(task_info, file_path),
            error_callback=lambda error: self._on_task_error(task_info, error)
        )
        
        # 執行下載
        success = self._current_download_task.execute()
        
        # 清理
        self.download_manager.remove_task(self._current_download_task)
        self._current_download_task = None
        
        # 如果失敗且未達重試上限，重新加入佇列
        if not success and task_info.retry_count < self.max_retries and self.is_running:
            task_info.retry_count += 1
            task_info.status = TaskStatus.PENDING
            self.task_queue.put((task_info, output_path))
            self.logger.info(f"任務重試 ({task_info.retry_count}/{self.max_retries}): {task_info.url}")
        elif not success:
            task_info.status = TaskStatus.FAILED
            self.logger.error(f"任務最終失敗: {task_info.url}")
    
    def _on_task_progress(self, task_info: BatchTaskInfo, data: dict):
        """任務進度回調"""
        if self.progress_callback:
            # 加入任務資訊
            data['task_info'] = task_info
            data['batch_summary'] = self.get_task_summary()
            self.progress_callback(data)
    
    def _on_task_complete(self, task_info: BatchTaskInfo, file_path: str):
        """任務完成回調"""
        task_info.status = TaskStatus.COMPLETED
        task_info.downloaded_file = file_path
        
        if self.task_complete_callback:
            self.task_complete_callback(task_info, self.get_task_summary())
            
        self.logger.info(f"任務完成: {task_info.url} -> {file_path}")
    
    def _on_task_error(self, task_info: BatchTaskInfo, error_message: str):
        """任務錯誤回調"""
        task_info.error_message = error_message
        # 狀態會在 _process_single_task 中根據重試情況設定