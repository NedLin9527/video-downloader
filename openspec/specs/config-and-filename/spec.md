# Capability: Config and Filename Handling

## Purpose
定義使用者偏好設定的持久化、下載路徑可用性保障，以及下載完成後檔名繁簡轉換與衝突處理規則，確保設定管理與檔案命名行為在不同執行環境下維持一致且安全。

## Requirements
### Requirement: Persist user preferences in config file
系統 MUST 使用 `config.json` 儲存使用者偏好，並在啟動時載入；檔案不存在或讀取失敗時 SHALL 使用預設值。

#### Scenario: Missing config file
- **Given** 尚未建立 `config.json`
- **When** 設定管理器初始化
- **Then** 系統 SHALL 載入預設設定

### Requirement: Ensure download path exists before use
系統在取得下載路徑時 MUST 確保目錄存在，不存在時 SHALL 自動建立。

#### Scenario: Config points to non-existing directory
- **Given** 設定中的下載目錄尚未建立
- **When** 系統讀取下載路徑
- **Then** 系統 SHALL 建立該目錄並回傳可用路徑

### Requirement: Optional simplified-to-traditional filename conversion
當 `auto_convert_filename` 啟用時，下載完成後系統 MUST 嘗試將檔名由簡體轉繁體並清理不合法字元；失敗時 SHALL 不中斷下載結果。

#### Scenario: Conversion fails
- **Given** 下載已完成且檔名轉換過程發生錯誤
- **When** 系統處理檔名
- **Then** 系統 SHALL 記錄警告
- **And** 任務結果 SHALL 維持成功

### Requirement: Avoid filename collision on rename
檔名轉換後若目標檔名已存在，系統 MUST 透過遞增後綴避免覆蓋既有檔案。

#### Scenario: Converted filename already exists
- **Given** 轉換後的新檔名在目標目錄已存在
- **When** 系統執行 rename
- **Then** 系統 SHALL 產生附加序號的新檔名
