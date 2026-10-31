import io
import json
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

from app_loader import load_functions
import privacy
from test_app_filesystem import app_namespace, playlist

PROTECTED = 'https://yoto.io/ABCDE?private=SYNTHETIC_CARD_SECRET'
MEDIA = 'https://media.example.invalid/path?signature=SYNTHETIC_MEDIA_SECRET'
PUBLIC = 'https://yoto.io/SHARE?share=SYNTHETIC_PUBLIC_SHARE'


class PrivacyTests(unittest.TestCase):
    def setUp(self):
        privacy._PUBLIC_LINKS.clear()
        privacy._SENSITIVE_VALUES.clear()

    def test_redaction_catches_urls_contacts_bearer_tokens_and_callback_fragments(self):
        text = privacy.redact_text(f'{PROTECTED} {MEDIA} person@example.invalid Authorization: Bearer SYNTHETIC_TOKEN access_token=OTHER_SECRET')
        for secret in ('SYNTHETIC_CARD_SECRET', 'SYNTHETIC_MEDIA_SECRET', 'person@', 'SYNTHETIC_TOKEN', 'OTHER_SECRET'):
            self.assertNotIn(secret, text)

    def test_only_explicit_nonofficial_sharing_field_is_preserved(self):
        data = playlist()
        card = data['props']['pageProps']['card']
        card.update(userId='yoto', shareLinkUrl=PROTECTED)
        privacy.register_public_links(data)
        self.assertNotIn(PROTECTED, privacy.redact_text(PROTECTED))
        card.update(userId='synthetic-creator', shareLinkUrl=PUBLIC)
        privacy.register_public_links(data)
        self.assertEqual(privacy.redact_text(PUBLIC), PUBLIC)
        card['shareLinkUrl'] = 'https://yoto.io.evil.invalid/SHARE'
        privacy.register_public_links(data)
        self.assertNotIn('evil.invalid', privacy.redact_text(card['shareLinkUrl']))

    def test_optional_json_is_scrubbed_recursive_and_never_overwrites_existing_file(self):
        data = playlist()
        card = data['props']['pageProps']['card']
        card.update(userId='synthetic-creator', shareLinkUrl=PUBLIC,
                    access_token='SYNTHETIC_TOKEN', email='person@example.invalid',
                    source=PROTECTED, nested=[{'refreshToken': 'SYNTHETIC_REFRESH', 'source': MEDIA}])
        privacy.register_public_links(data)
        with tempfile.TemporaryDirectory() as root:
            first = privacy.export_json(root, '..', data)
            second = privacy.export_json(root, '..', data)
            self.assertNotEqual(first, second)
            saved = Path(first).read_text()
            for secret in ('SYNTHETIC_TOKEN', 'SYNTHETIC_REFRESH', 'person@', 'SYNTHETIC_CARD_SECRET', 'SYNTHETIC_MEDIA_SECRET'):
                self.assertNotIn(secret, saved)
            self.assertIn(PUBLIC, saved)
            self.assertIn('access_token', card)  # source in memory stays untouched

    def test_production_json_modes_never_dump_raw_data_on_failure(self):
        with tempfile.TemporaryDirectory() as root:
            calls = []
            ns = app_namespace(root, lambda *a: None)
            ns.update(JSON_STATUS={'clean': 1, 'keep': 2, 'only': 3}, STATUS={'ok': 1, 'fail': 3},
                      register_public_links=privacy.register_public_links, export_json=privacy.export_json)
            load_functions({'handle_json_data'}, ns)
            data = playlist()
            data['props']['pageProps']['card']['access_token'] = 'SYNTHETIC_TOKEN'
            ns['process_json'] = lambda *args: (_ for _ in ()).throw(RuntimeError('SYNTHETIC_TOKEN'))
            self.assertEqual(ns['handle_json_data'](data, PROTECTED, 1), 3)
            self.assertFalse(list(Path(root).glob('*.json')))
            self.assertEqual(ns['handle_json_data'](data, PROTECTED, 3), 1)
            self.assertEqual(len(list(Path(root).glob('*.json'))), 1)
            self.assertNotIn('SYNTHETIC_TOKEN', next(Path(root).glob('*.json')).read_text())

    def test_actual_metadata_and_csv_are_redacted_and_csv_formulas_are_neutralized(self):
        with tempfile.TemporaryDirectory() as root:
            data = playlist('=2+2')
            data['props']['pageProps']['card']['metadata']['author'] = 'person@example.invalid'
            captured = []
            def compress(src, dst):
                captured.extend(p.read_text() for p in Path(src).glob('*.txt'))
                return dst
            ns = app_namespace(root, compress)
            ns['process_json'](data, '=2+2', PROTECTED)
            text = '\n'.join(captured) + Path(root, 'YJE-library-redacted.csv').read_text()
            self.assertNotIn('SYNTHETIC_CARD_SECRET', text)
            self.assertNotIn('person@', text)
            self.assertIn("'=2+2", text)

    def test_logger_and_log_exports_do_not_echo_exception_details(self):
        messages = []
        widget = types.SimpleNamespace(insert=lambda **kw: messages.append(kw['text']),
                                       tag_ranges=lambda *a: [], yview_moveto=lambda *a: None)
        ns = {'redact_text': privacy.redact_text, 'log_text': widget,
              'ctk': types.SimpleNamespace(END='end'), 'tk': types.SimpleNamespace(SEL='sel'),
              'silent_mode': True, 'MESSAGE_TYPES': {'info': 'Info'}}
        load_functions({'announce_message'}, ns)
        with patch('sys.stderr', new_callable=io.StringIO) as stderr:
            ns['announce_message'](PROTECTED, e=RuntimeError('SYNTHETIC_TOKEN'))
            self.assertEqual(stderr.getvalue(), '')
        self.assertNotIn('SYNTHETIC_TOKEN', ''.join(messages))
        with tempfile.TemporaryDirectory() as root:
            name = privacy.export_log(root, 'Failed-URLs', PROTECTED)
            self.assertNotIn('SYNTHETIC_CARD_SECRET', Path(name).read_text())

    def test_generated_data_and_credentials_are_ignored(self):
        paths = ['logs/run.log', 'playlist.json', 'YJE-library-redacted.csv', 'archive.7z',
                 '.env', 'tokens.txt', '.yje-work-example/card.txt', 'tests/__pycache__/x.pyc']
        result = subprocess.run(['git', 'check-ignore', '--no-index', '--stdin'],
                                input='\n'.join(paths), text=True, capture_output=True, check=True)
        self.assertEqual(set(result.stdout.splitlines()), set(paths))


if __name__ == '__main__':
    unittest.main()
