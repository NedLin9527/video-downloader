# 專案架構說明

## 目錄結構

```
video-downloader/
├── src/                    # 主要原始碼
│   ├── core/              # 核心功能模組
│   │   ├── __init__.py
│   │   ├── constants.py   # 常數定義
│   │   ├── config.py      # 設定管理
│   │   └── downloader.py  # 下載核心邏輯
│   ├── ui/                # 使用者介面
│   │   ├── __init__.py
│   │   └── main_window.py # 主視窗
│   ├── utils/             # 工具函式
│   │   ├── __init__.py
│   │   ├── logger.py      # 日誌管理
│   │   ├── validators.py  # 驗證工具
│   │   ├── file_utils.py  # 檔案處理
│   │   ├── system_utils.py # 系統工具
│   │   └── time_utils.py  # 時間工具
│   └── main.py            # 程式入口
├── tests/                 # 測試檔案
├── scripts/               # 建置與開發腳本
├── docs/                  # 文檔
├── main.py               # 根目錄啟動檔案
├── setup.py              # 安裝配置
├── pyproject.toml        # 現代化配置
└── requirements.txt      # 依賴套件
```

## 模組說明

### Core 模組
- **constants.py**: 所有常數定義，包含 UI 設定、格式選項、錯誤訊息等
- **config.py**: 設定檔管理，負責讀取/儲存使用者偏好
- **downloader.py**: 下載核心邏輯，包含任務管理和 yt-dlp 整合

### UI 模組
- **main_window.py**: 主視窗介面，處理所有 UI 互動

### Utils 模組
- **logger.py**: 統一的日誌管理
- **validators.py**: 輸入驗證功能
- **file_utils.py**: 檔案處理工具
- **system_utils.py**: 系統相關工具
- **time_utils.py**: 時間處理工具

## 設計原則

1. **關注點分離**: 每個模組負責特定功能
2. **模組化**: 易於測試和維護
3. **可擴展性**: 新功能可輕鬆添加
4. **錯誤處理**: 完善的異常處理機制
5. **類型提示**: 提高代碼可讀性和 IDE 支援

## 依賴關係

```
main.py
└── src/main.py
    └── ui/main_window.py
        ├── core/config.py
        ├── core/downloader.py
        └── utils/*
```

## 擴展指南

### 添加新的下載平台
1. 在 `core/constants.py` 中添加平台相關常數
2. 在 `core/downloader.py` 中擴展下載邏輯
3. 更新 UI 以支援新選項

### 添加新的 UI 功能
1. 在 `ui/` 目錄下創建新的 UI 模組
2. 在 `main_window.py` 中整合新功能
3. 更新相關的設定和常數

### 添加新的工具函式
1. 在適當的 `utils/` 子模組中添加函式
2. 更新 `utils/__init__.py` 的匯出清單
3. 添加對應的測試案例