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
    # Add checks for strictness where master is an older
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

    expected_output = """diff --git a{tmpdir}/dir0/file1 b{tmpdir}/dir0/file1
index ac3e272..eaae237 100644
--- a{tmpdir}/dir0/file1
+++ b{tmpdir}/dir0/file1
@@ -1 +1 @@
-content1
+new content 1
diff --git a{tmpdir}/file0 b{tmpdir}/file0
index 1fc03a9..be6a56b 100644
--- a{tmpdir}/file0
+++ b{tmpdir}/file0
@@ -1 +1 @@
-content0
+new content 0
"""
    expected_output_regex = re.escape(expected_output)
    expected_output_regex = expected_output_regex.replace(r"\{tmpdir\}", r"([^\n]*)")
    expected_output_regex = fr"^{expected_output_regex}$"

    match = re.search(expected_output_regex, stdout, re.MULTILINE)
    assert match is not None

    if expect_reproducible_diff:
        # If the output is not displayed to the user (for example when piping the result
        # of the "cruft diff" command) or if the user requested an exit code, we must make
        # sure the absolute path to the temporary directory does not appear in the diff
        # because the user might want to process the output.
        # Conversely, when the output is suposed to be displayed to the user directly (e.g.
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
    assert "--- a/README.md" in stdout
    assert "+++ b/README.md" in stdout
    assert "-Updated again" in stdout
    assert "+Updated" in stdout
