from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import py7zr
from archive_safety import Workspace, create_verified_archive
from test_app_filesystem import app_namespace, playlist


class ArchiveRecoveryTests(unittest.TestCase):
    def test_verified_roundtrip_and_collision_preserve_previous_archive(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Workspace.create(root)
            (workspace.path / 'audio').mkdir()
            payload = b'synthetic media\x00\x01' * 1024
            (workspace.path / 'audio' / 'track.mp3').write_bytes(payload)
            target = Path(root, 'playlist.7z')
            target.write_bytes(b'existing archive')
            result = Path(create_verified_archive(workspace.path, target))
            self.assertNotEqual(target, result)
            self.assertEqual(target.read_bytes(), b'existing archive')
            with py7zr.SevenZipFile(result) as archive:
                archive.extractall(Path(root, 'restore'))
            self.assertEqual((Path(root, 'restore') / workspace.path.name / 'audio' / 'track.mp3').read_bytes(), payload)
            workspace.cleanup()
            self.assertTrue(result.is_file())

    def test_integrity_failure_preserves_source_and_never_publishes_archive(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Workspace.create(root)
            sentinel = workspace.path / 'keep'
            sentinel.write_bytes(b'recover me')
            with patch.object(py7zr.SevenZipFile, 'testzip', return_value='corrupt member'):
                with self.assertRaises(ValueError):
                    create_verified_archive(workspace.path, Path(root, 'playlist.7z'))
            self.assertEqual(sentinel.read_bytes(), b'recover me')
            self.assertFalse(list(Path(root).glob('*.7z')))

    def test_application_compression_exception_retains_workspace_and_reports_failure(self):
        with tempfile.TemporaryDirectory() as root:
            def fail(*args):
                raise OSError('simulated disk full')
            ns = app_namespace(root, fail)
            with self.assertRaisesRegex(OSError, 'downloads were kept'):
                ns['process_json'](playlist(), 'Playlist', 'https://example.invalid')
            workspaces = list(Path(root).glob('.yje-work-*'))
            self.assertEqual(len(workspaces), 1)
            self.assertTrue((workspaces[0] / 'card.txt').is_file())

    def test_archive_write_failure_preserves_source_and_removes_partial_output(self):
        with tempfile.TemporaryDirectory() as root:
            workspace = Workspace.create(root)
            (workspace.path / 'keep').write_bytes(b'recover me')
            with patch.object(py7zr.SevenZipFile, 'writeall', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    create_verified_archive(workspace.path, Path(root, 'playlist.7z'))
            self.assertTrue((workspace.path / 'keep').exists())
            self.assertFalse(list(Path(root).glob('*.7z')))


if __name__ == '__main__':
    unittest.main()
