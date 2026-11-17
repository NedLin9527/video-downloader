## ADDED
### Requirement: Local-only default listener
Web 啟動入口與文件中的預設啟動方式 MUST 僅監聽本機 loopback 介面。

#### Scenario: Start the Web service with defaults
- **Given** 使用者以預設方式啟動 Web 服務
- **When** 服務開始監聽
- **Then** 服務 SHALL 綁定 `127.0.0.1`
