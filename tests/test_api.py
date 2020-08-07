import json
import os

import pytest
from cruft import api, exceptions
from examples import verify_and_test_examples
from git import Repo
from git.exc import GitCommandError
from hypothesis_auto import auto_pytest, auto_pytest_magic


def test_create_examples(tmpdir):
    tmpdir.chdir()
    verify_and_test_examples(api.create)


@auto_pytest(api.create)
def test_create_auto_invalid_repo(test_case, tmpdir):
    tmpdir.chdir()
    with pytest.raises(exceptions.InvalidCookiecutterRepository):
        test_case()


def test_check_examples(project_dir):
    with pytest.raises(exceptions.NoCruftFound):
        verify_and_test_examples(api.check)

    os.chdir(project_dir)
    verify_and_test_examples(api.check)


def test_update_and_check_real_repo(tmpdir):
    tmpdir.chdir()
    repo = Repo.clone_from("https://github.com/timothycrosley/cruft", str(tmpdir))
    repo.head.reset(commit="86a6e6beda8095690414ff7652c15b7ae36e6128", working_tree=True)
    with open(os.path.join(tmpdir, ".cruft.json")) as cruft_file:
        cruft = json.load(cruft_file)
        cruft["skip"] = ["cruft/__init__.py", "tests"]
    with open(os.path.join(tmpdir, ".cruft.json"), "w") as cruft_file:
        json.dump(cruft, cruft_file)
    repo_dir = str(tmpdir)
    assert not api.check(repo_dir)
    assert api.update(repo_dir, skip_apply_ask=True)


def test_update_examples(project_dir, tmpdir):
    tmpdir.chdir()
    with pytest.raises(exceptions.NoCruftFound):
        verify_and_test_examples(api.update)

    os.chdir(project_dir)
    verify_and_test_examples(api.update)


def test_link_examples(project_dir, tmpdir):
    os.chdir(project_dir)
    with pytest.raises(exceptions.CruftAlreadyPresent):
        verify_and_test_examples(api.link)

    tmpdir.chdir()
    Repo.clone_from("https://github.com/timothycrosley/cruft", str(tmpdir))
    os.remove(os.path.join(tmpdir, ".cruft.json"))
    verify_and_test_examples(api.link)
