"""
工具函式測試
"""

import unittest
from src.utils.validators import validate_url
from src.utils.file_utils import sanitize_filename
from src.utils.system_utils import format_size, format_time


class TestValidators(unittest.TestCase):
    """驗證工具測試"""

    def test_validate_url(self):
        """測試 URL 驗證"""
        # 有效 URL
        self.assertTrue(validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(validate_url("http://example.com"))
        
        # 無效 URL
        self.assertFalse(validate_url(""))
        self.assertFalse(validate_url("not_a_url"))
        self.assertFalse(validate_url(None))


class TestFileUtils(unittest.TestCase):
    """檔案工具測試"""

    def test_sanitize_filename(self):
        """測試檔名清理"""
        self.assertEqual(sanitize_filename("test<>file.mp4"), "test__file.mp4")
        self.assertEqual(sanitize_filename("test|file?.mp4"), "test_file_.mp4")
        self.assertEqual(sanitize_filename("  test.mp4  "), "test.mp4")


class TestSystemUtils(unittest.TestCase):
    """系統工具測試"""

    def test_format_size(self):
        """測試檔案大小格式化"""
        self.assertEqual(format_size(1024), "1.00 KB")
        self.assertEqual(format_size(1048576), "1.00 MB")
        self.assertEqual(format_size(500), "500.00 B")

    def test_format_time(self):
        """測試時間格式化"""
        self.assertEqual(format_time(30), "30 秒")
        self.assertEqual(format_time(90), "1 分 30 秒")
        self.assertEqual(format_time(3661), "1 小時 1 分")


if __name__ == '__main__':
    unittest.main()

class TestDownloadValidation(unittest.TestCase):
    def test_complete_url_syntax(self):
        valid = [
            'https://www.youtube.com/watch?v=example&t=15',
            'https://example.technology:8443/path?q=a%20b#fragment',
            'http://localhost:8000/video',
            'http://127.0.0.1:8080/video',
            'http://[::1]:8080/video',
            'https://例子.台灣/影片',
        ]
        invalid = [
            '', 'not_a_url', 'ftp://example.com/video', 'https://',
            'https://example.com trailing', 'https://example.com\n/path',
            'https://example.com:abc/path', 'https://example.com:99999',
            'https://example.com:', 'https://-bad.example/', 'https://example..com/',
            'https://example.com/%zz', 'https://[::1]invalid/path',
            'https://example.com\\evil', 'http://999.999.999.999/',
        ]
        for url in valid:
            with self.subTest(url=url):
                self.assertTrue(validate_url(url))
        for url in invalid:
            with self.subTest(url=url):
                self.assertFalse(validate_url(url))

    def test_batch_validation_is_atomic(self):
        from src.core.batch_downloader import BatchDownloadManager
        manager = BatchDownloadManager()
        self.assertEqual(manager.add_urls_from_text('https://example.com/old', 'video', '720p', '/tmp'), 1)
        with self.assertRaisesRegex(ValueError, '第 2 項'):
            manager.add_urls_from_text('https://example.com/good,invalid', 'video', '720p', '/tmp')
        self.assertEqual([task.url for task in manager.tasks], ['https://example.com/old'])
        self.assertEqual(manager.task_queue.qsize(), 1)
        with self.assertRaisesRegex(ValueError, '格式'):
            manager.add_urls_from_text('https://example.com/good', 'video', 'OPUS', '/tmp')
        self.assertEqual(manager.task_queue.qsize(), 1)


if __name__ == '__main__':
    unittest.main()
