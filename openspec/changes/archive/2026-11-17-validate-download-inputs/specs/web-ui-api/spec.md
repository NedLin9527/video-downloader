## ADDED
### Requirement: Reject invalid download inputs
Web API MUST 在建立任務前驗證完整 URL 和下載類型對應的格式；無效輸入 SHALL 回傳 HTTP 422 和明確錯誤。

#### Scenario: Unsupported format is submitted
- **Given** 下載請求包含與類型不相符的格式
- **When** 呼叫 `POST /api/download`
- **Then** API SHALL 回傳 HTTP 422
- **And** 不建立下載任務
