import json
import os
import re
import sys
from pathlib import Path
from subprocess import run

import pytest
from examples import verify_and_test_examples
from git import Repo

import cruft
from cruft import exceptions
from cruft._commands import utils


def test_invalid_cookiecutter_repo(tmpdir):
    with pytest.raises(exceptions.InvalidCookiecutterRepository):
        cruft.create("DNE", Path(tmpdir))


def test_invalid_cookiecutter_reference(tmpdir):
    with pytest.raises(exceptions.InvalidCookiecutterRepository):
        cruft.create("https://github.com/cruft/cookiecutter-test", Path(tmpdir), checkout="DNE")


def test_no_cookiecutter_dir(tmpdir):
    with pytest.raises(exceptions.UnableToFindCookiecutterTemplate):
        cruft.create("https://github.com/cruft/cookiecutter-test", Path(tmpdir))


def test_create_examples(tmpdir):
    tmpdir.chdir()
    verify_and_test_examples(cruft.create)


def test_check_examples(tmpdir, project_dir):
    tmpdir.chdir()
    with pytest.raises(exceptions.NoCruftFound):
        verify_and_test_examples(cruft.check)

    os.chdir(project_dir)
    verify_and_test_examples(cruft.check)


def test_create_with_skips(tmpdir):
    tmpdir.chdir()
    skips = ["setup.cfg"]
    cruft.create("https://github.com/timothycrosley/cookiecutter-python", Path(tmpdir), skip=skips)

    assert json.load((tmpdir / "python_project_name" / ".cruft.json").open("r"))["skip"] == skips


@pytest.mark.parametrize("value", ["main", None])
def test_create_stores_checkout_value(value, tmpdir):
    tmpdir.chdir()

    cruft.create(
        "https://github.com/timothycrosley/cookiecutter-python", Path(tmpdir), checkout=value
    )

    assert (
        json.load((tmpdir / "python_project_name" / ".cruft.json").open("r"))["checkout"] == value
    )


@pytest.mark.parametrize("value", ["main", None])
def test_link_stores_checkout_value(value, tmpdir):
    project_dir = Path(tmpdir)
    cruft.link(
        "https://github.com/timothycrosley/cookiecutter-python",
        project_dir=project_dir,
        checkout=value,
    )

    assert json.load(utils.cruft.get_cruft_file(project_dir).open("r"))["checkout"] == value


@pytest.mark.parametrize("value", ["main", None])
def test_update_stores_checkout_value(value, tmpdir):
    tmpdir.chdir()
    cruft.create(
        "https://github.com/timothycrosley/cookiecutter-python",
        Path(tmpdir),
        checkout="ea8f733f85e7089df338d41ace199d3f4d397e29",
    )
    project_dir = tmpdir / "python_project_name"

    cruft.update(Path(project_dir), checkout=value)

    assert json.load((project_dir / ".cruft.json").open("r"))["checkout"] == value


def test_update_and_check_real_repo(tmpdir):
    tmpdir.chdir()
    repo = Repo.clone_from("https://github.com/timothycrosley/cruft", str(tmpdir))
    repo.head.reset(commit="86a6e6beda8095690414ff7652c15b7ae36e6128", working_tree=True)
    with open(os.path.join(tmpdir, ".cruft.json")) as cruft_file:
        cruft_state = json.load(cruft_file)
        cruft_state["skip"] = ["cruft/__init__.py", "tests"]
    with open(os.path.join(tmpdir, ".cruft.json"), "w") as cruft_file:
        json.dump(cruft_state, cruft_file)
    repo_dir = Path(tmpdir)
    assert not cruft.check(repo_dir)
    # Update should fail since we have an unclean git repo
    assert not cruft.update(repo_dir)
    # Commit the changes so that the repo is clean
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
        cwd=repo_dir,
    )
    assert cruft.update(repo_dir, skip_apply_ask=True)


def test_update_allows_untracked_files_option(tmpdir):
    tmpdir.chdir()
    Repo.clone_from("https://github.com/timothycrosley/cruft", str(tmpdir))
    with open(os.path.join(tmpdir, "untracked.txt"), "w") as new_file:
        new_file.write("hello, world!\n")
    repo_dir = Path(tmpdir)
    # update should fail since repo is now unclean (has a tracked file)
    assert not cruft.update(repo_dir)
    # update should work if allow_untracked_files is True
    assert cruft.update(repo_dir, allow_untracked_files=True)


def test_relative_repo_check(tmpdir):
    tmpdir.chdir()
    temp_dir = Path(tmpdir)
    Repo.clone_from("https://github.com/cruft/cookiecutter-test", str(temp_dir / "cc"))
    project_dir = cruft.create("./cc", output_dir=str(temp_dir / "output"), directory="dir")
    assert cruft.check(project_dir)


def test_update_examples(project_dir, tmpdir):
    tmpdir.chdir()
    with pytest.raises(exceptions.NoCruftFound):
        verify_and_test_examples(cruft.update)

    os.chdir(project_dir)
    verify_and_test_examples(cruft.update)


