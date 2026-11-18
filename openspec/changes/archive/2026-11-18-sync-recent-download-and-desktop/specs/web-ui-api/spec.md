## ADDED Requirements

### Requirement: Report playlist completion count
Web 任務完成播放清單下載時，狀態訊息 MUST 包含成功下載的檔案數；`file_path` SHALL 回報最後一個成功下載的最終檔案路徑。

#### Scenario: Poll a completed playlist task
- **Given** 播放清單任務至少成功下載一個檔案
- **When** 使用者查詢完成的任務狀態
- **Then** `message` SHALL 包含成功下載的檔案數
- **And** `file_path` SHALL 為最後一個成功檔案的最終路徑
