# Capability: Download Core

## Purpose
定義單一下載任務的完整核心契約，包含輸入 URL 驗證、yt-dlp 參數建構、進度事件傳遞、使用者取消處理與下載前磁碟空間檢查，確保下載流程在成功與失敗路徑都可預期。

## Requirements
### Requirement: URL validation before download
系統在建立並執行下載任務前 MUST 驗證輸入 URL，無效 URL SHALL 立即回傳錯誤而不啟動 `yt-dlp`。

#### Scenario: Invalid URL is rejected
- **Given** 使用者提供空字串或不符合 URL 規則的文字
- **When** 系統執行單一下載任務
- **Then** 任務 SHALL 失敗並回報 URL 無效錯誤
- **And** 不會發生實際下載流程

### Requirement: Video and audio format mapping
系統 MUST 根據下載類型與格式選項建立對應 `yt-dlp` 參數；影片下載 SHALL 使用影片格式規則，音訊下載 SHALL 使用 FFmpeg 後處理抽取音訊。

#### Scenario: Audio download applies postprocessor
- **Given** 使用者選擇 `audio` 類型與可用音訊格式
- **When** 系統建立 `yt-dlp` 選項
- **Then** 選項 MUST 包含 `format=bestaudio/best`
- **And** MUST 包含 `FFmpegExtractAudio` 對應編碼與品質

### Requirement: Progress callback for active downloads
下載任務在執行期間 MUST 提供進度資料（百分比、速度、剩餘時間），下載完成前 SHALL 回報 `downloading` 狀態。

#### Scenario: Progress update emitted during transfer
- **Given** 任務正在下載且來源回報位元組進度
- **When** 進度 hook 被觸發
- **Then** 系統 SHALL 回呼進度資料並包含 `percentage`、`speed`、`eta`

### Requirement: Cancellation support
下載任務 MUST 支援使用者取消；被取消任務 SHALL 停止並回傳失敗結果。

#### Scenario: User cancels an in-flight task
- **Given** 任務正在下載中
- **When** 使用者觸發取消
- **Then** 任務 SHALL 終止下載流程
- **And** 系統 SHALL 記錄取消事件

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
### Requirement: Final output path
下載完成回呼 MUST 回報 yt-dlp 後處理完成且檔名轉換後的實際輸出路徑。

#### Scenario: Audio is converted after downloading
- **Given** 音訊下載後被轉換為不同副檔名
- **When** 下載與後處理成功完成
- **Then** 完成回呼 SHALL 回報已存在的最終音訊檔案路徑

### Requirement: Validate complete download inputs
系統 MUST 驗證完整 HTTP(S) URL，以及下載類型和格式選項的對應關係；驗證失敗 SHALL 回報明確錯誤且不啟動 yt-dlp。

#### Scenario: Format belongs to another download type
- **Given** 影片任務選擇音訊格式
- **When** 執行下載
- **Then** 系統 SHALL 回報格式不支援
- **And** 不使用預設格式代替

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
