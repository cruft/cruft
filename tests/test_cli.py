import json
from functools import partial
from pathlib import Path
from subprocess import run  # nosec
from textwrap import dedent

import pytest
from typer.testing import CliRunner

import cruft
from cruft._cli import app
from cruft._commands import utils


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


@pytest.fixture
def cookiecutter_dir_hooked_git(tmpdir):
    yield Path(
        cruft.create(
            # See pull request!
            "https://github.com/juhuebner/cookiecutter-test",
            Path(tmpdir),
            directory="dir",
            checkout="with-git-from-hook",
        )
    )


@pytest.fixture
def cookiecutter_dir_input(tmpdir):
    yield Path(
        cruft.create(
            "https://github.com/gmsantos/cookiecutter-test",
            Path(tmpdir),
            directory="dir",
            checkout="input",
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
    result = cruft_runner(["check", "--project-dir", cookiecutter_dir.as_posix()])
    assert result.exit_code == 0


def test_check_strict(cruft_runner, cookiecutter_dir_updated):
    result = cruft_runner(["check", "--project-dir", cookiecutter_dir_updated.as_posix()])
    assert result.exit_code == 1
    assert "failure" in result.stdout.lower()


def test_check_not_strict(cruft_runner, cookiecutter_dir_updated):
    result = cruft_runner(
        ["check", "--project-dir", cookiecutter_dir_updated.as_posix(), "--not-strict"]
    )
    assert result.exit_code == 0


def test_check_stale(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["check", "--project-dir", cookiecutter_dir.as_posix(), "--checkout", "updated"]
    )
    assert result.exit_code == 1
    assert "failure" in result.stdout.lower()


def test_link(cruft_runner, cookiecutter_dir):
    cruft_file = utils.cruft.get_cruft_file(cookiecutter_dir)
    cruft_config_from_create = json.loads(cruft_file.read_text())
    cruft_file.unlink()
    result = cruft_runner(
        [
            "link",
            "https://github.com/cruft/cookiecutter-test",
            "--project-dir",
            cookiecutter_dir.as_posix(),
            "-y",
            "--directory",
            "dir",
        ]
    )
    assert result.stdout == ""
    assert result.exit_code == 0

    # compare the 2 .cruft.json
    cruft_file = utils.cruft.get_cruft_file(cookiecutter_dir)
    cruft_config_from_link = json.loads(cruft_file.read_text())
    assert cruft_config_from_create == cruft_config_from_link


def test_link_interactive(cruft_runner, cookiecutter_dir):
    cruft_file = utils.cruft.get_cruft_file(cookiecutter_dir)
    cruft_config_from_create = json.loads(cruft_file.read_text())
    commit = cruft_config_from_create["commit"]
    cruft_file.unlink()
    result = cruft_runner(
        [
            "link",
            "https://github.com/cruft/cookiecutter-test",
            "--project-dir",
            cookiecutter_dir.as_posix(),
            "--directory",
            "dir",
        ],
        input=f"{commit}\n",
    )
    assert "Link to template at commit" in result.stdout
    assert result.exit_code == 0

    # compare the 2 .cruft.json (except for the "project" key)
    cruft_file = utils.cruft.get_cruft_file(cookiecutter_dir)
    cruft_config_from_link = json.loads(cruft_file.read_text())
    cruft_config_from_create["context"]["cookiecutter"].pop("project")
    cruft_config_from_link["context"]["cookiecutter"].pop("project")
    assert cruft_config_from_create == cruft_config_from_link


def test_link_checkout(cruft_runner, cookiecutter_dir_updated):
    cruft_file = utils.cruft.get_cruft_file(cookiecutter_dir_updated)
    cruft_config_from_create = json.loads(cruft_file.read_text())
    cruft_file.unlink()
    result = cruft_runner(
        [
            "link",
            "https://github.com/cruft/cookiecutter-test",
            "--project-dir",
            cookiecutter_dir_updated.as_posix(),
            "-y",
            "--directory",
            "dir",
            "--checkout",
            "updated",
        ]
    )
    assert result.exit_code == 0

    # compare the 2 .cruft.json
    cruft_file = utils.cruft.get_cruft_file(cookiecutter_dir_updated)
    cruft_config_from_link = json.loads(cruft_file.read_text())
    assert cruft_config_from_create == cruft_config_from_link


def test_update_noop(cruft_runner, cookiecutter_dir):
    result = cruft_runner(["update", "--project-dir", cookiecutter_dir.as_posix(), "-y"])
    assert "Nothing to do" in result.stdout
    assert result.exit_code == 0


def test_update_unclean(cruft_runner, cookiecutter_dir):
    run(["git", "init"], cwd=cookiecutter_dir)
    result = cruft_runner(["update", "--project-dir", cookiecutter_dir.as_posix(), "-y"])
    assert "Cruft cannot apply updates on an unclean git project." in result.stdout
    assert result.exit_code == 1


def test_update_allow_untracked_files(cruft_runner, cookiecutter_dir):
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
    (cookiecutter_dir / "new_file.txt").touch()
    result = cruft_runner(["update", "--project-dir", str(cookiecutter_dir), "-y"])
    assert "Cruft cannot apply updates on an unclean git project." in result.stdout
    assert result.exit_code == 1
    result = cruft_runner(
        [
            "update",
            "--project-dir",
            str(cookiecutter_dir),
            "-y",
            "--allow-untracked-files",
            "-c",
            "updated",
        ]
    )
    assert "cruft has been updated" in result.stdout
    assert result.exit_code == 0


def test_update(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-y", "-c", "updated"]
    )
    assert "cruft has been updated" in result.stdout
    assert result.exit_code == 0


def test_update_with_conflicts(cruft_runner, cookiecutter_dir):
    with (cookiecutter_dir / "README.md").open("w") as f:
        f.write("conflicts")
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-y", "-c", "updated"]
    )
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
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-y", "-c", "updated"]
    )
    assert "cruft has been updated" in result.stdout
    assert result.exit_code == 0
    assert set(cookiecutter_dir.glob("**/*.rej"))
    assert "Project directory may have *.rej files" in result.stdout
    assert "Retrying again with a different update strategy." in result.stdout


