"""不啟動視窗，驗證桌面入口的輸入處理。"""
import unittest
from unittest.mock import MagicMock, patch

from src.core.batch_downloader import BatchDownloadManager
from src.ui.main_window import VideoDownloaderUI


class TestDesktopValidation(unittest.TestCase):
    def setUp(self):
        self.ui = VideoDownloaderUI.__new__(VideoDownloaderUI)
        self.ui.current_task = None
        self.ui.batch_manager = BatchDownloadManager()
        self.ui.download_manager = MagicMock()
        self.ui.path_entry = MagicMock()
        self.ui.path_entry.get.return_value = '/tmp'
        self.ui.video_format_var = MagicMock()
        self.ui.video_format_var.get.return_value = '720p'
        self.ui.audio_format_var = MagicMock()
        self.ui.audio_format_var.get.return_value = 'OPUS'
        self.ui.batch_text = MagicMock()
        self.ui.url_entry = MagicMock()
        self.ui._set_downloading_state = MagicMock()
        self.ui.log_message = MagicMock()

    def test_invalid_single_url_is_rejected_before_task_creation(self):
        self.ui.is_batch_mode = False
        self.ui.url_entry.get.return_value = 'https://example.com invalid'
        with patch('src.ui.main_window.messagebox.showerror') as showerror:
            self.ui._start_download('video')
        self.assertIn('URL', showerror.call_args.args[1])
        self.ui.download_manager.create_task.assert_not_called()
        self.ui._set_downloading_state.assert_not_called()

    def test_valid_single_input_creates_download_task(self):
        self.ui.is_batch_mode = False
        self.ui.url_entry.get.return_value = ' https://example.com/video '
        with patch('src.ui.main_window.threading.Thread') as thread:
            self.ui._start_download('video')
        self.assertEqual(self.ui.download_manager.create_task.call_args.kwargs['url'], 'https://example.com/video')
        thread.return_value.start.assert_called_once()
        self.ui._set_downloading_state.assert_called_once_with(True)

    def test_invalid_batch_preserves_existing_tasks(self):
        self.ui.is_batch_mode = True
        self.ui.batch_manager.add_urls_from_text('https://example.com/old', 'video', '720p', '/tmp')
        self.ui.batch_text.get.return_value = 'https://example.com/good, invalid'
        with patch('src.ui.main_window.messagebox.showerror') as showerror:
            self.ui._start_download('video')
        self.assertIn('第 2 項', showerror.call_args.args[1])
        self.assertEqual([task.url for task in self.ui.batch_manager.tasks], ['https://example.com/old'])
        self.assertFalse(self.ui.batch_manager.is_running)

    def test_invalid_format_is_rejected_before_clearing_batch(self):
        self.ui.is_batch_mode = True
        self.ui.batch_manager.add_urls_from_text('https://example.com/old', 'video', '720p', '/tmp')
        self.ui.batch_text.get.return_value = 'https://example.com/good'
        self.ui.video_format_var.get.return_value = 'OPUS'
        with patch('src.ui.main_window.messagebox.showerror') as showerror:
            self.ui._start_download('video')
        self.assertIn('格式', showerror.call_args.args[1])
        self.assertEqual([task.url for task in self.ui.batch_manager.tasks], ['https://example.com/old'])


if __name__ == '__main__':
    unittest.main()
