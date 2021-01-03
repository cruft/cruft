from pathlib import Path
from subprocess import PIPE, run  # nosec
from typing import List


def _git_diff(*args: str) -> List[str]:
    return ["git", "-c", "diff.noprefix=", "diff", "--no-index", "--relative", *args]


def get_diff(repo0: Path, repo1: Path) -> str:
    """Compute the raw diff between two repositories."""
    diff = run(
        _git_diff("--no-ext-diff", "--no-color", str(repo0), str(repo1)),
        cwd=str(repo0),
        stdout=PIPE,
        stderr=PIPE,
    ).stdout.decode()

    # By default, git diff --no-index will output full paths like so:
    # --- a/tmp/tmpmp34g21y/remote/.coveragerc
    # +++ b/tmp/tmpmp34g21y/local/.coveragerc
    # We don't want this as we may need to apply the diff later on.
    diff = diff.replace("a" + str(repo0), "a").replace("b" + str(repo1), "b")
    # This replacement is needed for renamed/moved files to be recognized properly
    # Renamed files in the diff don't have the "a" or "b" prefix and instead look like
    # /tmp/tmpmp34g21y/remote/.coveragerc
    # If we replace repo paths which are like /tmp/tmpmp34g21y/remote
    # we would end up with /.coveragerc which doesn't work.
    # We also need to replace the trailing slash. As a result, we only do
    # this after the above replacement is made as the trailing slash is needed there.
    diff = diff.replace(str(repo0) + "/", "").replace(str(repo1) + "/", "")
    return diff


def display_diff(repo0: Path, repo1: Path):
    """Displays the diff between two repositories."""
    run(_git_diff(str(repo0), str(repo1)))
