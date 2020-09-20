import json
from functools import partial
from pathlib import Path
from subprocess import run  # nosec

import pytest
from typer.testing import CliRunner

import cruft
from cruft._cli import app
from cruft._commands.utils import get_cruft_file


@pytest.fixture
def cruft_runner():
    runner = CliRunner()
    yield partial(runner.invoke, app)


@pytest.fixture
def cookiecutter_dir(tmpdir):
    yield Path(
        cruft.create("https://github.com/cruft/cookiecutter-test", Path(tmpdir), directory="dir")
    )


@pytest.fixture
def cookiecutter_dir_updated(tmpdir):
    yield Path(
        cruft.create(
            "https://github.com/cruft/cookiecutter-test",
            Path(tmpdir),
            directory="dir",
            checkout="updated",
        )
    )


def test_create(cruft_runner, tmpdir):
    result = cruft_runner(
        [
            "create",
            "--output-dir",
            str(tmpdir),
            "https://github.com/cruft/cookiecutter-test",
            "--directory",
            "dir",
            "-y",
        ]
    )
    assert result.exit_code == 0
    assert result.stdout == ""


def test_create_interactive(cruft_runner, tmpdir):
    result = cruft_runner(
        [
            "create",
            "--output-dir",
            str(tmpdir),
            "https://github.com/cruft/cookiecutter-test",
            "--directory",
            "dir",
        ],
        input="RANDOM_NAME\n",
    )
    assert result.exit_code == 0
    assert (Path(tmpdir) / "RANDOM_NAME").exists()


def test_check(cruft_runner, cookiecutter_dir):
    result = cruft_runner(["check", "--project-dir", str(cookiecutter_dir)])
    assert result.exit_code == 0


def test_check_strict(cruft_runner, cookiecutter_dir_updated):
    result = cruft_runner(["check", "--project-dir", str(cookiecutter_dir_updated)])
    assert result.exit_code == 1
    assert "failure" in result.stdout.lower()


def test_check_not_strict(cruft_runner, cookiecutter_dir_updated):
    result = cruft_runner(["check", "--project-dir", str(cookiecutter_dir_updated), "--not-strict"])
    assert result.exit_code == 0


def test_check_stale(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["check", "--project-dir", str(cookiecutter_dir), "--checkout", "updated"]
    )
    assert result.exit_code == 1
    assert "failure" in result.stdout.lower()


def test_link(cruft_runner, cookiecutter_dir):
    get_cruft_file(cookiecutter_dir).unlink()
    result = cruft_runner(
        [
            "link",
            "https://github.com/cruft/cookiecutter-test",
            "--project-dir",
            str(cookiecutter_dir),
            "-y",
            "--directory",
            "dir",
        ]
    )
    assert result.stdout == ""
    assert result.exit_code == 0


def test_link_interactive(cruft_runner, cookiecutter_dir):
    cruft_file = get_cruft_file(cookiecutter_dir)
    commit = json.loads(cruft_file.read_text())["commit"]
    cruft_file.unlink()
    result = cruft_runner(
        [
            "link",
            "https://github.com/cruft/cookiecutter-test",
            "--project-dir",
            str(cookiecutter_dir),
            "--directory",
            "dir",
        ],
        input=f"{commit}\n",
    )
    assert "Link to template at commit" in result.stdout
    assert result.exit_code == 0


def test_update_noop(cruft_runner, cookiecutter_dir):
    result = cruft_runner(["update", "--project-dir", str(cookiecutter_dir), "-y"])
    assert "Nothing to do" in result.stdout
    assert result.exit_code == 0


def test_update_unclean(cruft_runner, cookiecutter_dir):
    run(["git", "init"], cwd=cookiecutter_dir)
    result = cruft_runner(["update", "--project-dir", str(cookiecutter_dir), "-y"])
    assert "Cruft cannot apply updates on an unclean git project." in result.stdout
    assert result.exit_code == 1


def test_update(cruft_runner, cookiecutter_dir):
    result = cruft_runner(["update", "--project-dir", str(cookiecutter_dir), "-y", "-c", "updated"])
    assert "cruft has been updated" in result.stdout
    assert result.exit_code == 0


def test_update_with_conflicts(cruft_runner, cookiecutter_dir):
    with (cookiecutter_dir / "README.md").open("w") as f:
        f.write("conflicts")
    result = cruft_runner(["update", "--project-dir", str(cookiecutter_dir), "-y", "-c", "updated"])
    assert "cruft has been updated" in result.stdout
    assert "Project directory may have *.rej files" in result.stdout
    assert result.exit_code == 0
    assert set(cookiecutter_dir.glob("**/*.rej"))


def test_update_with_conflicts_with_git(cruft_runner, cookiecutter_dir):
    with (cookiecutter_dir / "README.md").open("w") as f:
        f.write("conflicts")
    # Commit the changes so that the repo is clean
    run(["git", "init"], cwd=cookiecutter_dir)
    run(["git", "add", "-A"], cwd=cookiecutter_dir)
    run(
        [
            "git",
            "-c",
            "user.name='test'",
            "-c",
            "user.email='user@test.com'",
            "commit",
            "-am",
            "test",
        ],
        cwd=cookiecutter_dir,
    )
    result = cruft_runner(["update", "--project-dir", str(cookiecutter_dir), "-y", "-c", "updated"])
    assert "cruft has been updated" in result.stdout
    assert result.exit_code == 0
    assert set(cookiecutter_dir.glob("**/*.rej"))
    assert "Project directory may have *.rej files" in result.stdout
    assert "Retrying again with a different update stratergy." in result.stdout


def test_update_interactive_cancelled(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", str(cookiecutter_dir), "-c", "updated"], input="n\n"
    )
    assert result.exit_code == 0
    assert "User cancelled Cookiecutter template update" in result.stdout


def test_update_interactive_skip(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", str(cookiecutter_dir), "-c", "updated"], input="s\n"
    )
    assert result.exit_code == 0
    assert "cruft has been updated" in result.stdout


def test_update_interactive_view(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", str(cookiecutter_dir), "-c", "updated"], input="v\ny\n"
    )
    assert result.exit_code == 0
    assert "cruft has been updated" in result.stdout


def test_update_not_strict(cruft_runner, cookiecutter_dir_updated):
    result = cruft_runner(
        ["update", "--project-dir", str(cookiecutter_dir_updated), "--not-strict"]
    )
    assert result.exit_code == 0
    assert "Nothing to do, project's cruft is already up to date" in result.stdout


def test_update_strict(cruft_runner, cookiecutter_dir_updated):
    result = cruft_runner(["update", "--project-dir", str(cookiecutter_dir_updated), "-y"])
    assert result.exit_code == 0
    assert "cruft has been updated" in result.stdout


def test_update_interactive_view_no_changes(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", str(cookiecutter_dir), "-c", "no-changes"], input="v\ny\n"
    )
    assert result.exit_code == 0
    assert "There are no changes" in result.stdout
    assert "cruft has been updated" in result.stdout


def test_update_interactive_view_no_changes_when_deleted(cruft_runner, cookiecutter_dir):
    # Remove the file that changed.
    (cookiecutter_dir / "README.md").unlink()
    result = cruft_runner(
        ["update", "--project-dir", str(cookiecutter_dir), "-c", "updated"], input="v\ny\n"
    )
    assert result.exit_code == 0
    assert "There are no changes" in result.stdout
    assert "cruft has been updated" in result.stdout
