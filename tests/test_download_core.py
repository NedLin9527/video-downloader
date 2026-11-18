"""下載完成路徑的回歸測試。"""
import gc
import os
import shutil
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import yt_dlp

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
            task.info = None
            gc.collect()  # yt-dlp 的 file:// 測試來源會暫時保留 Windows 檔案控制代碼。

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
        with tempfile.TemporaryDirectory() as tmp:
            task = DownloadTask('https://example.com/video', 'video', tmp, '最高畫質')
            errors = []
            task.error_callback = errors.append
            with patch('src.core.downloader.yt_dlp.YoutubeDL') as mock_ydl:
                ydl = mock_ydl.return_value.__enter__.return_value
                ydl.extract_info.side_effect = [{'id': 'example'}, {}]
                ydl.process_ie_result.return_value = {'id': 'example'}
                self.assertFalse(task.execute())
            self.assertIn('最終檔案', errors[0])

    def test_playlist_skips_unavailable_entry_and_tracks_completed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = [str(Path(tmp) / name) for name in ('first.mp4', 'second.mp4')]
            completed = []
            task = DownloadTask(
                'https://www.youtube.com/playlist?list=example', 'video', tmp, '720p',
                complete_callback=lambda path, info: completed.append((path, info)),
            )
            raw = {'_type': 'playlist', 'entries': [{}, None, {}]}

            def download_playlist(info, download):
                self.assertIs(info, raw)
                self.assertTrue(download)
                for path in paths:
                    Path(path).write_bytes(b'video')
                    task._record_final_path(path)
                return {'_type': 'playlist', 'entries': [{}, None, {}]}

            with patch('src.core.downloader.yt_dlp.YoutubeDL') as mock_ydl, \
                 patch.object(task, '_convert_filename'):
                ydl = mock_ydl.return_value.__enter__.return_value
                ydl.extract_info.return_value = raw
                ydl.process_ie_result.side_effect = download_playlist
                self.assertTrue(task.execute())

            ydl.extract_info.assert_called_once_with(task.url, download=False, process=False)
            ydl.params.__setitem__.assert_called_once_with('ignoreerrors', True)
            self.assertEqual(task.downloaded_files, paths)
            self.assertEqual(completed[0][0], paths[-1])
            self.assertEqual(completed[0][1]['downloaded_files'], paths)

    def test_playlist_with_no_completed_files_reports_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = []
            task = DownloadTask(
                'https://www.youtube.com/playlist?list=example', 'video', tmp, '720p',
                error_callback=errors.append,
            )
            with patch('src.core.downloader.yt_dlp.YoutubeDL') as mock_ydl:
                ydl = mock_ydl.return_value.__enter__.return_value
                ydl.extract_info.return_value = {'_type': 'playlist', 'entries': [None]}
                ydl.process_ie_result.return_value = {'_type': 'playlist', 'entries': [None]}
                self.assertFalse(task.execute())
            self.assertIn('沒有成功下載的檔案', errors[0])

    @unittest.skipUnless(shutil.which('ffmpeg'), '需要 FFmpeg')
    def test_real_playlist_continues_after_unavailable_local_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.wav'
            with wave.open(str(source), 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(8000)
                wav.writeframes(b'\0\0' * 800)

            playlist_url = 'https://example.com/playlist'
            raw = {
                '_type': 'playlist', 'id': 'fixture', 'title': 'fixture',
                'extractor': 'generic', 'extractor_key': 'Generic',
                'entries': [
                    {'_type': 'url', 'url': (root / 'unavailable.wav').as_uri(), 'ie_key': 'Generic'},
                    {'_type': 'url', 'url': source.as_uri(), 'ie_key': 'Generic'},
                ],
            }
            task = DownloadTask(playlist_url, 'audio', str(root / 'output'), 'MP3 (192kbps)')
            original_extract = yt_dlp.YoutubeDL.extract_info
            original_options = task._get_ydl_options

            def extract(ydl, url, *args, **kwargs):
                if url == playlist_url:
                    return raw
                return original_extract(ydl, url, *args, **kwargs)

            with patch.object(yt_dlp.YoutubeDL, 'extract_info', new=extract), \
                 patch.object(task, '_get_ydl_options', side_effect=lambda: {
                     **original_options(), 'enable_file_urls': True, 'quiet': True,
                 }), \
                 patch.object(task, '_convert_filename'):
                self.assertTrue(task.execute())

            self.assertEqual(len(task.downloaded_files), 1)
            self.assertTrue(Path(task.downloaded_files[0]).is_file())
            self.assertEqual(Path(task.downloaded_files[0]).suffix, '.mp3')


if __name__ == '__main__':
    unittest.main()
