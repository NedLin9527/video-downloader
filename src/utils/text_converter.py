"""
繁簡轉換工具
"""

import os
from typing import Optional
from utils.logger import Logger

try:
    import opencc
    OPENCC_AVAILABLE = True
except ImportError:
    OPENCC_AVAILABLE = False


class TextConverter:
    """繁簡轉換器"""
    
    def __init__(self):
        self.converter: Optional[opencc.OpenCC] = None
        self.logger = Logger()
        self._init_converter()
    
    def _init_converter(self):
        """初始化轉換器"""
        if not OPENCC_AVAILABLE:
            self.logger.warning("OpenCC 未安裝，繁簡轉換功能無法使用")
            return
            
        try:
            # 嘗試不同的配置
            configs = ['s2t.json', 's2t', 's2tw', 's2twp']
            
            for config in configs:
                try:
                    self.converter = opencc.OpenCC(config)
                    self.logger.info(f"繁簡轉換器初始化成功，使用配置: {config}")
                    break
                except Exception as e:
                    self.logger.debug(f"配置 {config} 初始化失敗: {e}")
                    continue
                    
            if not self.converter:
                self.logger.error("所有 OpenCC 配置都初始化失敗")
                
        except Exception as e:
            self.logger.error(f"繁簡轉換器初始化失敗: {e}")
    
    def is_available(self) -> bool:
        """檢查轉換器是否可用"""
        return self.converter is not None
    
    def convert(self, text: str) -> str:
        """轉換文字（簡體轉繁體）"""
        if not self.is_available():
            return text
            
        try:
            return self.converter.convert(text)
        except Exception as e:
            self.logger.error(f"文字轉換失敗: {e}")
            return text
    
    def convert_filename(self, filename: str) -> str:
        """轉換檔名（保留副檔名）"""
        if not filename or not self.is_available():
            return filename
            
        try:
            # 分離檔名和副檔名
            name, ext = os.path.splitext(filename)
            
            # 轉換檔名部分
            converted_name = self.convert(name)
            
            # 重新組合
            converted_filename = converted_name + ext
            
            if converted_filename != filename:
                self.logger.info(f"檔名轉換: {filename} -> {converted_filename}")
                
            return converted_filename
            
        except Exception as e:
            self.logger.error(f"檔名轉換失敗: {e}")
            return filename


# 全域實例
_converter = TextConverter()

def convert_text(text: str) -> str:
    """轉換文字（簡體轉繁體）"""
    return _converter.convert(text)

def convert_filename(filename: str) -> str:
    """轉換檔名（簡體轉繁體）"""
    return _converter.convert_filename(filename)

def is_converter_available() -> bool:
    """檢查轉換器是否可用"""
    return _converter.is_available()