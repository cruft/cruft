from pathlib import Path
from re import sub
from subprocess import PIPE, run  # nosec
from typing import List


def _git_diff(*args: str) -> List[str]:
    return ["git", "-c", "diff.noprefix=", "diff", "--no-index", "--relative", *args]


def get_diff(repo0: Path, repo1: Path) -> str:
    """Compute the raw diff between two repositories."""
    # Use Path methods in order to straighten out the differeneces between the the OSs.
    repo0_str = repo0.resolve().as_posix()
    repo1_str = repo1.resolve().as_posix()
    diff = run(
        _git_diff("--no-ext-diff", "--no-color", repo0_str, repo1_str),
        cwd=repo0_str,
        stdout=PIPE,
        stderr=PIPE,
    ).stdout.decode(encoding="utf-8", errors="ignore")

    # By default, git diff --no-index will output full paths like so:
    # --- a/tmp/tmpmp34g21y/remote/.coveragerc
    # +++ b/tmp/tmpmp34g21y/local/.coveragerc
    # We don't want this as we may need to apply the diff later on.
    # Note that diff headers contain repo0 and repo1 with both "a" and "b"
    # prefixes: headers for new files have a/repo1, headers for deleted files
    # have b/repo0.
    # NIX OPs have a/folder/file
    # WIN OPS have a/c:/folder/file
    for repo in [repo0_str, repo1_str]:
        # Make repo look like a NIX absolute path.
        repo = sub("/[a-z]:", "", repo)
        diff = diff.replace("a" + repo, "a").replace("b" + repo, "b")
        # if repo[0] == '/':
        #     # NIX case
        #     diff = diff.replace("a" + repo, "a").replace("b" + repo, "b")
        # else:
        #     # WIN case
        #     diff = diff.replace("a/" + repo, "a").replace("b/" + repo, "b")

    # This replacement is needed for renamed/moved files to be recognized properly
    # Renamed files in the diff don't have the "a" or "b" prefix and instead look like
    # /tmp/tmpmp34g21y/remote/.coveragerc
    # If we replace repo paths which are like /tmp/tmpmp34g21y/remote
    # we would end up with /.coveragerc which doesn't work.
    # We also need to replace the trailing slash. As a result, we only do
    # this after the above replacement is made as the trailing slash is needed there.
    diff = diff.replace(repo0_str + "/", "").replace(repo1_str + "/", "")

    return diff


def display_diff(repo0: Path, repo1: Path):
    """Display the diff between two repositories."""
    run(_git_diff(repo0.as_posix(), repo1.as_posix()))
