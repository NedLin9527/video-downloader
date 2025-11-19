"""
優化版影片下載器 - 主程式入口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from ui.main_window import VideoDownloaderUI


def main():
    """主程式入口"""
    root = tk.Tk()
    app = VideoDownloaderUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()