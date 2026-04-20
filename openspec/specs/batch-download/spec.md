# Capability: Batch Download

## Purpose
定義批次下載管理器如何從文字建立任務佇列、以單一工作執行緒依序處理任務、在失敗時依上限重試，並提供可供 UI 呈現的進度摘要與批次完成通知，確保批次流程一致可追蹤。

## Requirements
### Requirement: Parse batch URLs from comma-separated text
批次下載管理器 MUST 將逗號分隔文字解析為 URL 任務清單，並以輸入順序加入佇列。

#### Scenario: Add multiple URLs into queue
- **Given** 使用者輸入多個以逗號分隔的 URL 文字
- **When** 系統建立批次任務
- **Then** 每個有效項目 SHALL 轉為一筆待處理任務
- **And** 任務順序 SHALL 與輸入順序一致

### Requirement: Sequential batch execution
批次流程 MUST 以單一工作執行緒依序執行任務，並維護目前索引與摘要統計。

#### Scenario: Worker processes tasks one by one
- **Given** 佇列中有多個待下載任務
- **When** 批次下載啟動
- **Then** 系統 SHALL 一次只處理一個任務
- **And** SHALL 可查詢總數、完成、失敗、等待、進行中統計

### Requirement: Retry failed tasks up to configured limit
任務失敗時，系統 MUST 在未超過重試上限時重新排入佇列；達上限後 SHALL 標記最終失敗。

#### Scenario: Failed task is retried then finalized
- **Given** 任務下載失敗且仍低於 `max_retries`
- **When** 單次任務結束
- **Then** 系統 SHALL 增加 retry 次數並重新加入待處理佇列
- **And** 若重試次數達上限後仍失敗，任務 SHALL 標記為 `FAILED`

### Requirement: Batch completion callback
批次處理結束後 MUST 觸發完成回調，回傳最終摘要。

#### Scenario: Batch reaches terminal state
- **Given** 佇列已清空或批次已停止
- **When** 工作迴圈結束
- **Then** 系統 SHALL 回報批次摘要給完成回調
