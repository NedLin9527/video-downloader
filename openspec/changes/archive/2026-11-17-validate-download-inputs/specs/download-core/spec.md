## ADDED
### Requirement: Validate complete download inputs
系統 MUST 驗證完整 HTTP(S) URL，以及下載類型和格式選項的對應關係；驗證失敗 SHALL 回報明確錯誤且不啟動 yt-dlp。

#### Scenario: Format belongs to another download type
- **Given** 影片任務選擇音訊格式
- **When** 執行下載
- **Then** 系統 SHALL 回報格式不支援
- **And** 不使用預設格式代替
