from tempfile import TemporaryDirectory
from time import sleep
import sys


class AltTemporaryDirectory:
    def __init__(self):
        self.tmpdir = TemporaryDirectory()
        self._extended_path = False
        name = self.tmpdir.name
        if name not in sys.path:
            self._extended_path = True
            sys.path.append(name)

    def __enter__(self):
        return self.tmpdir.name

    def cleanup(self, cnt=0):
        if self._extended_path:
            sys.path.remove(self.tmpdir.name)
        if cnt >= 5:  # pragma: no cover
            raise RuntimeError("Could not delete TemporaryDirectory!")
        try:
            self.tmpdir.cleanup()
        except IOError:  # pragma: no cov_4_nix
            sleep(1)
            self.cleanup(cnt + 1)

    def __exit__(self, exc, value, tb):
        self.cleanup()
