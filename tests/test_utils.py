from pathlib import Path
from textwrap import dedent

import pytest

from cruft import exceptions
from cruft._commands import utils


def test_get_diff_with_add(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    repo1 = tmp_path / "repo1"

    repo0.mkdir()
    repo1.mkdir()

    (repo1 / "file").touch()

    diff = utils.diff.get_diff(repo0, repo1)

    assert diff.startswith("diff --git upstream-template-old/file upstream-template-new/file")


def test_get_diff_with_delete(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    repo1 = tmp_path / "repo1"

    repo0.mkdir()
    repo1.mkdir()

    (repo0 / "file").touch()

    diff = utils.diff.get_diff(repo0, repo1)

    assert diff.startswith("diff --git upstream-template-old/file upstream-template-new/file")


def test_get_diff_with_unicode(project_dir):
    with pytest.raises(exceptions.ChangesetUnicodeError):
        utils.diff.get_diff(
            Path(project_dir, "tests", "testdata", "unicode-data").absolute(),
            Path(project_dir, "tests", "testdata", "non-unicode-data").absolute(),
        )


def test_remove_paths_with_pathlib(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    (repo0 / "tests").mkdir(parents=True)

    (repo0 / "file").touch()
    (repo0 / "tests" / "test0.py").touch()
    (repo0 / "tests" / "test1.py").touch()

    utils.generate._remove_paths(repo0, {Path("tests/test0.py")})
    assert not (repo0 / "tests" / "test0.py").exists()
    assert (repo0 / "tests" / "test1.py").exists()


def test_remove_paths_with_string(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    (repo0 / "tests").mkdir(parents=True)

    (repo0 / "file").touch()
    (repo0 / "tests" / "test0.py").touch()
    (repo0 / "tests" / "test1.py").touch()

    utils.generate._remove_paths(repo0, {"tests/test0.py"})
    assert not (repo0 / "tests" / "test0.py").exists()
    assert (repo0 / "tests" / "test1.py").exists()


def test_remove_paths_with_glob_pattern(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    (repo0 / "tests").mkdir(parents=True)

    (repo0 / "file").touch()
    (repo0 / "tests" / "test0.py").touch()
    (repo0 / "tests" / "test1.py").touch()

    utils.generate._remove_paths(repo0, {"tests/*"})
    assert not (repo0 / "tests" / "test0.py").exists()
    assert not (repo0 / "tests" / "test1.py").exists()


def test_remove_paths_folder(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    (repo0 / "tests").mkdir(parents=True)

    (repo0 / "file").touch()
    (repo0 / "tests" / "test0.py").touch()
    (repo0 / "tests" / "test1.py").touch()

    utils.generate._remove_paths(repo0, {"tests", "file"})
    assert not (repo0 / "tests").exists()
    assert not (repo0 / "file").exists()


def test_remove_paths_with_glob_pattern_and_string(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    (repo0 / "tests").mkdir(parents=True)

    (repo0 / "file").touch()
    (repo0 / "tests" / "test0.py").touch()
    (repo0 / "tests" / "test1.py").touch()

    with pytest.warns(None) as warn_record:
        utils.generate._remove_paths(repo0, {5})  # type: ignore
    assert len(warn_record) != 0, "a warning should have been called as typing was off"
    assert (repo0 / "tests" / "test0.py").exists()
    assert (repo0 / "tests" / "test1.py").exists()


def test_warn_if_cant_read_pyproject_toml(monkeypatch):
    monkeypatch.setattr(utils.generate, "tomllib", None)
    with pytest.warns(UserWarning, match="`toml` package is not installed"):
        utils.generate._get_skip_paths({}, Path(__file__))


def test_get_extra_context_from_file():
    extra_context_file = Path(__file__).parent / "testdata" / "unicode-data" / "extra_context.json"
    extra_context = utils.cookiecutter.get_extra_context_from_file(extra_context_file)
    assert extra_context == {"project": "CRUFT-TEST-PROJECT"}


def test_remove_paths_with_get_skip_paths_from_cruft_state_and_pyproject_toml(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    repo0.mkdir(parents=True)

    (repo0 / "file0").touch()
    (repo0 / "file1").touch()

    (repo0 / "tests").mkdir(parents=True)
    (repo0 / "tests" / "test0.py").touch()
    (repo0 / "tests" / "test1.py").touch()

    (repo0 / "package" / "__pycache__").mkdir(parents=True)
    (repo0 / "package" / "__init__.py").touch()
    (repo0 / "package" / "test0.py").touch()
    (repo0 / "package" / "test1.py").touch()
    (repo0 / "package" / "__pycache__" / "test0.cpython-38.pyc").touch()
    (repo0 / "package" / "__pycache__" / "test1.cpython-38.pyc").touch()
    (repo0 / "package" / "module" / "__pycache__").mkdir(parents=True)
    (repo0 / "package" / "module" / "__init__.py").touch()
    (repo0 / "package" / "module" / "__pycache__" / "test0.cpython-38.pyc").touch()
    (repo0 / "package" / "module" / "test0.py").touch()

    (repo0 / ".mypy_cache").mkdir(parents=True)
    (repo0 / ".mypy_cache" / "test0.json").touch()
    (repo0 / ".ruff_cache").mkdir(parents=True)
    (repo0 / ".ruff_cache" / "test0.json").touch()

    (repo0 / ".git").mkdir(parents=True)
    (repo0 / ".git" / "file").touch()
    (repo0 / ".git" / "tests").mkdir(parents=True)
    (repo0 / ".git" / "tests" / "test0.py").touch()

    pyproject = repo0 / "pyproject.toml"
    with pyproject.open("w") as f:
        f.write(
            dedent(
                """
            [tool.cruft]
            skip = [
                "file1",
                "tests/*",
                "**/__pycache__/",
                "**/__init__.py",
                "*_cache/",
            ]
            """
            )
        )

    paths_to_remove = utils.generate._get_skip_paths({"skip": [".git"]}, pyproject)
    utils.generate._remove_paths(repo0, paths_to_remove)

    assert (repo0 / "file0").exists()
    assert not (repo0 / "file1").exists()

    assert not (repo0 / ".git").exists()

    assert (repo0 / "tests").exists()
    assert not (repo0 / "tests" / "test0.py").exists()
    assert not (repo0 / "tests" / "test0.py").exists()

    assert not (repo0 / "package" / "__pycache__").exists()
    assert (repo0 / "package").exists()

    assert not (repo0 / "package" / "module" / "__pycache__").exists()
    assert (repo0 / "package" / "module").exists()

    assert not (repo0 / ".mypy_cache").exists()
    assert not (repo0 / ".ruff_cache").exists()
