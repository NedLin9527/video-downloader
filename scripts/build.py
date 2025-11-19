#!/usr/bin/env python3
"""
建置腳本
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """執行命令"""
    print(f"執行: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"命令執行失敗: {cmd}")
        sys.exit(1)

def main():
    """主要建置流程"""
    project_root = Path(__file__).parent.parent
    
    print("開始建置專案...")
    
    # 清理舊的建置檔案
    print("清理舊檔案...")
    run_command("rm -rf build dist *.egg-info", cwd=project_root)
    
    # 建置套件
    print("建置套件...")
    run_command("python -m build", cwd=project_root)
    
    print("建置完成！")

if __name__ == "__main__":
    main()