def test_link_examples(project_dir, tmpdir):
    os.chdir(project_dir)
    with pytest.raises(exceptions.CruftAlreadyPresent):
        verify_and_test_examples(cruft.link)

    tmpdir.chdir()
    Repo.clone_from("https://github.com/timothycrosley/cruft", str(tmpdir))
    os.remove(os.path.join(tmpdir, ".cruft.json"))
    verify_and_test_examples(cruft.link)


def test_directory_and_checkout(tmpdir):
    output_path = cruft.create(
        "https://github.com/cruft/cookiecutter-test",
        output_dir=Path(tmpdir),
        directory="dir",
        checkout="initial",
    )
    cruft_file = utils.cruft.get_cruft_file(output_path)
    assert cruft_file.exists()
    assert cruft.check(output_path, checkout="initial")
    assert not cruft.check(output_path, checkout="updated")
    assert cruft.update(output_path, checkout="updated")
    assert cruft.check(output_path, checkout="updated")
    cruft_file.unlink()
    assert not cruft_file.exists()
    assert cruft.link(
        "https://github.com/cruft/cookiecutter-test",
        project_dir=output_path,
        directory="dir",
        checkout="updated",
    )
    assert cruft.check(output_path, checkout="updated")
    # Add checks for strictness where main is an older
    # version than updated
    assert not cruft.check(output_path, strict=True)
    assert cruft.check(output_path, strict=False)


@pytest.mark.parametrize(
    "exit_code,isatty,expect_reproducible_diff,expected_return_value",
    [
        (False, False, True, True),  # $ cruft diff | cat
        (False, True, False, True),  # $ cruft diff
        (True, False, True, False),  # $ cruft diff --exit-code | cat
        (True, True, False, False),  # $ cruft diff --exit-code
    ],
)
def test_diff_has_diff(
    exit_code, isatty, expect_reproducible_diff, expected_return_value, capfd, mocker, tmpdir
):
    mocker.patch.object(sys.stdout, "isatty", return_value=isatty)

    project_dir = cruft.create(
        "https://github.com/cruft/cookiecutter-test", Path(tmpdir), directory="dir", checkout="diff"
    )
    (project_dir / "file0").write_text("new content 0\n")
    (project_dir / "dir0/file1").write_text("new content 1\n")
    (project_dir / "dir0/file2").unlink()

    assert cruft.diff(project_dir, exit_code=exit_code) == expected_return_value

    captured = capfd.readouterr()
    stdout = captured.out
    stderr = captured.err

    assert stderr == ""

    expected_output = """diff --git upstream-template-old{tmpdir}/dir0/file1 upstream-template-new{tmpdir}/dir0/file1
index eaae237..ac3e272 100644
--- upstream-template-old{tmpdir}/dir0/file1
+++ upstream-template-new{tmpdir}/dir0/file1
@@ -1 +1 @@
-new content 1
+content1
diff --git upstream-template-old{tmpdir}/file0 upstream-template-new{tmpdir}/file0
index be6a56b..1fc03a9 100644
--- upstream-template-old{tmpdir}/file0
+++ upstream-template-new{tmpdir}/file0
@@ -1 +1 @@
-new content 0
+content0
"""
    expected_output_regex = re.escape(expected_output)
    expected_output_regex = expected_output_regex.replace(r"\{tmpdir\}", r"([^\n]*)")
    expected_output_regex = rf"^{expected_output_regex}$"

    match = re.search(expected_output_regex, stdout, re.MULTILINE)
    assert match is not None

    if expect_reproducible_diff:
        # If the output is not displayed to the user (for example when piping the result
        # of the "cruft diff" command) or if the user requested an exit code, we must make
        # sure the absolute path to the temporary directory does not appear in the diff
        # because the user might want to process the output.
        # Conversely, when the output is supposed to be displayed to the user directly (e.g.
        # when running "cruft diff" command directly in a terminal), absolute path to the
        # actual files on disk may be displayed because git diff command is called directly
        # without reprocessing by cruft. This delegates diff coloring and paging to git which
        # improves user experience. As far as I know, there is no way to ask git diff to not
        # display this path.
        assert set(match.groups()) == {""}


@pytest.mark.parametrize("exit_code", [(False,), (True,)])
def test_diff_no_diff(exit_code, capfd, mocker, tmpdir):
    project_dir = cruft.create(
        "https://github.com/cruft/cookiecutter-test", Path(tmpdir), directory="dir", checkout="diff"
    )

    assert cruft.diff(project_dir, exit_code=exit_code) is True

    captured = capfd.readouterr()
    stdout = captured.out
    stderr = captured.err

    assert stdout == ""
    assert stderr == ""


def test_diff_checkout(capfd, tmpdir):
    project_dir = cruft.create(
        "https://github.com/samj1912/cookiecutter-test",
        Path(tmpdir),
        directory="dir",
        checkout="master",
    )

    assert cruft.diff(project_dir, exit_code=True, checkout="updated") is False

    captured = capfd.readouterr()
    stdout = captured.out
    stderr = captured.err

    assert stderr == ""
    assert "--- upstream-template-old/README.md" in stdout
    assert "+++ upstream-template-new/README.md" in stdout
    assert "+Updated again" in stdout
    assert "-Updated" in stdout


