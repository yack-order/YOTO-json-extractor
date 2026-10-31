from pathlib import Path
import tempfile
import unittest

from app_loader import load_functions
from test_app_filesystem import app_namespace, playlist


class AppDownloadTests(unittest.TestCase):
    def test_legacy_adapter_calls_bounded_client_without_spawning_a_request_thread(self):
        calls = []
        ns = {'fetch_url': lambda *a, **kw: calls.append((a, kw)) or 'response'}
        load_functions({'fetchURL_threading'}, ns)
        self.assertEqual(ns['fetchURL_threading']('https://example.invalid', 'token', max_bytes=20), 'response')
        self.assertEqual(calls, [(('https://example.invalid', 'token'), {'max_bytes': 20})])

    def test_missing_audio_source_never_publishes_or_deletes_downloads(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []
            ns = app_namespace(root, lambda *a: calls.append(a))
            data = playlist()
            data['props']['pageProps']['card']['content']['chapters'] = [{'tracks': [{'title': 'missing audio'}]}]
            with self.assertRaisesRegex(ValueError, 'no downloadable audio'):
                ns['process_json'](data, 'Playlist', 'https://example.invalid')
            self.assertEqual(calls, [])
            self.assertEqual(len(list(Path(root).glob('.yje-work-*'))), 1)


if __name__ == '__main__':
    unittest.main()
