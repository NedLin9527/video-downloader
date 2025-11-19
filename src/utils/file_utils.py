"""
檔案處理工具
"""

import re
import os
from typing import Optional
from utils.logger import Logger
from core.constants import OPENCC_CONFIG, OPENCC_FALLBACK_CONFIGS


def sanitize_filename(filename: str) -> str:
    """
    清理檔名，移除不合法字元
    
    Args:
        filename: 原始檔名
        
    Returns:
        str: 清理後的檔名
    """
    # 移除不合法字元
    illegal_chars = r'[<>:"/\\|?*]'
    filename = re.sub(illegal_chars, '_', filename)
    
    # 移除開頭結尾的空白和點
    filename = filename.strip('. ')
    
    # 限制長度
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200 - len(ext)] + ext
    
    return filename


def convert_to_traditional_chinese(text: str) -> Optional[str]:
    """
    將簡體中文轉換為繁體中文
    
    Args:
        text: 要轉換的文字
        
    Returns:
        Optional[str]: 轉換後的文字，失敗則返回 None
    """
    try:
        import opencc
        
        # 嘗試使用主要設定
        try:
            converter = opencc.OpenCC(OPENCC_CONFIG)
            return converter.convert(text)
        except:
            # 嘗試備用設定
            for config in OPENCC_FALLBACK_CONFIGS:
                try:
                    converter = opencc.OpenCC(config)
                    return converter.convert(text)
                except:
                    continue
        
        Logger().warning("所有 OpenCC 設定檔都無法使用")
        return None
    except ImportError:
        Logger().warning("OpenCC 未安裝，無法進行繁簡轉換")
        return None
    except Exception as e:
        Logger().error(f"繁簡轉換失敗: {e}")
        return None