def test_update_interactive_cancelled(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-c", "updated"], input="n\n"
    )
    assert result.exit_code == 0
    assert "User cancelled Cookiecutter template update" in result.stdout


def test_update_interactive_skip(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-c", "updated"], input="s\n"
    )
    assert result.exit_code == 0
    assert "cruft has been updated" in result.stdout


def test_update_interactive_view(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-c", "updated"], input="v\ny\n"
    )
    assert result.exit_code == 0
    assert "cruft has been updated" in result.stdout


def test_update_not_strict(cruft_runner, cookiecutter_dir_updated):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir_updated.as_posix(), "--not-strict"]
    )
    assert result.exit_code == 0
    assert "Nothing to do, project's cruft is already up to date" in result.stdout


def test_update_strict(cruft_runner, cookiecutter_dir_updated):
    result = cruft_runner(["update", "--project-dir", cookiecutter_dir_updated.as_posix(), "-y"])
    assert result.exit_code == 0
    assert "cruft has been updated" in result.stdout


def test_update_when_new_file(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-c", "new-file"], input="y\n"
    )
    assert result.exit_code == 0
    assert (cookiecutter_dir / "new-file").exists()
    assert "cruft has been updated" in result.stdout


def test_update_when_file_moved(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-c", "file-moved"], input="y\n"
    )
    assert result.exit_code == 0
    assert (cookiecutter_dir / "NEW-README.md").exists()
    assert not (cookiecutter_dir / "README.md").exists()
    assert "cruft has been updated" in result.stdout


def test_update_interactive_view_no_changes(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-c", "no-changes"], input="v\ny\n"
    )
    assert result.exit_code == 0
    assert "There are no changes" in result.stdout
    assert "cruft has been updated" in result.stdout


def test_update_interactive_view_no_changes_when_deleted(cruft_runner, cookiecutter_dir):
    # Remove the file that changed.
    (cookiecutter_dir / "README.md").unlink()
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir.as_posix(), "-c", "updated"], input="v\ny\n"
    )
    assert result.exit_code == 0
    assert "There are no changes" in result.stdout
    assert "cruft has been updated" in result.stdout


def test_update_same_commit_but_ask_for_input(cruft_runner, cookiecutter_dir_input):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir_input.as_posix(), "-c", "input", "-y", "-i"],
        input="\n\n",  # no input changes
    )
    assert "cruft has been updated" in result.stdout
    assert result.exit_code == 0


