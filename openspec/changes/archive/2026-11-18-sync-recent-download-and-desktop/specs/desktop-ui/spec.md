## ADDED Requirements

### Requirement: Desktop download workspace
桌面主視窗 MUST 提供下載連結、下載格式、儲存位置、下載操作、進度與下載記錄區。預設及最小視窗尺寸下，單一與批次模式的主要操作和下載記錄 SHALL 完整顯示而不需捲動主畫面；下載記錄內容可在其區域內捲動。

#### Scenario: View the single-download workspace
- **Given** 使用者以預設視窗尺寸開啟桌面程式
- **When** 顯示單一下載模式
- **Then** 主要操作及下載記錄區 SHALL 完整顯示
- **And** 使用者 SHALL 不需捲動主畫面

#### Scenario: View the batch-download workspace
- **Given** 使用者切換至批次模式
- **When** 視窗處於支援的最小尺寸
- **Then** 批次輸入、下載操作與下載記錄區 SHALL 完整顯示

### Requirement: Display playlist completion count
桌面介面 MUST 在播放清單下載完成時顯示成功下載的檔案數。

#### Scenario: Playlist download finishes
- **Given** 播放清單至少有一個檔案成功下載
- **When** 桌面介面收到完成事件
- **Then** 下載記錄 SHALL 顯示成功下載的檔案數

## MODIFIED Requirements

### Requirement: Audio button gated by FFmpeg availability
當系統檢查不到 FFmpeg 時，UI MUST 停用音訊下載按鈕並提示使用者；其他下載結束並恢復操作狀態後，音訊下載按鈕 SHALL 保持停用。

#### Scenario: FFmpeg not installed
- **Given** 啟動時 FFmpeg 檢查失敗
- **When** 主視窗完成初始化
- **Then** 音訊下載按鈕 SHALL 為 disabled
- **And** 記錄區 SHALL 出現警告訊息

#### Scenario: Another download finishes without FFmpeg
- **Given** FFmpeg 不可用且影片下載已結束
- **When** UI 恢復下載按鈕狀態
- **Then** 音訊下載按鈕 SHALL 保持 disabled
