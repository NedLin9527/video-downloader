"""版本來源與執行時顯示的一致性。"""
import tomllib
import unittest
from pathlib import Path

from src import __version__
from src.core.constants import APP_TITLE, APP_VERSION
from src.web.app import app


class TestVersionConsistency(unittest.TestCase):
    def test_package_desktop_and_web_share_version(self):
        self.assertEqual(APP_VERSION, __version__)
        self.assertEqual(APP_TITLE, f'影片下載器 v{__version__}')
        self.assertEqual(app.version, __version__)
        self.assertEqual(app.openapi()['info']['version'], __version__)

    def test_packaging_uses_the_same_version_source(self):
        root = Path(__file__).resolve().parents[1]
        with (root / 'pyproject.toml').open('rb') as file:
            metadata = tomllib.load(file)
        self.assertIn('version', metadata['project']['dynamic'])
        self.assertEqual(metadata['tool']['setuptools']['dynamic']['version']['attr'], 'src.__version__')
        self.assertEqual(metadata['project']['requires-python'], '>=3.11')


if __name__ == '__main__':
    unittest.main()
