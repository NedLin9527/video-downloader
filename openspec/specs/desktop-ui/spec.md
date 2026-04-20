# Capability: Desktop UI

## Purpose
定義桌面介面在單一/批次模式切換、下載啟動防呆、即時進度顯示、完成或失敗後狀態復原，以及 FFmpeg 依賴檢查與提示訊息的互動契約，避免 UI 行為與核心下載邏輯脫鉤。

## Requirements
### Requirement: Support single and batch modes
桌面 UI MUST 提供單一下載與批次下載模式切換；批次模式 SHALL 顯示批次輸入區並停用單一 URL 欄位。

#### Scenario: Switch to batch mode
- **Given** 使用者在主視窗切換至批次模式
- **When** UI 更新版面
- **Then** 批次 URL 輸入區 SHALL 顯示
- **And** 單一 URL 欄位 SHALL 被停用

### Requirement: Prevent overlapping download runs
在已有進行中任務時，UI MUST 阻止再次啟動新下載。

#### Scenario: Start blocked while task is active
- **Given** 目前已有單一或批次下載進行中
- **When** 使用者再次按下下載
- **Then** UI SHALL 顯示提示並不建立新任務

### Requirement: Reflect progress and completion in UI
UI MUST 在下載過程顯示進度、速度與剩餘時間，完成或失敗後 SHALL 重置狀態元件。

#### Scenario: Download finishes
- **Given** 任務回報完成
- **When** UI 接收完成事件
- **Then** UI SHALL 顯示完成訊息
- **And** 進度條與狀態 SHALL 重置為可再次下載

### Requirement: Audio button gated by FFmpeg availability
當系統檢查不到 FFmpeg 時，UI MUST 停用音訊下載按鈕並提示使用者。

#### Scenario: FFmpeg not installed
- **Given** 啟動時 FFmpeg 檢查失敗
- **When** 主視窗完成初始化
- **Then** 音訊下載按鈕 SHALL 為 disabled
- **And** 記錄區 SHALL 出現警告訊息
