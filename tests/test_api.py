import json
import os
from pathlib import Path

import pytest
from examples import verify_and_test_examples
from git import Repo

import cruft
from cruft import exceptions
from cruft._commands.utils import get_cruft_file


def test_invalid_cookiecutter_repo(tmpdir):
    with pytest.raises(exceptions.InvalidCookiecutterRepository):
        cruft.create("DNE", Path(tmpdir))


def test_no_cookiecutter_dir(tmpdir):
    with pytest.raises(exceptions.UnableToFindCookiecutterTemplate):
        cruft.create("https://github.com/samj1912/cookiecutter-test", Path(tmpdir))


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
    assert cruft.update(repo_dir, skip_apply_ask=True)


def test_relative_repo_check(tmpdir):
    tmpdir.chdir()
    temp_dir = Path(tmpdir)
    Repo.clone_from("https://github.com/samj1912/cookiecutter-test", str(temp_dir / "cc"))
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
        "https://github.com/samj1912/cookiecutter-test",
        output_dir=Path(tmpdir),
        directory="dir",
        checkout="initial",
    )
    cruft_file = get_cruft_file(output_path)
    assert cruft_file.exists()
    assert cruft.check(output_path, checkout="initial")
    assert not cruft.check(output_path, checkout="updated")
    assert cruft.update(output_path, checkout="updated")
    assert cruft.check(output_path, checkout="updated")
    cruft_file.unlink()
    assert not cruft_file.exists()
    assert cruft.link(
        "https://github.com/samj1912/cookiecutter-test",
        project_dir=output_path,
        directory="dir",
        checkout="updated",
    )
    assert cruft.check(output_path, checkout="updated")
    # Add checks for strictness where master is an older
    # version than updated
    assert not cruft.check(output_path, strict=True)
    assert cruft.check(output_path, strict=False)
