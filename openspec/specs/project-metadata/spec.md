# Capability: Project Metadata

## Requirements
### Requirement: Consistent application version
套件中繼資料、桌面標題及 Web API 版本 MUST 使用同一個專案版本來源。

#### Scenario: Read version from application surfaces
- **Given** 專案版本在單一來源中定義
- **When** 讀取套件中繼資料、桌面標題與 Web API 資訊
- **Then** 各處 SHALL 顯示相同版本

### Requirement: Accurate environment and usage documentation
目前環境需求及操作文件 MUST 與實作和套件設定一致；未確認的歷史發布紀錄 SHALL 明確標示。

#### Scenario: Check Python requirement
- **Given** 套件要求 Python 3.11 或更新版本
- **When** 閱讀專案環境需求
- **Then** 文件 SHALL 記載 Python 3.11+
