"""
日誌管理工具
"""

import logging
from core.constants import LOG_FILE, LOG_LEVEL


class Logger:
    """日誌管理器"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        """設定日誌"""
        self.logger = logging.getLogger("VideoDownloader")
        self.logger.setLevel(getattr(logging, LOG_LEVEL))

        # 檔案處理器
        fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # 控制台處理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # 格式設定
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def debug(self, message: str):
        self.logger.debug(message)