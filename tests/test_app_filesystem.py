from datetime import datetime
from contextlib import ExitStack
import json
import csv
import privacy
import os
from pathlib import Path
import re
import tempfile
import unittest

from app_loader import load_functions
from archive_safety import Workspace, output_path, safe_filename


def playlist(title='Playlist', category='test'):
    return {'props': {'pageProps': {'card': {
        'title': title, 'cardId': '../../ABCDE',
        'metadata': {'author': 'Author', 'category': category, 'languages': [],
                     'media': {'duration': 0, 'fileSize': 0}},
        'content': {'chapters': []},
    }}}}


def app_namespace(root, compress):
    return load_functions({'process_json', '_process_json', 'clean_filename', 'convert_seconds', 'convert_bytes'}, {
        'ExitStack': ExitStack, 'csv': csv, 'redact_text': privacy.redact_text, 'open_private_text': privacy.open_private_text, 'csv_cell': privacy.csv_cell,
        'os': os, 're': re, 'datetime': datetime, 'json': json,
        'Workspace': Workspace, 'output_path': output_path, 'safe_filename': safe_filename,
        'save_directory': root, 'compress_folder': compress,
        'announce_message': lambda *a, **kw: None,
        'MESSAGE_TYPES': {'info': 'Info', 'warning': 'Warning', 'error': 'Error'},
        'REGEX_DISCOVER': r'(Discover\: [0-9]+ track[s]?)',
    })


class AppFilesystemTests(unittest.TestCase):
    def test_real_processing_confines_malicious_metadata_and_preserves_existing_folder(self):
        with tempfile.TemporaryDirectory() as root:
            existing = Path(root, 'Playlist')
            existing.mkdir()
            (existing / 'keep').write_text('user data')
            seen = []
            def compress(src, dst):
                seen.append((Path(src), Path(dst)))
            ns = app_namespace(root, compress)
            ns['process_json'](playlist('..', '../../outside'), '..', 'https://example.invalid')
            self.assertEqual(len(seen), 1)
            src, dst = seen[0]
            self.assertEqual(src.parent, Path(root).resolve())
            self.assertEqual(dst.parent, Path(root).resolve())
            self.assertFalse(src.exists())
            self.assertEqual((existing / 'keep').read_text(), 'user data')


if __name__ == '__main__':
    unittest.main()
