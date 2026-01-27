"""
常數定義
"""

# 應用程式資訊
APP_TITLE = "影片下載器 v2.1"
APP_VERSION = "2.1.0"

# UI 相關常數
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 500
URL_ENTRY_WIDTH = 60
MESSAGE_TEXT_HEIGHT = 12

# 下載類型
DOWNLOAD_TYPE_VIDEO = "video"
DOWNLOAD_TYPE_AUDIO = "audio"

# 影片格式設定
VIDEO_FORMATS = {
    "最高畫質": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
}

# 音訊格式設定
AUDIO_FORMATS = {
    "MP3 (192kbps)": {"codec": "mp3", "quality": "192"},
    "MP3 (320kbps)": {"codec": "mp3", "quality": "320"},
    "M4A (高品質)": {"codec": "m4a", "quality": "0"},
    "OPUS": {"codec": "opus", "quality": "0"},
}

# 檔案路徑
DEFAULT_DOWNLOAD_PATH = "./downloads"
CONFIG_FILE = "config.json"
LOG_FILE = "downloader.log"

# 錯誤訊息
ERROR_MESSAGES = {
    "empty_url": "請輸入有效的 URL",
    "invalid_url": "URL 格式無效，請檢查後重試",
    "network_error": "網路連線失敗，請檢查網路狀態",
    "download_error": "下載過程發生錯誤",
    "permission_error": "檔案權限不足，請檢查儲存路徑",
    "disk_space_error": "磁碟空間不足",
    "ffmpeg_not_found": "FFmpeg 未安裝，音訊轉換功能無法使用",
}

# 成功訊息
SUCCESS_MESSAGES = {
    "download_complete": "下載完成",
    "conversion_complete": "檔名轉換完成",
    "cancel_success": "下載已取消",
}

# 下載選項
DOWNLOAD_TIMEOUT = 300
RETRY_ATTEMPTS = 3

# 日誌等級
LOG_LEVEL = "INFO"

# OpenCC 設定
OPENCC_CONFIG = "s2t.json"
OPENCC_FALLBACK_CONFIGS = ["s2t", "s2tw", "s2twp"]

# URL 驗證
URL_PATTERN = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'