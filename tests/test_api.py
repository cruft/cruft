from examples import verify_and_test_examples
from git.exc import GitCommandError
from hypothesis_auto import auto_pytest

from cruft import api


def test_create_examples(tmpdir):
    tmpdir.chdir()
    verify_and_test_examples(api)


@auto_pytest(api.create)
def test_create(test_case, tmpdir):
    tmpdir.chdir()
    try:
        test_case()
    except (UnicodeEncodeError, GitCommandError, ValueError):
        pass
