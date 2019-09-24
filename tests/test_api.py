import os

import pytest
from examples import verify_and_test_examples
from git.exc import GitCommandError
from hypothesis_auto import auto_pytest, auto_pytest_magic

from cruft import api, exceptions


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


def test_update_examples(project_dir, tmpdir):
    tmpdir.chdir()
    with pytest.raises(exceptions.NoCruftFound):
        verify_and_test_examples(api.update)

    os.chdir(project_dir)
    verify_and_test_examples(api.update)
