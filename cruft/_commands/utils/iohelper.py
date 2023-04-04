import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from typing import Optional


class AltTemporaryDirectory:
    def __init__(self, directory: Optional[str] = None):
        self.tmpdir = TemporaryDirectory()
        self._extended_path = False
        self._directory = directory or ""
        name = str(Path(self.tmpdir.name) / self._directory)
        if name not in sys.path:
            self._extended_path = True
            sys.path.append(name)

    def __enter__(self):
        return self.tmpdir.name

    def cleanup(self, cnt=0):
        if self._extended_path:
            name = str(Path(self.tmpdir.name) / self._directory)
            if name in sys.path:
                sys.path.remove(name)
        if cnt >= 5:  # pragma: no cover
            raise RuntimeError("Could not delete TemporaryDirectory!")
        try:
            self.tmpdir.cleanup()
        except IOError:  # pragma: no cov_4_nix
            sleep(1)
            self.cleanup(cnt + 1)

    def __exit__(self, exc, value, tb):
        self.cleanup()
