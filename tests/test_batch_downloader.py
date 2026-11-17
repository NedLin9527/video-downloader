"""以受控執行緒驗證批次停止、清除、重啟及重試。"""
import threading
import unittest
from unittest.mock import patch

from src.core.batch_downloader import BatchDownloadManager, TaskStatus


class FakeTask:
    def __init__(self, callbacks, started=None, release=None, success=False):
        self.callbacks = callbacks
        self.started = started
        self.release = release
        self.success = success
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def is_cancelled(self):
        return self.cancelled

    def execute(self):
        if self.started:
            self.started.set()
        if self.release and not self.release.wait(3):
            raise RuntimeError('測試等待逾時')
        if self.success and not self.cancelled:
            self.callbacks['complete_callback']('/tmp/result.mp4', {})
            return True
        self.callbacks['error_callback']('cancelled' if self.cancelled else 'failure')
        return False


class TestBatchStop(unittest.TestCase):
    def setUp(self):
        self.manager = BatchDownloadManager(max_retries=1)
        self.started = threading.Event()
        self.release = threading.Event()
        self.created = []
        self.summaries = []
        self.manager.batch_complete_callback = self.summaries.append

    def tearDown(self):
        self.release.set()
        if self.manager.worker_thread:
            self.manager.worker_thread.join(4)

    def queue(self, urls='https://example.com/one,https://example.com/two'):
        return self.manager.add_urls_from_text(urls, 'video', '720p', '/tmp')

    def install_factory(self, factory):
        def create_task(**kwargs):
            task = factory(kwargs)
            self.created.append(task)
            return task
        self.manager.download_manager.create_task = create_task
        self.manager.download_manager.remove_task = lambda task: None

    def join(self):
        self.manager.worker_thread.join(4)
        self.assertFalse(self.manager.worker_thread.is_alive())

    def test_stop_blocks_restart_until_worker_finishes_then_new_batch_works(self):
        self.install_factory(lambda callbacks: FakeTask(callbacks, self.started, self.release))
        self.assertEqual(self.queue(), 2)
        self.assertTrue(self.manager.start_batch_download())
        self.assertTrue(self.started.wait(2))
        self.manager.stop_batch_download()
        self.assertTrue(self.manager.is_running)
        self.assertFalse(self.manager.start_batch_download())
        self.assertEqual(self.queue('https://example.com/three'), 0)
        self.assertEqual(len(self.created), 1)
        self.assertEqual(self.manager.tasks[1].status, TaskStatus.CANCELLED)
        self.release.set()
        self.join()
        self.assertFalse(self.manager.is_running)
        self.assertEqual([t.status for t in self.manager.tasks], [TaskStatus.CANCELLED] * 2)
        self.assertEqual(self.summaries[0]['cancelled'], 2)
        self.assertEqual(self.summaries[0]['failed'], 0)
        self.assertEqual(self.manager.tasks[0].retry_count, 0)
        self.assertTrue(self.summaries[0]['stopped'])

        self.assertTrue(self.manager.clear_tasks())
        self.install_factory(lambda callbacks: FakeTask(callbacks, success=True))
        self.assertEqual(self.queue('https://example.com/three'), 1)
        self.assertTrue(self.manager.start_batch_download())
        self.join()
        self.assertEqual(self.manager.tasks[0].status, TaskStatus.COMPLETED)
        self.assertEqual(self.summaries[-1]['completed'], 1)

    def test_clear_waits_for_worker_before_removing_tasks(self):
        self.install_factory(lambda callbacks: FakeTask(callbacks, self.started, self.release))
        self.queue()
        self.assertTrue(self.manager.start_batch_download())
        self.assertTrue(self.started.wait(2))
        self.assertFalse(self.manager.clear_tasks())
        self.assertEqual(len(self.manager.tasks), 2)
        self.assertFalse(self.manager.start_batch_download())
        self.release.set()
        self.join()
        self.assertEqual(self.manager.tasks, [])
        self.assertTrue(self.manager.task_queue.empty())
        self.assertTrue(self.summaries[0]['cleared'])
        self.assertEqual(self.summaries[0]['cancelled'], 2)

    def test_stop_during_real_task_metadata_prevents_download(self):
        with patch('src.core.downloader.yt_dlp.YoutubeDL') as ydl_factory:
            ydl = ydl_factory.return_value.__enter__.return_value

            def extract_info(url, download):
                self.assertFalse(download)
                self.started.set()
                if not self.release.wait(3):
                    raise RuntimeError('測試等待逾時')
                return {}

            ydl.extract_info.side_effect = extract_info
            self.queue('https://example.com/one,https://example.com/two')
            self.assertTrue(self.manager.start_batch_download())
            self.assertTrue(self.started.wait(2))
            self.manager.stop_batch_download()
            self.assertFalse(self.manager.start_batch_download())
            self.release.set()
            self.join()
            self.assertEqual(ydl.extract_info.call_count, 1)
            self.assertEqual(self.summaries[0]['cancelled'], 2)
            self.assertEqual(self.summaries[0]['failed'], 0)

    def test_failures_still_retry_and_finish_as_failed(self):
        self.install_factory(lambda callbacks: FakeTask(callbacks))
        self.queue('https://example.com/one')
        self.assertTrue(self.manager.start_batch_download())
        self.join()
        self.assertEqual(len(self.created), 2)
        self.assertEqual(self.manager.tasks[0].status, TaskStatus.FAILED)
        self.assertEqual(self.manager.tasks[0].retry_count, 1)
        self.assertEqual(self.summaries[0]['failed'], 1)
        self.assertEqual(self.summaries[0]['cancelled'], 0)


if __name__ == '__main__':
    unittest.main()
