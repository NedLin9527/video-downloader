"""
工具函式測試
"""

import unittest
import sys
import os

# 添加 src 目錄到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.validators import validate_url
from utils.file_utils import sanitize_filename
from utils.system_utils import format_size, format_time


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