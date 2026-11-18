## ADDED Requirements

### Requirement: Handle playlist entries independently
播放清單包含不可用項目時，系統 MUST 繼續處理其他項目。至少一個檔案成功完成且最終檔案存在時，任務 SHALL 回報成功，並在完成資訊中提供轉換後的 `downloaded_files` 清單；沒有成功檔案時 SHALL 回報失敗。

#### Scenario: Playlist contains an unavailable entry
- **Given** 播放清單包含不可用項目及可成功下載的項目
- **When** 任務執行完成
- **Then** 系統 SHALL 繼續處理可用項目
- **And** 完成資訊 SHALL 包含成功下載的最終檔案路徑

#### Scenario: No playlist files succeed
- **Given** 播放清單沒有成功下載的檔案
- **When** 任務結束
- **Then** 系統 SHALL 回報失敗

### Requirement: Configure download runtime and retry options
系統 MUST 探測可用的 Deno、Node.js、QuickJS 和 Bun runtime，並將找到的 runtime 傳給 yt-dlp；未找到時 SHALL 記錄警告。系統 SHALL 設定片段重試，且不從既有部分下載檔續傳。

#### Scenario: Runtime is unavailable
- **Given** 系統找不到支援的 JavaScript runtime
- **When** 系統建立下載選項
- **Then** 系統 SHALL 記錄警告並繼續建立下載選項

## MODIFIED Requirements

### Requirement: Disk space pre-check
對單一媒體，系統在可取得預估檔案大小時 MUST 檢查目標路徑空間是否足夠；不足時 SHALL 中止任務。播放清單目前 SHALL 不執行此下載前空間預檢。

#### Scenario: Disk space is insufficient
- **Given** 單一媒體來源提供檔案大小估計且磁碟剩餘空間不足
- **When** 任務準備下載
- **Then** 系統 SHALL 回報磁碟空間不足錯誤
- **And** 不啟動實際下載

#### Scenario: Playlist is submitted
- **Given** 輸入為播放清單
- **When** 任務準備下載
- **Then** 系統 SHALL 不執行單一媒體的下載前空間預檢
