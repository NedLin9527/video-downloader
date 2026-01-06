# 批次下載使用範例

## 基本用法

### 1. 準備 URL 清單

將多個 URL 用逗號分隔，可以跨行輸入：

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ,
https://www.youtube.com/watch?v=oHg5SJYRHA0,
https://www.bilibili.com/video/BV1xx411c7mu,
https://www.youtube.com/watch?v=9bZkp7q19f0
```

### 2. 程式化使用

```python
from src.core.batch_downloader import BatchDownloadManager
from src.core.constants import DOWNLOAD_TYPE_AUDIO

# 創建批次下載管理器
batch_manager = BatchDownloadManager(max_retries=3)

# 設定回調函數
def on_progress(data):
    task_info = data['task_info']
    summary = data['batch_summary']
    print(f"進度: {task_info.url} - {data.get('percentage', 0):.1f}%")
    print(f"批次: {summary['current_index']}/{summary['total']}")

def on_task_complete(task_info, summary):
    if task_info.status.value == "completed":
        print(f"✓ 完成: {task_info.downloaded_file}")
    else:
        print(f"✗ 失敗: {task_info.url}")

def on_batch_complete(summary):
    print(f"批次完成！成功: {summary['completed']}, 失敗: {summary['failed']}")

# 設定回調
batch_manager.progress_callback = on_progress
batch_manager.task_complete_callback = on_task_complete
batch_manager.batch_complete_callback = on_batch_complete

# 新增批次任務
urls_text = """
https://www.youtube.com/watch?v=example1,
https://www.youtube.com/watch?v=example2
"""

count = batch_manager.add_urls_from_text(
    urls_text, 
    DOWNLOAD_TYPE_AUDIO, 
    "MP3 (192kbps)", 
    "./downloads"
)

# 開始下載
if batch_manager.start_batch_download():
    print(f"開始批次下載 {count} 個任務")
    
    # 等待完成
    while batch_manager.is_running:
        time.sleep(1)
```

## 重試機制

- 每個失敗的任務會自動重試最多 3 次
- 重試時會保留原始的格式設定和檔名轉換設定
- 最終失敗的任務會在日誌中標記，不影響其他任務

## 檔名轉換

批次下載會自動應用檔名簡轉繁功能：

- 下載完成後自動將簡體中文檔名轉為繁體
- 避免檔名衝突（自動加數字後綴）
- 保留原始副檔名

## 進度監控

批次下載提供詳細的進度資訊：

```python
summary = batch_manager.get_task_summary()
print(f"總計: {summary['total']}")
print(f"完成: {summary['completed']}")
print(f"失敗: {summary['failed']}")
print(f"等待: {summary['pending']}")
print(f"下載中: {summary['downloading']}")
print(f"當前: {summary['current_index']}")
```

## 錯誤處理

常見錯誤及處理方式：

1. **無效 URL**: 會跳過並記錄在日誌中
2. **網路錯誤**: 會自動重試
3. **格式不支援**: 會跳過該任務
4. **磁碟空間不足**: 會停止下載並報錯

## 最佳實踐

1. **URL 準備**: 確保 URL 格式正確，避免包含特殊字符
2. **批次大小**: 建議每批不超過 50 個 URL，避免記憶體過度使用
3. **網路狀況**: 在網路不穩定時可以增加重試次數
4. **儲存空間**: 確保有足夠的磁碟空間
5. **格式選擇**: 音訊下載通常比影片下載更穩定快速