"""Web 本機啟動設定。"""
import unittest
from unittest.mock import patch

from src.web.app import run


class TestWebDefaults(unittest.TestCase):
    def test_run_binds_loopback(self):
        with patch('uvicorn.run') as run_server, patch.dict('os.environ', {'PORT': '8765'}):
            run()
        self.assertEqual(run_server.call_args.kwargs['host'], '127.0.0.1')
        self.assertEqual(run_server.call_args.kwargs['port'], 8765)


class TestWebRoutes(unittest.IsolatedAsyncioTestCase):
    async def request(self, method, path, body=b''):
        from src.web.app import app
        sent = []
        received = False

        async def receive():
            nonlocal received
            if not received:
                received = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return {'type': 'http.disconnect'}

        async def send(message):
            sent.append(message)

        scope = {'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
                 'method': method, 'scheme': 'http', 'path': path,
                 'raw_path': path.encode(), 'query_string': b'', 'root_path': '',
                 'headers': [(b'host', b'127.0.0.1'), (b'content-type', b'application/json')],
                 'client': ('127.0.0.1', 12345), 'server': ('127.0.0.1', 8000)}
        await app(scope, receive, send)
        return sent

    async def test_homepage_and_download_api(self):
        messages = await self.request('GET', '/')
        self.assertEqual(messages[0]['status'], 200)
        self.assertIn('最高畫質'.encode(), b''.join(m.get('body', b'') for m in messages))
        with patch('src.web.app.service.start_task', return_value='test-task'):
            messages = await self.request('POST', '/api/download',
                b'{"url":"https://example.com/video","download_type":"video","format_option":"720p"}')
        self.assertEqual(messages[0]['status'], 200)
        self.assertIn(b'test-task', b''.join(m.get('body', b'') for m in messages))

    async def test_invalid_inputs_return_422_without_starting_task(self):
        import json
        for payload in [
            {'url': 'https://example.com invalid', 'download_type': 'video', 'format_option': '720p'},
            {'url': 'https://example.com/video', 'download_type': 'video', 'format_option': 'OPUS'},
            {'url': 'https://example.com/video', 'download_type': 'audio', 'format_option': '720p'},
            {'url': 'https://example.com/video', 'download_type': 'other', 'format_option': '720p'},
        ]:
            with self.subTest(payload=payload), patch('src.web.app.service.start_task') as start:
                messages = await self.request('POST', '/api/download', json.dumps(payload).encode())
                self.assertEqual(messages[0]['status'], 422)
                self.assertIn('無效' if ' invalid' in payload['url'] else ('download_type' if payload['download_type'] == 'other' else '格式'),
                              b''.join(m.get('body', b'') for m in messages).decode())
                start.assert_not_called()
