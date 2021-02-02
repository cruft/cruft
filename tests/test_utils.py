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
