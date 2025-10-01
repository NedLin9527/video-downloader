"""
使用者介面模組
處理所有 UI 相關邏輯
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Optional
import threading
import queue

from constants import (
  APP_TITLE,
  WINDOW_WIDTH,
  WINDOW_HEIGHT,
  URL_ENTRY_WIDTH,
  MESSAGE_TEXT_HEIGHT,
  VIDEO_FORMATS,
  AUDIO_FORMATS,
  DOWNLOAD_TYPE_VIDEO,
  DOWNLOAD_TYPE_AUDIO,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
)
from config import ConfigManager
from downloader import DownloadManager, DownloadTask
from utils import Logger, get_timestamp, format_size, format_time, \
  open_directory, is_ffmpeg_installed


class VideoDownloaderUI:
  """影片下載器使用者介面"""

  def __init__(self, master: tk.Tk):
    self.master = master
    self.master.title(APP_TITLE)
    self.master.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

    # 初始化管理器
    self.config = ConfigManager()
    self.download_manager = DownloadManager()
    self.logger = Logger()
    self.message_queue = queue.Queue()

    # 當前任務
    self.current_task: Optional[DownloadTask] = None

    # 建立 UI
    self._create_widgets()
    self._setup_bindings()

    # 檢查 FFmpeg
    self._check_ffmpeg()

    # 開始處理訊息佇列
    self._process_message_queue()

  def _create_widgets(self):
    """建立所有 UI 元件"""
    # 主容器
    main_frame = ttk.Frame(self.master, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # URL 輸入區
    self._create_url_section(main_frame)

    # 格式選擇區
    self._create_format_section(main_frame)

    # 下載路徑區
    self._create_path_section(main_frame)

    # 按鈕區
    self._create_button_section(main_frame)

    # 進度條
    self._create_progress_section(main_frame)

    # 訊息顯示區
    self._create_message_section(main_frame)

    # 狀態列
    self._create_status_bar(main_frame)

  def _create_url_section(self, parent):
    """建立 URL 輸入區"""
    url_frame = ttk.LabelFrame(parent, text="影片/音樂 URL", padding="5")
    url_frame.pack(fill=tk.X, pady=5)

    self.url_entry = ttk.Entry(url_frame, width=URL_ENTRY_WIDTH)
    self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

    paste_btn = ttk.Button(url_frame, text="貼上", command=self._paste_url)
    paste_btn.pack(side=tk.LEFT)

  def _create_format_section(self, parent):
    """建立格式選擇區"""
    format_frame = ttk.LabelFrame(parent, text="格式設定", padding="5")
    format_frame.pack(fill=tk.X, pady=5)

    # 影片格式
    ttk.Label(format_frame, text="影片品質:").grid(row=0, column=0, sticky=tk.W,
                                                   padx=5)
    self.video_format_var = tk.StringVar(value=self.config.get("video_format"))
    video_combo = ttk.Combobox(
        format_frame,
        textvariable=self.video_format_var,
        values=list(VIDEO_FORMATS.keys()),
        state="readonly",
        width=20
    )
    video_combo.grid(row=0, column=1, sticky=tk.W, padx=5)

    # 音訊格式
    ttk.Label(format_frame, text="音訊品質:").grid(row=0, column=2, sticky=tk.W,
                                                   padx=5)
    self.audio_format_var = tk.StringVar(value=self.config.get("audio_format"))
    audio_combo = ttk.Combobox(
        format_frame,
        textvariable=self.audio_format_var,
        values=list(AUDIO_FORMATS.keys()),
        state="readonly",
        width=20
    )
    audio_combo.grid(row=0, column=3, sticky=tk.W, padx=5)

  def _create_path_section(self, parent):
    """建立下載路徑區"""
    path_frame = ttk.LabelFrame(parent, text="下載設定", padding="5")
    path_frame.pack(fill=tk.X, pady=5)

    ttk.Label(path_frame, text="儲存路徑:").pack(side=tk.LEFT)

    self.path_entry = ttk.Entry(path_frame, width=50)
    self.path_entry.insert(0, self.config.get_download_path())
    self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    browse_btn = ttk.Button(path_frame, text="瀏覽...",
                            command=self._browse_path)
    browse_btn.pack(side=tk.LEFT)

  def _create_button_section(self, parent):
    """建立按鈕區"""
    button_frame = ttk.Frame(parent)
    button_frame.pack(fill=tk.X, pady=10)

    self.download_video_btn = ttk.Button(
        button_frame,
        text="下載影片",
        command=lambda: self._start_download(DOWNLOAD_TYPE_VIDEO)
    )
    self.download_video_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    self.download_audio_btn = ttk.Button(
        button_frame,
        text="下載音樂",
        command=lambda: self._start_download(DOWNLOAD_TYPE_AUDIO)
    )
    self.download_audio_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    self.cancel_btn = ttk.Button(
        button_frame,
        text="取消下載",
        command=self._cancel_download,
        state=tk.DISABLED
    )
    self.cancel_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    settings_btn = ttk.Button(
        button_frame,
        text="設定",
        command=self._show_settings
    )
    settings_btn.pack(side=tk.LEFT, padx=5)

  def _create_progress_section(self, parent):
    """建立進度條區"""
    progress_frame = ttk.Frame(parent)
    progress_frame.pack(fill=tk.X, pady=5)

    self.progress_bar = ttk.Progressbar(
        progress_frame,
        mode='determinate',
        length=300
    )
    self.progress_bar.pack(fill=tk.X)

    self.progress_label = ttk.Label(progress_frame, text="")
    self.progress_label.pack(pady=5)

  def _create_message_section(self, parent):
    """建立訊息顯示區"""
    message_frame = ttk.LabelFrame(parent, text="下載記錄", padding="5")
    message_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    self.message_text = scrolledtext.ScrolledText(
        message_frame,
        height=MESSAGE_TEXT_HEIGHT,
        state=tk.DISABLED,
        wrap=tk.WORD
    )
    self.message_text.pack(fill=tk.BOTH, expand=True)

    # 清除按鈕
    clear_btn = ttk.Button(message_frame, text="清除記錄",
                           command=self._clear_messages)
    clear_btn.pack(pady=5)

  def _create_status_bar(self, parent):
    """建立狀態列"""
    status_frame = ttk.Frame(parent)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM)

    self.status_label = ttk.Label(status_frame, text="就緒", relief=tk.SUNKEN)
    self.status_label.pack(fill=tk.X)

  def _setup_bindings(self):
    """設定快捷鍵綁定"""
    self.url_entry.bind('<Control-v>', lambda e: self._paste_url())
    self.url_entry.bind('<Return>',
                        lambda e: self._start_download(DOWNLOAD_TYPE_VIDEO))

    # 視窗關閉事件
    self.master.protocol("WM_DELETE_WINDOW", self._on_closing)

  def _check_ffmpeg(self):
    """檢查 FFmpeg 是否安裝"""
    if not is_ffmpeg_installed():
      self.log_message("⚠️ 警告: FFmpeg 未安裝，音訊轉換功能將無法使用",
                       "warning")
      self.download_audio_btn.config(state=tk.DISABLED)

  def _paste_url(self):
    """貼上 URL"""
    try:
      clipboard = self.master.clipboard_get()
      self.url_entry.delete(0, tk.END)
      self.url_entry.insert(0, clipboard)
    except:
      pass

  def _browse_path(self):
    """瀏覽選擇路徑"""
    path = filedialog.askdirectory(initialdir=self.path_entry.get())
    if path:
      self.path_entry.delete(0, tk.END)
      self.path_entry.insert(0, path)
      self.config.set_download_path(path)

  def _start_download(self, download_type: str):
    """開始下載"""
    if self.current_task:
      messagebox.showinfo("提示", "目前已有下載任務進行中")
      return

    url = self.url_entry.get().strip()
    if not url:
      messagebox.showerror("錯誤", ERROR_MESSAGES['empty_url'])
      return

    output_path = self.path_entry.get().strip()

    if download_type == DOWNLOAD_TYPE_VIDEO:
      format_option = self.video_format_var.get()
    else:
      format_option = self.audio_format_var.get()

    # 更新 UI 狀態
    self._set_downloading_state(True)

    # 建立下載任務
    self.current_task = self.download_manager.create_task(
        url=url,
        download_type=download_type,
        output_path=output_path,
        format_option=format_option,
        progress_callback=self._on_progress,
        complete_callback=self._on_complete,
        error_callback=self._on_error,
    )

    # 在新執行緒中執行
    threading.Thread(target=self._execute_download, daemon=True).start()

    self.log_message(
      f"開始下載 {'影片' if download_type == DOWNLOAD_TYPE_VIDEO else '音樂'}: {url}")

  def _execute_download(self):
    """執行下載（在背景執行緒）"""
    try:
      self.current_task.execute()
    finally:
      self.download_manager.remove_task(self.current_task)
      self.current_task = None
      self.message_queue.put(('state', False))

  def _cancel_download(self):
    """取消下載"""
    if self.current_task:
      if messagebox.askyesno("確認", "確定要取消下載嗎？"):
        self.current_task.cancel()
        self.log_message("使用者取消下載")

  def _on_progress(self, data: dict):
    """進度更新回調"""
    self.message_queue.put(('progress', data))

  def _on_complete(self, file_path: str, info: dict):
    """下載完成回調"""
    self.message_queue.put(('complete', (file_path, info)))

  def _on_error(self, error_msg: str):
    """錯誤回調"""
    self.message_queue.put(('error', error_msg))

  def _process_message_queue(self):
    """處理訊息佇列（在主執行緒）"""
    try:
      while True:
        msg_type, data = self.message_queue.get_nowait()

        if msg_type == 'progress':
          self._update_progress(data)
        elif msg_type == 'complete':
          self._handle_complete(data[0], data[1])
        elif msg_type == 'error':
          self._handle_error(data)
        elif msg_type == 'state':
          self._set_downloading_state(data)
    except queue.Empty:
      pass

    self.master.after(100, self._process_message_queue)

  def _update_progress(self, data: dict):
    """更新進度顯示"""
    status = data.get('status')

    if status == 'downloading':
      percentage = data.get('percentage', 0)
      speed = data.get('speed', 0)
      eta = data.get('eta', 0)
      downloaded = data.get('downloaded', 0)
      total = data.get('total', 0)

      self.progress_bar['value'] = percentage

      speed_str = format_size(speed) + "/s" if speed > 0 else "計算中..."
      eta_str = format_time(eta) if eta > 0 else "計算中..."
      size_str = f"{format_size(downloaded)} / {format_size(total)}" if total > 0 else format_size(
        downloaded)

      progress_text = f"下載中: {percentage:.1f}% | {size_str} | 速度: {speed_str} | 剩餘: {eta_str}"
      self.progress_label.config(text=progress_text)
      self.status_label.config(text=f"下載中... {percentage:.1f}%")

    elif status == 'finished':
      self.progress_bar['value'] = 100
      self.progress_label.config(text="處理中...")
      self.status_label.config(text="後處理中...")

  def _handle_complete(self, file_path: str, info: dict):
    """處理下載完成"""
    self.log_message(f"✓ 下載完成: {file_path}", "success")

    self.progress_bar['value'] = 0
    self.progress_label.config(text="")
    self.status_label.config(text="就緒")

    # 詢問是否開啟目錄
    if self.config.get("auto_open_directory", True):
      import os
      if messagebox.askyesno("下載完成", "是否開啟下載目錄？"):
        open_directory(os.path.dirname(file_path))

  def _handle_error(self, error_msg: str):
    """處理錯誤"""
    self.log_message(f"✗ 錯誤: {error_msg}", "error")
    messagebox.showerror("下載失敗", error_msg)

    self.progress_bar['value'] = 0
    self.progress_label.config(text="")
    self.status_label.config(text="發生錯誤")

  def _set_downloading_state(self, is_downloading: bool):
    """設定下載中狀態"""
    if is_downloading:
      self.download_video_btn.config(state=tk.DISABLED)
      self.download_audio_btn.config(state=tk.DISABLED)
      self.cancel_btn.config(state=tk.NORMAL)
    else:
      self.download_video_btn.config(state=tk.NORMAL)
      self.download_audio_btn.config(state=tk.NORMAL)
      self.cancel_btn.config(state=tk.DISABLED)

  def log_message(self, message: str, level: str = "info"):
    """記錄訊息"""
    timestamp = get_timestamp()

    # 根據級別選擇圖示
    icons = {
      "info": "ℹ",
      "success": "✓",
      "warning": "⚠",
      "error": "✗",
    }
    icon = icons.get(level, "•")

    formatted_msg = f"[{timestamp}] {icon} {message}\n"

    self.message_text.config(state=tk.NORMAL)
    self.message_text.insert(tk.END, formatted_msg)
    self.message_text.see(tk.END)
    self.message_text.config(state=tk.DISABLED)

    # 同時記錄到日誌
    logger_method = getattr(self.logger, level, self.logger.info)
    logger_method(message)

  def _clear_messages(self):
    """清除訊息"""
    self.message_text.config(state=tk.NORMAL)
    self.message_text.delete(1.0, tk.END)
    self.message_text.config(state=tk.DISABLED)

  def _show_settings(self):
    """顯示設定視窗"""
    settings_window = tk.Toplevel(self.master)
    settings_window.title("設定")
    settings_window.geometry("400x300")
    settings_window.transient(self.master)
    settings_window.grab_set()

    # 設定選項
    frame = ttk.Frame(settings_window, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    # 自動轉換檔名
    auto_convert = tk.BooleanVar(
      value=self.config.get("auto_convert_filename", True))
    ttk.Checkbutton(
        frame,
        text="自動將檔名轉換為繁體中文",
        variable=auto_convert
    ).pack(anchor=tk.W, pady=5)

    # 自動開啟目錄
    auto_open = tk.BooleanVar(
      value=self.config.get("auto_open_directory", True))
    ttk.Checkbutton(
        frame,
        text="下載完成後自動開啟目錄",
        variable=auto_open
    ).pack(anchor=tk.W, pady=5)

    # 儲存按鈕
    def save_settings():
      self.config.set("auto_convert_filename", auto_convert.get())
      self.config.set("auto_open_directory", auto_open.get())
      settings_window.destroy()
      messagebox.showinfo("提示", "設定已儲存")

    ttk.Button(frame, text="儲存", command=save_settings).pack(pady=10)

  def _on_closing(self):
    """視窗關閉處理"""
    if self.current_task:
      if messagebox.askyesno("確認", "下載進行中，確定要關閉程式嗎？"):
        self.download_manager.cancel_all()
        self.master.destroy()
    else:
      self.master.destroy()