from tempfile import TemporaryDirectory
from time import sleep


class AltTemporaryDirectory:
    def __init__(self):
        self.tmpdir = TemporaryDirectory()

    def __enter__(self):
        return self.tmpdir.name

    def cleanup(self, cnt=0):
        if cnt >= 5:  # pragma: no cover
            raise RuntimeError("Could not delete TemporaryDirectory!")
        try:
            self.tmpdir.cleanup()
        except IOError:  # pragma: no cov_4_nix
            sleep(1)
            self.cleanup(cnt + 1)

    def __exit__(self, exc, value, tb):
        self.cleanup()