def test_update_with_input_changes(cruft_runner, cookiecutter_dir_input, capfd):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir_input.as_posix(), "-c", "input", "-i"],
        input="test\nnew-input\nv\ny\n",
    )
    git_diff_captured = capfd.readouterr()
    assert "-Input from cookiecutter: some-input" in git_diff_captured.out
    assert "+Input from cookiecutter: new-input" in git_diff_captured.out
    assert "cruft has been updated" in result.stdout
    assert result.exit_code == 0


def test_update_new_inputs_added_to_template(cruft_runner, cookiecutter_dir_input, capfd):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir_input.as_posix(), "-c", "input-updated", "-i"],
        input="test\nsome-input\nnew-input-from-template\nv\ny\n",
    )
    git_diff_captured = capfd.readouterr()
    assert "-Initial" in git_diff_captured.out
    assert "+Updated" in git_diff_captured.out
    assert "+New input added from template: new-input-from-template" in git_diff_captured.out
    assert "cruft has been updated" in result.stdout
    assert result.exit_code == 0


def test_update_refresh_private_variables_from_template(
    cruft_runner, cookiecutter_dir_input, capfd
):
    result = cruft_runner(
        ["update", "--project-dir", cookiecutter_dir_input.as_posix(), "-c", "input-updated", "-r"],
        input="v\ny\n",
    )
    git_diff_captured = capfd.readouterr()
    assert "-Private variable: 1.0" in git_diff_captured.out
    assert "+Private variable: 2.0" in git_diff_captured.out
    assert "cruft has been updated" in result.stdout
    assert result.exit_code == 0


@pytest.mark.parametrize("args,expected_exit_code", [([], 0), (["--exit-code"], 1), (["-e"], 1)])
def test_diff_has_diff(args, expected_exit_code, cruft_runner, cookiecutter_dir):
    (cookiecutter_dir / "README.md").write_text("changed content\n")
    result = cruft_runner(["diff", "--project-dir", cookiecutter_dir.as_posix()] + args)
    assert result.exit_code == expected_exit_code
    assert result.stdout != ""


def test_diff_checkout(cruft_runner, cookiecutter_dir):
    result = cruft_runner(
        [
            "diff",
            "--project-dir",
            cookiecutter_dir.as_posix(),
            "--checkout",
            "updated",
            "--exit-code",
        ]
    )
    assert result.exit_code == 1
    assert result.stdout != ""


@pytest.mark.parametrize("args,expected_exit_code", [([], 0), (["--exit-code"], 0), (["-e"], 0)])
def test_diff_no_diff(args, expected_exit_code, cruft_runner, cookiecutter_dir):
    result = cruft_runner(["diff", "--project-dir", cookiecutter_dir.as_posix()] + args)
    assert result.exit_code == expected_exit_code
    assert result.stdout == ""


@pytest.mark.parametrize("args, expected_exit_code", [([], 0)])
def test_diff_skip_git_dir(args, expected_exit_code, cruft_runner, cookiecutter_dir_hooked_git):
    cookiecutter_dir = cookiecutter_dir_hooked_git
    print("cookiecutter_dir", cookiecutter_dir)
    # The two points below could as well be nicely stored within
    # a cookiecutter-test branch.
    # Write a skip section into pyproject.toml
    # This file is not (yet) in the test branch and is thus not diffed to the template.
    skip_section = """
        [tool.cruft]
        skip = [".git"]
        """
    with (cookiecutter_dir / "pyproject.toml").open("w") as f:
        f.write(dedent(skip_section))
    # Alter the git repo.
    # run(["git", "config", "--global", "user.email", "user@test.com"], cwd=cookiecutter_dir)
    # run(["git", "config", "--global", "user.name", "testm"], cwd=cookiecutter_dir)
    run(["git", "add", "--all"], cwd=cookiecutter_dir)
    run(["git", "commit", "-m", "2nd commit"], cwd=cookiecutter_dir)
    result = cruft_runner(["diff", "--project-dir", cookiecutter_dir.as_posix(), "--exit-code"])
    print(result.stdout)
    assert result.exit_code == expected_exit_code
    assert ".git" not in result.stdout
