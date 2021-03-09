from pathlib import Path

from cruft._commands import utils


def test_get_diff_with_add(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    repo1 = tmp_path / "repo1"

    repo0.mkdir()
    repo1.mkdir()

    (repo1 / "file").touch()

    diff = utils.diff.get_diff(repo0, repo1)

    assert diff.startswith("diff --git a/file b/file")


def test_get_diff_with_delete(tmp_path: Path):
    repo0 = tmp_path / "repo0"
    repo1 = tmp_path / "repo1"

    repo0.mkdir()
    repo1.mkdir()

    (repo0 / "file").touch()

    diff = utils.diff.get_diff(repo0, repo1)

    assert diff.startswith("diff --git a/file b/file")


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
