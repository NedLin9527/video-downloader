"""
優化版影片下載器 - 主程式入口
Author: Ned Lin
Version: 2.0.0
"""

import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import src.main as src_main

if __name__ == "__main__":
    src_main.main()