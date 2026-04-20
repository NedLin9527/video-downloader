# Capability: Testing and Documentation Governance

## ADDED Requirements
### Requirement: Behavior changes MUST include specification updates
所有會影響外部行為的變更 MUST 先更新對應 OpenSpec change 與 delta spec，再進入實作。

#### Scenario: Feature change starts
- **Given** 開發者準備修改 UI 或 API 行為
- **When** 變更開始
- **Then** 變更 SHALL 先建立 proposal、tasks 與 delta spec

### Requirement: Implementation MUST be traceable to tasks
實作階段每一項功能變更 MUST 對應 `tasks.md` 可勾選項目，避免超範圍實作。

#### Scenario: Task-driven implementation
- **Given** 開發者在 apply 階段執行變更
- **When** 完成某一項工作
- **Then** 對應 task SHALL 被勾選並可追溯到相關提交

### Requirement: Verification MUST be recorded before archive
變更在 archive 前 MUST 記錄最小驗證結果（至少包含執行項目與結果摘要）。

#### Scenario: Preparing archive
- **Given** change 進入收尾階段
- **When** 準備 archive
- **Then** 文件 SHALL 記錄測試或驗證摘要
- **And** 未驗證項目 SHALL 明確標註風險
