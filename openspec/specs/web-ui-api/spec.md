# Capability: Web UI and API

## Purpose
定義 Web 介面的首頁渲染與下載 API 契約，包含任務建立、輪詢查詢、狀態欄位內容與錯誤回應行為，讓前端頁面與後端服務對於非同步下載流程有一致且可測試的介面規格。

## Requirements
### Requirement: Homepage renders available formats
系統 MUST 在首頁回傳下載表單，並提供目前可用影片與音訊格式選項。

#### Scenario: Open home page
- **Given** 使用者訪問 `/`
- **When** 伺服器回應 HTML
- **Then** 回應 SHALL 包含影片格式選單與音訊格式選單

### Requirement: Create asynchronous download tasks
API MUST 接受 `/api/download` 請求建立下載任務，並回傳可輪詢的 `task_id`。

#### Scenario: Submit valid download request
- **Given** 請求 payload 含有效 URL、下載類型與格式選項
- **When** 呼叫 `POST /api/download`
- **Then** API SHALL 回傳 `task_id`
- **And** 任務狀態 SHALL 先標記為 `queued` 或 `pending`

### Requirement: Expose task status polling endpoint
API MUST 提供 `/api/status/{task_id}` 查詢任務狀態；找不到任務時 SHALL 回傳 404。

#### Scenario: Query unknown task id
- **Given** 查詢不存在的 task id
- **When** 呼叫 `GET /api/status/{task_id}`
- **Then** API SHALL 回傳 HTTP 404

### Requirement: Status includes progress metadata
Web 任務在下載中 MUST 提供進度百分比與訊息，若有可用資料 SHALL 另含速度與 ETA。

#### Scenario: Poll active task
- **Given** 任務處於下載中
- **When** 前端輪詢狀態 API
- **Then** 回應 SHALL 包含 `status`、`progress`、`message`
- **And** 若有下載速率與剩餘時間則 SHALL 一併提供

### Requirement: Local-only default listener
Web 啟動入口與文件中的預設啟動方式 MUST 僅監聽本機 loopback 介面。

#### Scenario: Start the Web service with defaults
- **Given** 使用者以預設方式啟動 Web 服務
- **When** 服務開始監聽
- **Then** 服務 SHALL 綁定 `127.0.0.1`

### Requirement: Reject invalid download inputs
Web API MUST 在建立任務前驗證完整 URL 和下載類型對應的格式；無效輸入 SHALL 回傳 HTTP 422 和明確錯誤。

#### Scenario: Unsupported format is submitted
- **Given** 下載請求包含與類型不相符的格式
- **When** 呼叫 `POST /api/download`
- **Then** API SHALL 回傳 HTTP 422
- **And** 不建立下載任務

### Requirement: Report playlist completion count
Web 任務完成播放清單下載時，狀態訊息 MUST 包含成功下載的檔案數；`file_path` SHALL 回報最後一個成功下載的最終檔案路徑。

#### Scenario: Poll a completed playlist task
- **Given** 播放清單任務至少成功下載一個檔案
- **When** 使用者查詢完成的任務狀態
- **Then** `message` SHALL 包含成功下載的檔案數
- **And** `file_path` SHALL 為最後一個成功檔案的最終路徑