def test_diff_git_subdir(capfd, tmpdir):
    tmpdir.chdir()
    temp_dir = Path(tmpdir)
    Repo.clone_from("https://github.com/cruft/cookiecutter-test", temp_dir)

    # Create something deeper in the git tree
    project_dir = cruft.create(
        "https://github.com/cruft/cookiecutter-test",
        Path("tmpdir/foo/bar"),
        directory="dir",
        checkout="master",
    )
    # not added & committed
    assert not cruft.update(project_dir)
    # Add & commit the changes so that the repo is clean
    run(["git", "add", "."], cwd=temp_dir)
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
        cwd=temp_dir,
    )

    assert cruft.update(project_dir, checkout="updated")


@pytest.mark.parametrize("is_reverse_diff", (True, False))
@pytest.mark.parametrize("use_exit_code", (True, False))
@pytest.mark.parametrize("commit_changes", (True, False))
@pytest.mark.parametrize("include_paths", (("dir0/file1", "dir2/file6"), ()))
def test_reverse_diff(is_reverse_diff, use_exit_code, commit_changes, include_paths, capfd, tmpdir):
    """Test reverse diff and its differences from the regular one."""

    branch = "diff"
    # Set up a test project from a template
    project_dir = cruft.create(
        "https://github.com/cruft/cookiecutter-test", Path(tmpdir), directory="dir", checkout=branch
    )

    # Make this a repo and commit its initial state.
    repo = Repo.init(project_dir)
    repo.git.add(all=True)
    repo.index.commit("Initial commit.")

    unchanged_file = "file0"
    updated_file = "dir0/file1"
    updated_and_ignored_file = "dir0/file2"
    deleted_file = "dir1/file3"
    new_file = "file4"
    new_and_ignored_file = "file5"
    new_directory = "dir2"
    new_directory_file = "file6"
    new_and_ignored_directory = "dir3"
    new_and_ignored_directory_file = "file7"

    (project_dir / updated_file).write_text("I have been updated.\n")
    (project_dir / updated_and_ignored_file).write_text("I have been updated.\n")
    (project_dir / deleted_file).unlink()
    (project_dir / new_file).write_text("I am new.")
    (project_dir / new_and_ignored_file).write_text("I am new and ignored.")
    (project_dir / new_directory).mkdir()
    (project_dir / new_directory / new_directory_file).write_text("I am new.")
    (project_dir / new_and_ignored_directory).mkdir()
    (project_dir / new_and_ignored_directory / new_and_ignored_directory_file).write_text(
        "I am new and in an ignored directory."
    )

    gitignore_content = "\n".join(
        f"/{path}"
        for path in [
            updated_and_ignored_file,
            new_and_ignored_file,
            new_and_ignored_directory,
        ]
    )
    (project_dir / ".gitignore").write_text(gitignore_content)

    # Results should be the same regardless of whether the project repo is dirty.
    if commit_changes:
        repo.git.add(all=True)
        repo.index.commit("Make changes to project.")

    # Sanity-check repo dirtiness
    assert repo.is_dirty() == (not commit_changes)

    exit_code = cruft._commands.diff(
        project_dir,
        include_paths=[Path(path) for path in include_paths],
        checkout=branch,
        exit_code=use_exit_code,
        reverse=is_reverse_diff,
    )
    captured = capfd.readouterr()
    stdout = captured.out
    stderr = captured.err

    # Check exit code
    assert exit_code == (not use_exit_code)

    # Check stderr
    assert stderr == ""

    # Check file changes reported are as expected.
    diff = stdout

    # File in both the template and repo that hasn't changed; shouldn't be in the diff.
    assert unchanged_file not in diff

    # Updated file that is in both the template and repo should always be in the diff.
    assert (updated_file in diff) == ((updated_file in include_paths) if include_paths else True)

    # Updated file that is ignored should be in both diffs.
    # Gitignore doesn't work on files that are already tracked.
    assert (updated_and_ignored_file in diff) == (
        (updated_and_ignored_file in include_paths) if include_paths else True
    )

    #  cruft._commands.utils.generate.cookiecutter_template already
    # filters out files that have been deleted in the project
    # before any comparison.
    assert deleted_file not in diff

    # New file in the project dir but not the template should be in the reverse diff only.
    assert (new_file in diff) == (
        is_reverse_diff and ((new_file in include_paths) if include_paths else True)
    )

    # New file that is ignored should be in neither diff.
    assert "I am new and ignored" not in diff

    # New directory that is in the project but not the template should be in reverse only.
    assert (new_directory in diff) == is_reverse_diff
    assert (new_directory_file in diff) == is_reverse_diff

    # New directory that is ignored should be in neither diff.
    assert "I am new and in an ignored directory." not in diff
