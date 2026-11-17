"""
優化版影片下載器 - 主程式入口
"""

import tkinter as tk
from src.ui.main_window import VideoDownloaderUI


def main():
    """主程式入口"""
    root = tk.Tk()
    app = VideoDownloaderUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()