import importlib
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from typing import Optional


def forget_modules_under(directory: Path) -> None:
    """Make Python import modules under directory again the next time they are needed.

    The module and its cached bytecode are dropped: a checkout changing a source file
    within the same second and to the same size would still match that bytecode.
    """
    directory = directory.resolve()
    for name, module in list(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if module_file and directory in Path(module_file).resolve().parents:
            cached = getattr(getattr(module, "__spec__", None), "cached", None)
            if cached:
                try:
                    Path(cached).unlink()
                except FileNotFoundError:
                    pass
            del sys.modules[name]
    importlib.invalidate_caches()


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
            forget_modules_under(Path(name))
        if cnt >= 5:  # pragma: no cover
            raise RuntimeError("Could not delete TemporaryDirectory!")
        try:
            self.tmpdir.cleanup()
        except IOError:  # pragma: no cov_4_nix
            sleep(1)
            self.cleanup(cnt + 1)

    def __exit__(self, exc, value, tb):
        self.cleanup()
