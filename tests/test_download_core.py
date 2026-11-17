"""下載完成路徑的回歸測試。"""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.core.downloader import DownloadTask


class TestDownloadOutput(unittest.TestCase):
    @unittest.skipUnless(shutil.which('ffmpeg'), '需要 FFmpeg')
    def test_real_audio_postprocessing_reports_existing_mp3(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / '视频.wav'
            subprocess.run([
                'ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                'sine=frequency=440:duration=0.2', '-y', str(source),
            ], check=True, capture_output=True)
            output = root / 'output'
            result = []
            task = DownloadTask(source.as_uri(), 'audio', str(output), 'MP3 (192kbps)',
                                complete_callback=lambda path, info: result.append(path))
            original_options = task._get_ydl_options

            def local_options():
                return {**original_options(), 'enable_file_urls': True, 'quiet': True}

            # 本機檔案作為可重複的輸入，實際執行 yt-dlp 與 FFmpeg 後處理。
            with patch('src.core.downloader.validate_url', return_value=True), \
                 patch.object(task, '_get_ydl_options', side_effect=local_options), \
                 patch('src.core.config.ConfigManager.get', side_effect=[False, True]):
                self.assertTrue(task.execute())
                self.assertTrue(task.execute())  # 重複執行同一任務
            self.assertEqual(len(result), 2)
            self.assertEqual(Path(result[-1]).name, '視頻.mp3')
            self.assertTrue(os.path.isfile(result[-1]))
            self.assertFalse(Path(result[-1]).with_suffix('.wav').exists())

    def test_invalid_format_and_url_do_not_launch_yt_dlp(self):
        cases = [
            ('https://example.com trailing', 'video', '720p', 'URL'),
            ('https://example.com/video', 'video', 'OPUS', '格式'),
            ('https://example.com/video', 'audio', '720p', '格式'),
            ('https://example.com/video', 'unknown', '720p', '類型'),
        ]
        for url, kind, selected_format, message in cases:
            with self.subTest(url=url, kind=kind, selected_format=selected_format):
                errors = []
                task = DownloadTask(url, kind, '/tmp', selected_format, error_callback=errors.append)
                with patch('src.core.downloader.yt_dlp.YoutubeDL') as mock_ydl:
                    self.assertFalse(task.execute())
                    mock_ydl.assert_not_called()
                self.assertIn(message, errors[0])

    def test_cancelled_before_start_does_not_open_yt_dlp(self):
        task = DownloadTask('https://example.com/video', 'video', '/tmp', '最高畫質')
        task.cancel()
        with patch('src.core.downloader.yt_dlp.YoutubeDL') as mock_ydl:
            self.assertFalse(task.execute())
            mock_ydl.assert_not_called()

    def test_missing_final_output_fails_instead_of_reporting_success(self):
        task = DownloadTask('https://example.com/video', 'video', '/tmp', '最高畫質')
        errors = []
        task.error_callback = errors.append
        with patch('src.core.downloader.yt_dlp.YoutubeDL') as mock_ydl:
            mock_ydl.return_value.__enter__.return_value.extract_info.return_value = {}
            self.assertFalse(task.execute())
        self.assertIn('最終檔案', errors[0])


if __name__ == '__main__':
    unittest.main()
