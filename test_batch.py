#!/usr/bin/env python3
"""
批次下載測試腳本
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.batch_downloader import BatchDownloadManager, TaskStatus
from core.constants import DOWNLOAD_TYPE_AUDIO
import time

def test_batch_download():
    """測試批次下載功能"""
    
    # 測試 URL（使用一些短音訊）
    test_urls = """
    https://www.youtube.com/watch?v=dQw4w9WgXcQ,
    https://www.youtube.com/watch?v=oHg5SJYRHA0,
    https://invalid-url-for-testing
    """
    
    # 創建批次下載管理器
    batch_manager = BatchDownloadManager(max_retries=2)
    
    # 設定回調
    def on_progress(data):
        if 'task_info' in data:
            task_info = data['task_info']
            summary = data['batch_summary']
            print(f"進度: {task_info.url} - {data.get('percentage', 0):.1f}% | 批次: {summary['current_index']}/{summary['total']}")
    
    def on_task_complete(task_info, summary):
        if task_info.status == TaskStatus.COMPLETED:
            print(f"✓ 任務完成: {task_info.downloaded_file}")
        else:
            print(f"✗ 任務失敗: {task_info.url} - {task_info.error_message}")
    
    def on_batch_complete(summary):
        print(f"\n批次下載完成！")
        print(f"總計: {summary['total']}, 成功: {summary['completed']}, 失敗: {summary['failed']}")
    
    batch_manager.progress_callback = on_progress
    batch_manager.task_complete_callback = on_task_complete
    batch_manager.batch_complete_callback = on_batch_complete
    
    # 新增批次任務
    output_path = "./test_downloads"
    os.makedirs(output_path, exist_ok=True)
    
    count = batch_manager.add_urls_from_text(
        test_urls, 
        DOWNLOAD_TYPE_AUDIO, 
        "MP3 (192kbps)", 
        output_path
    )
    
    print(f"新增了 {count} 個下載任務")
    
    # 開始下載
    if batch_manager.start_batch_download():
        print("批次下載已開始...")
        
        # 等待完成
        while batch_manager.is_running:
            time.sleep(1)
            summary = batch_manager.get_task_summary()
            print(f"狀態: {summary['current_index']}/{summary['total']} | 完成: {summary['completed']} | 失敗: {summary['failed']}")
    else:
        print("無法開始批次下載")

if __name__ == "__main__":
    test_batch_download()