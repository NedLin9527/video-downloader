"""
優化版影片下載器 - 主程式入口
Author: Your Name
Version: 2.0.0
"""

import tkinter as tk
from ui import VideoDownloaderUI

def main():
    """主程式入口"""
    root = tk.Tk()
    app = VideoDownloaderUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()