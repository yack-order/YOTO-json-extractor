"""Filesystem boundaries for untrusted playlist metadata."""
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import tempfile


def safe_filename(value, fallback="Untitled", limit=180):
    """Return a single portable filename component, never a special directory."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', '', str(value or '')).strip(' .')
    name = name.encode('utf-8')[:limit].decode('utf-8', errors='ignore').rstrip(' .')
    if not name or name.split('.')[0].upper() in {
        'CON', 'PRN', 'AUX', 'NUL',
        *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10)),
    }:
        return fallback
    return name


def output_path(directory, name):
    """Anchor a filename to the chosen output directory; reject existing symlinks."""
    root = Path(directory).resolve(strict=True)
    if not root.is_dir() or name != safe_filename(name) or Path(name).name != name:
        raise ValueError('Invalid output filename')
    target = root / name
    if target.is_symlink():
        raise ValueError('Refusing a symlink output')
    return str(target)


@dataclass(frozen=True)
class Workspace:
    root: Path
    path: Path
    identity: tuple

    @classmethod
    def create(cls, directory):
        root = Path(directory).resolve(strict=True)
        path = Path(tempfile.mkdtemp(prefix='.yje-work-', dir=root))
        info = path.stat()
        return cls(root, path, (info.st_dev, info.st_ino))

    def cleanup(self):
        """Remove only this fresh directory, never a reused or replaced directory."""
        info = self.path.lstat()
        if (self.path.parent != self.root or not self.path.name.startswith('.yje-work-')
                or self.path.is_symlink() or (info.st_dev, info.st_ino) != self.identity):
            raise ValueError('Workspace ownership changed; keeping files')
        shutil.rmtree(self.path)
