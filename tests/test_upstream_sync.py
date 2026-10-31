import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import MagicMock

from app_loader import load_functions
from archive_safety import create_verified_archive
from test_app_filesystem import app_namespace, playlist


class UpstreamSyncTests(unittest.TestCase):
    def test_silent_toggle_changes_the_logger_state_and_suppresses_popups_when_reenabled(self):
        log, popup = MagicMock(), MagicMock()
        log.tag_ranges.return_value = []
        toggle = MagicMock()
        ns = {'silent_mode': True, 'silent_mode_toggle': toggle,
              'MESSAGE_TYPES': {'info': 'Info', 'warning': 'Warning', 'error': 'Error'},
              'log_text': log, 'messagebox': popup, 'redact_text': str,
              'ctk': types.SimpleNamespace(END='end'), 'tk': types.SimpleNamespace(SEL='sel')}
        load_functions({'toggle_silent_mode', 'announce_message'}, ns)
        toggle.get.return_value = 'off'
        ns['toggle_silent_mode']()
        self.assertFalse(ns['silent_mode'])
        popup.showinfo.assert_called_once()
        popup.reset_mock()
        toggle.get.return_value = 'on'
        ns['toggle_silent_mode']()
        self.assertTrue(ns['silent_mode'])
        popup.showinfo.assert_not_called()

    def test_retry_counter_is_incremented_only_by_the_batch_loop(self):
        ns = {'STATUS': {'ok': 1, 'retry': 2, 'fail': 3}}
        load_functions({'update_progress'}, ns)
        index, completed, attempts = ns['update_progress']('url', 2, 0, 0, 5, 1, None)
        self.assertEqual((index, completed, attempts), (0, 0, 5))

    def test_final_allowed_attempt_fetches_and_next_attempt_fails_without_fetching(self):
        for function, allowed, url in [('handle_url', 10, 'https://example.invalid'),
                                       ('handle_original_url', 3, 'https://yoto.io/ABCDE?s=synthetic')]:
            fetch = MagicMock(return_value=types.SimpleNamespace(status_code=200, text='{}'))
            ns = {'STATUS': {'ok': 1, 'retry': 2, 'fail': 3}, 'announce_message': lambda *a, **kw: None,
                  'MESSAGE_TYPES': {'info': 'Info', 'error': 'Error'}, 'ensure_https': lambda x: x,
                  'card_id_from_url': lambda x: 'ABCDE', 'access_token': 'synthetic', 'METADATA_LIMIT': 100,
                  'fetchURL_threading': fetch, 'process_response': lambda *a: 1,
                  'handle_json_data': lambda *a: 1, 'json': __import__('json')}
            load_functions({function}, ns)
            self.assertEqual(ns[function](url, allowed, 1), 1)
            self.assertEqual(ns[function](url, allowed + 1, 1), 3)
            self.assertEqual(fetch.call_count, 1)

    def test_resource_location_follows_source_or_bundle_instead_of_output_directory(self):
        root = Path(__file__).resolve().parents[1]
        system = types.SimpleNamespace()
        ns = {'sys': system, 'os': os, '__file__': str(root / 'YOTO.py')}
        load_functions({'resource_path'}, ns)
        self.assertEqual(Path(ns['resource_path']('YJE.ico')), root / 'YJE.ico')
        system._MEIPASS = '/synthetic-bundle'
        self.assertEqual(ns['resource_path']('YJE.ico'), '/synthetic-bundle/YJE.ico')

    def test_description_is_processed_with_author_and_null_description_stays_safe(self):
        for description, expected_demo in [('Discover: 2 tracks', True), (None, False)]:
            with self.subTest(description=description), tempfile.TemporaryDirectory() as root:
                data = playlist()
                data['props']['pageProps']['card']['metadata']['description'] = description
                captured = []
                def compress(src, dst):
                    captured.append(Path(src, 'card.txt').read_text())
                    return create_verified_archive(src, dst)
                ns = app_namespace(root, compress)
                ns['process_json'](data, 'Playlist', 'https://example.invalid')
                archives = list(Path(root).glob('*.7z'))
                self.assertEqual(len(archives), 1)
                self.assertEqual('[DEMO]' in archives[0].name, expected_demo)
                if description:
                    self.assertIn(description, captured[0])
                self.assertFalse(list(Path(root).glob('.yje-work-*')))


if __name__ == '__main__':
    unittest.main()
