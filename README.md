# 影片下載器 v2.0

優化版影片下載器，支援 YouTube、Bilibili 等多平台影片/音訊下載。

## 📋 主要特色

- ✅ **模組化架構**: 清晰的關注點分離，易於維護與擴展
- ✅ **進度追蹤**: 即時顯示下載進度、速度、剩餘時間
- ✅ **取消功能**: 可隨時中止進行中的下載
- ✅ **格式選擇**: 支援多種影片解析度與音訊品質
- ✅ **繁簡轉換**: 自動將簡體檔名轉為繁體中文
- ✅ **錯誤處理**: 完善的錯誤處理與日誌記錄
- ✅ **設定儲存**: 保存使用者偏好設定
- ✅ **跨平台支援**: Windows、macOS、Linux

## 📦 安裝

### 環境需求
- Python 3.8+
- FFmpeg（音訊轉換必須）

### 安裝步驟

1. 克隆或下載專案
```bash
git clone <repository_url>
cd video-downloader
```

2. 安裝 Python 套件
```bash
pip install -r requirements.txt
```

3. 安裝 FFmpeg

**Windows:**
```bash
# 使用 Chocolatey
choco install ffmpeg

# 或從官網下載: https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

## 🚀 使用方法

### 啟動程式
```bash
python main.py
```

### 基本操作

1. **輸入 URL**: 在 URL 欄位貼上影片連結
2. **選擇格式**: 
   - 影片品質: 最高畫質 / 1080p / 720p / 480p
   - 音訊品質: MP3 (192/320kbps) / M4A / OPUS
3. **設定路徑**: 選擇儲存位置（預設為 `./downloads`）
4. **開始下載**: 點擊「下載影片」或「下載音樂」
5. **取消下載**: 若需要，點擊「取消下載」按鈕

### 快捷鍵
- `Ctrl+V`: 貼上 URL
- `Enter`: 開始下載影片

## 📁 專案結構

```
video-downloader/
├── main.py              # 程式入口
├── ui.py                # 使用者介面
├── downloader.py        # 下載核心邏輯
├── config.py            # 設定管理
├── utils.py             # 工具函式
├── constants.py         # 常數定義
├── requirements.txt     # 套件需求
├── config.json          # 使用者設定（自動生成）
├── downloader.log       # 日誌檔案（自動生成）
└── downloads/           # 預設下載目錄（自動生成）
```

## ⚙️ 設定選項

點擊「設定」按鈕可調整以下選項：

- **自動轉換檔名**: 將簡體中文檔名轉為繁體
- **自動開啟目錄**: 下載完成後自動開啟儲存目錄

設定會自動儲存至 `config.json`。

## 🔧 進階使用

### 自訂下載選項

編輯 `constants.py` 以自訂：
- 影片格式選項
- 音訊品質設定
- 下載逾時時間
- 重試次數
- UI 主題顏色

### 日誌檔案

所有操作都會記錄在 `downloader.log`，包含：
- 下載開始/完成時間
- 錯誤訊息詳情
- 檔名轉換記錄

## 🐛 常見問題

### Q: 下載失敗顯示「FFmpeg 未安裝」
**A**: 請依照安裝步驟安裝 FFmpeg。音訊轉換功能需要 FFmpeg 支援。

### Q: 檔名沒有轉換為繁體中文
**A**: 確認已安裝 `opencc-python-reimplemented` 套件，並在設定中啟用「自動轉換檔名」。

### Q: 下載速度很慢
**A**: 這通常與網路狀態或影片平台限制有關。可以嘗試：
- 檢查網路連線
- 選擇較低解析度
- 使用代理伺服器（未來版本支援）

### Q: 支援哪些平台？
**A**: 支援所有 yt-dlp 支援的平台，包括但不限於：
- YouTube
- Bilibili
- Twitter/X
- Facebook
- Instagram
- TikTok
- 完整清單: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

## 📝 更新日誌

### v2.0.0 (2025-10-01)
- ✨ 完全重構，模組化架構
- ✨ 新增取消下載功能
- ✨ 新增即時進度顯示
- ✨ 新增格式選擇功能
- ✨ 新增設定管理
- ✨ 改進錯誤處理
- ✨ 改進 UI/UX
- ✨ 新增日誌系統
- ✨ 新增跨平台支援

### v1.0.0
- 🎉 初始版本

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

## 📄 授權

MIT License

## 👨‍💻 作者

Ned Lin

## 🙏 致謝

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 強大的影片下載工具
- [OpenCC](https://github.com/BYVoid/OpenCC) - 繁簡轉換引擎
- [FFmpeg](https://ffmpeg.org/) - 多媒體處理框架