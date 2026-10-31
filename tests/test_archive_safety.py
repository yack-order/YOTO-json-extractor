import os
from pathlib import Path
import tempfile
import unittest

from archive_safety import Workspace, output_path, safe_filename


class WorkspaceTests(unittest.TestCase):
    def test_untrusted_components_cannot_select_a_parent_or_absolute_path(self):
        for value in ('..', '.', '', '/', '\\', '../../outside', '/tmp/out', 'C:\\out', 'NUL', 'a\nb'):
            with self.subTest(value=value):
                name = safe_filename(value)
                self.assertNotIn(name, ('', '.', '..'))
                self.assertFalse(any(c in name for c in '/\\\n'))
                with tempfile.TemporaryDirectory() as root:
                    self.assertEqual(Path(output_path(root, name)).parent, Path(root).resolve())

    def test_existing_playlist_folder_survives_independent_workspace_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            existing = Path(root, 'playlist')
            existing.mkdir()
            sentinel = existing / 'keep.txt'
            sentinel.write_text('user data')
            first, second = Workspace.create(root), Workspace.create(root)
            self.assertNotEqual(first.path, second.path)
            (first.path / 'download').write_text('test')
            first.cleanup()
            self.assertEqual(sentinel.read_text(), 'user data')
            self.assertTrue(second.path.is_dir())
            second.cleanup()

    @unittest.skipIf(os.name == 'nt', 'symlink permissions differ on Windows')
    def test_symlink_output_and_replaced_workspace_are_rejected(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            link = Path(root, 'output.7z')
            link.symlink_to(Path(outside, 'target.7z'))
            with self.assertRaises(ValueError):
                output_path(root, link.name)
            workspace = Workspace.create(root)
            workspace.path.rmdir()
            workspace.path.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                workspace.cleanup()
            self.assertTrue(Path(outside).is_dir())


if __name__ == '__main__':
    unittest.main()
