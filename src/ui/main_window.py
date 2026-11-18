"""
主視窗 UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Optional
import threading
import queue
import os

from src.core.constants import (
    APP_TITLE,
    VIDEO_FORMATS,
    AUDIO_FORMATS,
    DOWNLOAD_TYPE_VIDEO,
    DOWNLOAD_TYPE_AUDIO,
    ERROR_MESSAGES,
)
from src.core.config import ConfigManager
from src.core.downloader import DownloadManager, DownloadTask
from src.core.batch_downloader import BatchDownloadManager, TaskStatus
from src.utils.validators import parse_batch_urls, validate_download_format, validate_url
from src.utils import (
    Logger, get_timestamp, format_size, format_time,
    open_directory, is_ffmpeg_installed
)


class VideoDownloaderUI:
    """影片下載器使用者介面"""

    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title(APP_TITLE)
        self.master.geometry("820x780")
        self.master.minsize(680, 700)

        # 初始化管理器
        self.config = ConfigManager()
        self.download_manager = DownloadManager()
        self.batch_manager = BatchDownloadManager(max_retries=3)
        self.logger = Logger()
        self.message_queue = queue.Queue()

        # 當前任務
        self.current_task: Optional[DownloadTask] = None
        self.is_batch_mode = False

        # 設定批次下載回調
        self.batch_manager.progress_callback = self._on_batch_progress
        self.batch_manager.task_complete_callback = self._on_batch_task_complete
        self.batch_manager.batch_complete_callback = self._on_batch_complete

        # 建立 UI
        self._create_widgets()
        self._setup_bindings()

        # 檢查 FFmpeg
        self._check_ffmpeg()

        # 開始處理訊息佇列
        self._process_message_queue()

    def _create_widgets(self):
        """建立下載工作區。"""
        self._configure_styles()
        self.master.configure(background="#f2f5f9")
        main = ttk.Frame(self.master, style="App.TFrame", padding=(22, 12))
        main.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main, style="App.TFrame")
        header.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(header, text="VIDEO DOWNLOADER", style="Eyebrow.TLabel").pack(anchor=tk.W)
        title_row = ttk.Frame(header, style="App.TFrame")
        title_row.pack(fill=tk.X)
        ttk.Label(title_row, text="影片下載器", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Button(title_row, text="設定", style="Quiet.TButton",
                   command=self._show_settings).pack(side=tk.RIGHT)
        ttk.Label(header, text="貼上連結，選擇格式，開始下載。", style="Subtitle.TLabel").pack(anchor=tk.W, pady=(4, 0))

        self._create_url_section(main)
        self._create_format_section(main)
        self._create_path_section(main)
        self._create_button_section(main)
        self._create_progress_section(main)
        self._create_message_section(main)
        self._create_status_bar(main)

    def _configure_styles(self):
        style = ttk.Style(self.master)
        style.theme_use("clam")
        style.configure("App.TFrame", background="#f2f5f9")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("App.TLabel", background="#f2f5f9", foreground="#273449", font=("Helvetica", 11))
        style.configure("Card.TLabel", background="#ffffff", foreground="#273449", font=("Helvetica", 11))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#68778b", font=("Helvetica", 10))
        style.configure("Section.TLabel", background="#ffffff", foreground="#18263a", font=("Helvetica", 12, "bold"))
        style.configure("Title.TLabel", background="#f2f5f9", foreground="#142238", font=("Helvetica", 21, "bold"))
        style.configure("Eyebrow.TLabel", background="#f2f5f9", foreground="#3167ca", font=("Helvetica", 9, "bold"))
        style.configure("Subtitle.TLabel", background="#f2f5f9", foreground="#68778b", font=("Helvetica", 11))
        style.configure("Card.TRadiobutton", background="#ffffff", foreground="#273449", font=("Helvetica", 11))
        style.map("Card.TRadiobutton", background=[("active", "#ffffff")])
        style.configure("TEntry", padding=4, fieldbackground="#f8fafc", bordercolor="#d7e0eb")
        style.configure("TCombobox", padding=4, fieldbackground="#f8fafc", bordercolor="#d7e0eb")
        style.configure("TButton", padding=(12, 5), font=("Helvetica", 10), background="#edf2f8", foreground="#273449", borderwidth=0)
        style.map("TButton", background=[("active", "#dfe8f4"), ("disabled", "#edf2f8")], foreground=[("disabled", "#a0aabb")])
        style.configure("Primary.TButton", background="#3268d4", foreground="#ffffff", font=("Helvetica", 11, "bold"))
        style.map("Primary.TButton", background=[("disabled", "#b9c9e6"), ("active", "#2556b8")], foreground=[("disabled", "#f4f6fa")])
        style.configure("Quiet.TButton", background="#e5ebf3", foreground="#34465d")
        style.configure("Download.Horizontal.TProgressbar", troughcolor="#e8eef5", background="#3268d4", borderwidth=0, thickness=8)

    def _card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(14, 8))
        card.pack(fill=tk.X, pady=(0, 6))
        return card

    def _create_url_section(self, parent):
        card = self._card(parent)
        heading = ttk.Frame(card, style="Card.TFrame")
        heading.pack(fill=tk.X)
        ttk.Label(heading, text="01  下載連結", style="Section.TLabel").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(heading, text="單一", variable=self.mode_var, value="single",
                        command=self._toggle_mode, style="Card.TRadiobutton").pack(side=tk.RIGHT)
        ttk.Radiobutton(heading, text="批次", variable=self.mode_var, value="batch",
                        command=self._toggle_mode, style="Card.TRadiobutton").pack(side=tk.RIGHT, padx=(0, 16))
        ttk.Label(card, text="輸入影片或音樂網址", style="Muted.TLabel").pack(anchor=tk.W, pady=(2, 4))
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill=tk.X)
        self.url_entry = ttk.Entry(row)
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(row, text="貼上", command=self._paste_url).pack(side=tk.LEFT)
        self.batch_frame = ttk.Frame(card, style="Card.TFrame")
        ttk.Label(self.batch_frame, text="多個網址請以逗號分隔", style="Muted.TLabel").pack(anchor=tk.W, pady=(2, 3))
        batch_row = ttk.Frame(self.batch_frame, style="Card.TFrame")
        batch_row.pack(fill=tk.X)
        self.batch_text = scrolledtext.ScrolledText(batch_row, height=2, wrap=tk.WORD,
                                                    relief=tk.SOLID, borderwidth=1, font=("Helvetica", 11),
                                                    background="#f8fafc", foreground="#273449", insertbackground="#273449")
        actions = ttk.Frame(batch_row, style="Card.TFrame")
        actions.pack(side=tk.RIGHT, padx=(8, 0))
        self.batch_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(actions, text="從剪貼簿載入", command=self._load_batch_urls).pack(fill=tk.X)
        ttk.Button(actions, text="清除輸入", command=lambda: self.batch_text.delete(1.0, tk.END)).pack(fill=tk.X)

    def _create_format_section(self, parent):
        card = self._card(parent)
        ttk.Label(card, text="02  下載格式", style="Section.TLabel").pack(anchor=tk.W)
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill=tk.X, pady=(5, 0))
        self.video_format_var = tk.StringVar(value=self.config.get("video_format"))
        self.audio_format_var = tk.StringVar(value=self.config.get("audio_format"))
        for column, (label, variable, values) in enumerate((
            ("影片畫質", self.video_format_var, VIDEO_FORMATS),
            ("音訊格式", self.audio_format_var, AUDIO_FORMATS),
        )):
            group = ttk.Frame(row, style="Card.TFrame")
            group.grid(row=0, column=column, sticky="ew", padx=(0, 12) if column == 0 else (0, 0))
            row.columnconfigure(column, weight=1)
            ttk.Label(group, text=label, style="Muted.TLabel").pack(anchor=tk.W, pady=(0, 2))
            ttk.Combobox(group, textvariable=variable, values=list(values), state="readonly").pack(fill=tk.X)

    def _create_path_section(self, parent):
        card = self._card(parent)
        ttk.Label(card, text="03  儲存位置", style="Section.TLabel").pack(anchor=tk.W)
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill=tk.X, pady=(5, 0))
        self.path_entry = ttk.Entry(row)
        self.path_entry.insert(0, self.config.get_download_path())
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ttk.Button(row, text="瀏覽", command=self._browse_path).pack(side=tk.LEFT)

    def _create_button_section(self, parent):
        row = ttk.Frame(parent, style="App.TFrame")
        row.pack(fill=tk.X, pady=(0, 6))
        self.download_video_btn = ttk.Button(row, text="下載影片", style="Primary.TButton",
                                             command=lambda: self._start_download(DOWNLOAD_TYPE_VIDEO))
        self.download_video_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.download_audio_btn = ttk.Button(row, text="下載音樂",
                                             command=lambda: self._start_download(DOWNLOAD_TYPE_AUDIO))
        self.download_audio_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.cancel_btn = ttk.Button(row, text="取消下載", command=self._cancel_download, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.batch_control_frame = ttk.Frame(row, style="App.TFrame")
        self.clear_queue_btn = ttk.Button(self.batch_control_frame, text="清除佇列", command=self._clear_batch_queue)
        self.clear_queue_btn.pack(side=tk.LEFT)

    def _create_progress_section(self, parent):
        card = self._card(parent)
        heading = ttk.Frame(card, style="Card.TFrame")
        heading.pack(fill=tk.X)
        ttk.Label(heading, text="下載進度", style="Section.TLabel").pack(side=tk.LEFT)
        self.status_label = ttk.Label(heading, text="就緒", style="Muted.TLabel")
        self.status_label.pack(side=tk.RIGHT)
        self.progress_bar = ttk.Progressbar(card, mode="determinate", style="Download.Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.progress_label = ttk.Label(card, text="", style="Muted.TLabel")
        self.progress_label.pack(anchor=tk.W)
        self.batch_progress_label = ttk.Label(card, text="", style="Muted.TLabel")
        self.batch_progress_label.pack(anchor=tk.W)

    def _create_message_section(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(14, 8))
        card.pack(fill=tk.BOTH, expand=True)
        heading = ttk.Frame(card, style="Card.TFrame")
        heading.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(heading, text="下載記錄", style="Section.TLabel").pack(side=tk.LEFT)
        ttk.Button(heading, text="清除記錄", command=self._clear_messages).pack(side=tk.RIGHT)
        self.message_text = scrolledtext.ScrolledText(card, height=3, state=tk.DISABLED, wrap=tk.WORD,
                                                       relief=tk.FLAT, background="#f8fafc", foreground="#43536a",
                                                       font=("Helvetica", 10), padx=8, pady=8)
        self.message_text.pack(fill=tk.BOTH, expand=True)

    def _create_status_bar(self, parent):
        """狀態顯示位於進度區。"""

    def _setup_bindings(self):
        """設定快捷鍵綁定"""
        self.url_entry.bind('<Control-v>', self._on_paste_key)
        self.url_entry.bind('<Return>', lambda e: self._start_download(DOWNLOAD_TYPE_VIDEO))

        # 視窗關閉事件
        self.master.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _toggle_mode(self):
        """切換單一/批次模式"""
        is_batch = self.mode_var.get() == "batch"
        
        if is_batch:
            self.batch_frame.pack(fill=tk.X, pady=(5, 0))
            self.batch_control_frame.pack(side=tk.LEFT, padx=5)
            self.url_entry.config(state=tk.DISABLED)
        else:
            self.batch_frame.pack_forget()
            self.batch_control_frame.pack_forget()
            self.url_entry.config(state=tk.NORMAL)
            
        self.is_batch_mode = is_batch
    
    def _load_batch_urls(self):
        """載入批次 URL 清單"""
        try:
            clipboard = self.master.clipboard_get()
            self.batch_text.delete(1.0, tk.END)
            self.batch_text.insert(1.0, clipboard)
        except tk.TclError:
            pass
    
    def _clear_batch_queue(self):
        """清除批次佇列"""
        if messagebox.askyesno("確認", "確定要清除所有批次任務嗎？"):
            cleared = self.batch_manager.clear_tasks()
            self.log_message("已清除批次佇列" if cleared else "正在取消下載，結束後會清除佇列")
            self._update_batch_progress()

    def _check_ffmpeg(self):
        """檢查 FFmpeg 是否安裝"""
        self.ffmpeg_available = is_ffmpeg_installed()
        if not self.ffmpeg_available:
            self.log_message("⚠️ 警告: FFmpeg 未安裝，音訊轉換功能將無法使用", "warning")
            self.download_audio_btn.config(state=tk.DISABLED)

    def _on_paste_key(self, event):
        """處理 Ctrl+V 快捷鍵"""
        self._paste_url()
        return "break"  # 阻止預設的貼上行為

    def _paste_url(self):
        """貼上 URL"""
        try:
            clipboard = self.master.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard)
        except tk.TclError:
            return

    def _browse_path(self):
        """瀏覽選擇路徑"""
        path = filedialog.askdirectory(initialdir=self.path_entry.get())
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)
            self.config.set_download_path(path)

    def _start_download(self, download_type: str):
        """開始下載"""
        if self.current_task or self.batch_manager.is_running:
            messagebox.showinfo("提示", "目前已有下載任務進行中")
            return

        output_path = self.path_entry.get().strip()
        
        if self.is_batch_mode:
            # 批次下載
            urls_text = self.batch_text.get(1.0, tk.END).strip()
            if not urls_text:
                messagebox.showerror("錯誤", "請輸入批次 URL 清單")
                return
                
            if download_type == DOWNLOAD_TYPE_VIDEO:
                format_option = self.video_format_var.get()
            else:
                format_option = self.audio_format_var.get()
                
            try:
                parse_batch_urls(urls_text)
                validate_download_format(download_type, format_option)
            except ValueError as exc:
                messagebox.showerror("錯誤", str(exc))
                return

            # 驗證成功後，才以目前輸入建立新批次。
            self.batch_manager.clear_tasks()
            count = self.batch_manager.add_urls_from_text(
                urls_text, download_type, format_option, output_path
            )
            
            if count == 0:
                messagebox.showerror("錯誤", "未找到有效的 URL")
                return
                
            # 開始批次下載
            self._set_downloading_state(True)
            if not self.batch_manager.start_batch_download():
                self._set_downloading_state(False)
                self.log_message("批次尚未結束或沒有待下載任務", "warning")
                return
            
            self.log_message(f"開始批次下載 {count} 個{'影片' if download_type == DOWNLOAD_TYPE_VIDEO else '音樂'}")
            
        else:
            # 單一下載
            url = self.url_entry.get().strip()
            if not url:
                messagebox.showerror("錯誤", ERROR_MESSAGES['empty_url'])
                return

            if download_type == DOWNLOAD_TYPE_VIDEO:
                format_option = self.video_format_var.get()
            else:
                format_option = self.audio_format_var.get()

            if not validate_url(url):
                messagebox.showerror("錯誤", ERROR_MESSAGES['invalid_url'])
                return
            try:
                validate_download_format(download_type, format_option)
            except ValueError as exc:
                messagebox.showerror("錯誤", str(exc))
                return

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
        if self.batch_manager.is_running:
            if messagebox.askyesno("確認", "確定要取消批次下載嗎？"):
                self.batch_manager.stop_batch_download()
                self.log_message("正在取消批次下載，請等待目前任務結束")
                self.status_label.config(text="正在取消…")
                self.cancel_btn.config(state=tk.DISABLED)
        elif self.current_task and messagebox.askyesno("確認", "確定要取消下載嗎？"):
            self.current_task.cancel()
            self.log_message("使用者取消下載")

    def _on_progress(self, data: dict):
        """進度更新回調"""
        self.message_queue.put(('progress', data))

    def _on_complete(self, file_path: str, info: dict):
        """下載完成回調"""
        self.message_queue.put(('complete', (file_path, len(info.get('downloaded_files', [])))))

    def _on_error(self, error_msg: str):
        """錯誤回調"""
        self.message_queue.put(('error', error_msg))
    
    def _on_batch_progress(self, data: dict):
        """批次進度回調"""
        self.message_queue.put(('batch_progress', data))
    
    def _on_batch_task_complete(self, task_info, summary: dict):
        """批次任務完成回調"""
        self.message_queue.put(('batch_task_complete', (task_info, summary)))
    
    def _on_batch_complete(self, summary: dict):
        """批次完成回調"""
        self.message_queue.put(('batch_complete', summary))

    def _process_message_queue(self):
        """處理訊息佇列（在主執行緒）"""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()

                if msg_type == 'progress':
                    self._update_progress(data)
                elif msg_type == 'complete':
                    self._handle_complete(data)
                elif msg_type == 'error':
                    self._handle_error(data)
                elif msg_type == 'state':
                    self._set_downloading_state(data)
                elif msg_type == 'batch_progress':
                    self._update_batch_progress(data)
                elif msg_type == 'batch_task_complete':
                    task_info, summary = data
                    self._handle_batch_task_complete(task_info, summary)
                elif msg_type == 'batch_complete':
                    self._handle_batch_complete(data)
        except queue.Empty:
            pass

        self.master.after(100, self._process_message_queue)

    def _update_progress(self, data: dict):
        """更新進度顯示"""
        status = data.get('status')

        if status == 'downloading':
            percentage_raw = data.get('percentage')
            speed_raw = data.get('speed')
            eta_raw = data.get('eta')
            downloaded_raw = data.get('downloaded')
            total_raw = data.get('total')

            def _num(v, default=0.0):
                return v if isinstance(v, (int, float)) else default

            percentage = max(0.0, min(100.0, _num(percentage_raw)))
            speed = _num(speed_raw)
            eta = _num(eta_raw, default=0)
            downloaded = _num(downloaded_raw)
            total = _num(total_raw)

            self.progress_bar['value'] = percentage

            speed_str = f"{format_size(speed)}/s" if speed > 0 else "計算中..."
            eta_str = format_time(eta) if eta > 0 else "計算中..."
            size_str = (
                f"{format_size(downloaded)} / {format_size(total)}" if total > 0
                else format_size(downloaded)
            )

            progress_text = (
                f"下載中: {percentage:.1f}% | {size_str} | 速度: {speed_str} | 剩餘: {eta_str}"
            )
            self.progress_label.config(text=progress_text)
            self.status_label.config(text=f"下載中... {percentage:.1f}%")

        elif status == 'finished':
            self.progress_bar['value'] = 100
            self.progress_label.config(text="處理中...")
            self.status_label.config(text="後處理中...")

    def _handle_complete(self, result):
        """處理下載完成"""
        file_path, playlist_count = result
        if playlist_count:
            self.log_message(f"✓ 播放清單下載完成：{playlist_count} 個檔案", "success")
        else:
            self.log_message(f"✓ 下載完成: {file_path}", "success")

        self.progress_bar['value'] = 0
        self.progress_label.config(text="")
        self.status_label.config(text="就緒")

        # 詢問是否開啟目錄
        if self.config.get("auto_open_directory", True):
            if messagebox.askyesno("下載完成", "是否開啟下載目錄？"):
                open_directory(os.path.dirname(file_path))

    def _handle_error(self, error_msg: str):
        """處理錯誤"""
        self.log_message(f"✗ 錯誤: {error_msg}", "error")
        messagebox.showerror("下載失敗", error_msg)

        self.progress_bar['value'] = 0
        self.progress_label.config(text="")
        self.status_label.config(text="發生錯誤")
    
    def _update_batch_progress(self, data: dict = None):
        """更新批次進度"""
        if data:
            # 更新單一任務進度
            self._update_progress(data)
            
        # 更新批次摘要
        summary = self.batch_manager.get_task_summary()
        if summary['total'] > 0:
            progress_text = (
                f"批次進度: {summary['current_index']}/{summary['total']} | "
                f"完成: {summary['completed']} | 失敗: {summary['failed']} | 已取消: {summary['cancelled']} | "
                f"等待: {summary['pending']}"
            )
            self.batch_progress_label.config(text=progress_text)
        else:
            self.batch_progress_label.config(text="")
    
    def _handle_batch_task_complete(self, task_info, summary: dict):
        """處理批次任務完成"""
        if task_info.status == TaskStatus.COMPLETED:
            self.log_message(f"✓ 批次任務完成: {task_info.downloaded_file}", "success")
        elif task_info.status == TaskStatus.FAILED:
            self.log_message(f"✗ 批次任務失敗: {task_info.url} - {task_info.error_message}", "error")
            
        self._update_batch_progress()
    
    def _handle_batch_complete(self, summary: dict):
        """處理批次完成"""
        label = "批次已取消" if summary.get('stopped') else "批次下載完成"
        self.log_message(
            f"{label}！總計: {summary['total']}, "
            f"成功: {summary['completed']}, 失敗: {summary['failed']}, "
            f"已取消: {summary['cancelled']}"
        )
        if summary.get('cleared'):
            self.log_message("已清除批次佇列")

        self.progress_bar['value'] = 0
        self.progress_label.config(text="")
        self.batch_progress_label.config(text="")
        self.status_label.config(text="就緒")
        
        self._set_downloading_state(False)
        
        # 詢問是否開啟目錄
        if not summary.get('stopped') and summary['completed'] > 0 and self.config.get("auto_open_directory", True):
            if messagebox.askyesno("批次下載完成", "是否開啟下載目錄？"):
                open_directory(self.path_entry.get().strip())

    def _set_downloading_state(self, is_downloading: bool):
        """設定下載中狀態"""
        if is_downloading:
            self.download_video_btn.config(state=tk.DISABLED)
            self.download_audio_btn.config(state=tk.DISABLED)
            self.cancel_btn.config(state=tk.NORMAL)
        else:
            self.download_video_btn.config(state=tk.NORMAL)
            self.download_audio_btn.config(state=tk.NORMAL if self.ffmpeg_available else tk.DISABLED)
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
        auto_convert = tk.BooleanVar(value=self.config.get("auto_convert_filename", True))
        ttk.Checkbutton(
            frame,
            text="自動將檔名轉換為繁體中文",
            variable=auto_convert
        ).pack(anchor=tk.W, pady=5)

        # 自動開啟目錄
        auto_open = tk.BooleanVar(value=self.config.get("auto_open_directory", True))
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
        if (self.current_task or self.batch_manager.is_running) and \
           messagebox.askyesno("確認", "下載進行中，確定要關閉程式嗎？"):
            self.download_manager.cancel_all()
            self.batch_manager.stop_batch_download()
            self.master.destroy()
        elif not self.current_task and not self.batch_manager.is_running:
            self.master.destroy()
