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
