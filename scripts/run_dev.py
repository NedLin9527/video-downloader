#!/usr/bin/env python3
"""
開發環境啟動腳本
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 啟動應用程式
from main import main

if __name__ == "__main__":
    main()