import shutil
from pathlib import Path
from re import sub
from subprocess import PIPE, run  # nosec
from typing import Iterable, List, Optional, Tuple

from git import InvalidGitRepositoryError, Repo

from cruft import exceptions

DIFF_SRC_PREFIX = "upstream-template-old"
DIFF_DST_PREFIX = "upstream-template-new"
DIFF_PRJ_PREFIX = "project-directory-old"


def _git_diff(
    *args: str, diff_src_prefix: str = DIFF_SRC_PREFIX, diff_dst_prefix: str = DIFF_DST_PREFIX
) -> List[str]:
    # https://git-scm.com/docs/git-diff#Documentation/git-diff.txt---binary support for binary patch
    return [
        "git",
        "-c",
        "diff.noprefix=",
        "diff",
        "--no-index",
        "--relative",
        "--binary",
        f"--src-prefix={diff_src_prefix}/",
        f"--dst-prefix={diff_dst_prefix}/",
        *args,
    ]


def get_diff(
    repo0: Path,
    repo1: Path,
    diff_src_prefix: str = DIFF_SRC_PREFIX,
    diff_dst_prefix: str = DIFF_DST_PREFIX,
) -> str:
    """Compute the raw diff between two repositories."""
    # Use Path methods in order to straighten out the differences between the OSs.
    repo0_str = repo0.resolve().as_posix()
    repo1_str = repo1.resolve().as_posix()
    try:
        diff_result = run(
            _git_diff(
                "--no-ext-diff",
                "--no-color",
                repo0_str,
                repo1_str,
                diff_src_prefix=diff_src_prefix,
                diff_dst_prefix=diff_dst_prefix,
            ),
            cwd=repo0_str,
            stdout=PIPE,
            stderr=PIPE,
        )
        diff = diff_result.stdout.decode()
    except UnicodeDecodeError:
        raise exceptions.ChangesetUnicodeError()

    # By default, git diff --no-index will output full paths like so:
    # --- a/tmp/tmpmp34g21y/remote/.coveragerc
    # +++ b/tmp/tmpmp34g21y/local/.coveragerc
    # We don't want this as we may need to apply the diff later on.
    # Note that diff headers contain repo0 and repo1 with both "a" and "b"
    # prefixes: headers for new files have a/repo1, headers for deleted files
    # have b/repo0.
    # NIX OPs have a/folder/file
    # WIN OPS have a/c:/folder/file
    # More info on git-diff can be found here: http://git-scm.com/docs/git-diff
    for repo in [repo0_str, repo1_str]:
        # Make repo look like a NIX absolute path.
        repo = sub("/[a-z]:", "", repo)
        diff = diff.replace(f"{diff_src_prefix}{repo}", diff_src_prefix).replace(
            f"{diff_dst_prefix}{repo}", diff_dst_prefix
        )
    # This replacement is needed for renamed/moved files to be recognized properly
    # Renamed files in the diff don't have the "a" or "b" prefix and instead look like
    # /tmp/tmpmp34g21y/remote/.coveragerc
    # If we replace repo paths which are like /tmp/tmpmp34g21y/remote
    # we would end up with /.coveragerc which doesn't work.
    # We also need to replace the trailing slash. As a result, we only do
    # this after the above replacement is made as the trailing slash is needed there.
    diff = diff.replace(repo0_str + "/", "").replace(repo1_str + "/", "")

    return diff


def display_diff(
    repo0: Path,
    repo1: Path,
    diff_src_prefix: str = DIFF_SRC_PREFIX,
    diff_dst_prefix: str = DIFF_DST_PREFIX,
):
    """Displays the diff between two repositories."""
    args = _git_diff(
        repo0.as_posix(),
        repo1.as_posix(),
        diff_src_prefix=diff_src_prefix,
        diff_dst_prefix=diff_dst_prefix,
    )
    run(args)


def _keep_and_ignore_paths(
    root: Path,
    start_path: Optional[Path] = None,
    include_paths: Optional[Iterable[Path]] = None,
    repo_path: Optional[Path] = None,
) -> Tuple[List[Path], List[Path]]:
    """Recursively classify paths by their include and gitignore status."""

    repo = None
    if start_path is None and repo_path is None:
        repo_path = root
    if repo_path is not None:
        try:
            repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            pass

    if not start_path:
        start_path = root

    # Make relative paths absolute
    include_paths = tuple((start_path / path) for path in include_paths) if include_paths else ()

    paths_to_keep: List[Path] = []
    paths_to_ignore: List[Path] = []

    for path in start_path.iterdir():
        if include_paths:
            if not (
                # Explicitly included
                (path in include_paths)
                # Parent of an included path
                or (
                    path
                    in [
                        parent_path
                        for include_path in include_paths
                        for parent_path in include_path.parents
                    ]
                )
                # Descendant of an included path
                or (set(include_paths).intersection(path.parents))
            ):
                paths_to_ignore.append(path)
                continue

        if repo_path and repo:
            # Get the path relative to the root and construct its equivalent under the repo
            # with the .gitignore we're consulting. This path may not actually exist. The root
            # of our scan may be separate, e.g. in the case of a template we want to filter by
            # the project's git. But we still want to know if we *would* ignore the path.
            relative_path = path.relative_to(start_path)
            path_to_check = repo_path / relative_path

            # Check if the path would be ignored by the repo we're consulting.
            if _should_ignore(repo, path_to_check):
                paths_to_ignore.append(path)
                # We needn't descend any further; subpaths of ignored directories should be
                # pruned by calling code; otherwise we might descend pointlessly into
                # .git, .tox, .mypy_cache and other large but irrelevant directories.
                continue

        if path.is_dir():
            # Recurse into the subdirectory.
            subpaths_to_keep, subpaths_to_ignore = _keep_and_ignore_paths(
                root,
                start_path=path,
                include_paths=include_paths,
                repo_path=repo_path,
            )
            paths_to_keep += subpaths_to_keep
            paths_to_ignore += subpaths_to_ignore
            if not subpaths_to_keep:
                # We're not interested in keeping this path as there's nothing
                # under it we want. Git doesn't bother with empty directories.
                continue

        # We're not ignoring this path, and if it's a directory, there's something
        # under it we want to keep.
        paths_to_keep.append(path)

    return sorted(paths_to_keep), sorted(paths_to_ignore)


def _should_ignore(repo, path) -> bool:
    if not isinstance(repo, Repo):
        return False
    if path.is_dir() and path.name == ".git":
        return True
    if repo.ignored(path):
        return True
    return False


def _trim_ignored_paths(
    target_dir: Path,
    project_dir: Path = Path("."),
    include_paths: Optional[Iterable[Path]] = None,
    respect_gitignore: bool = False,
):
    # We delete files from this generated directory that would be ignored by the
    # project, if respect_gitignore is True and the project directory (not the
    # template) is a repo.
    repo_path = project_dir if respect_gitignore else None
    _, paths_to_delete = _keep_and_ignore_paths(
        target_dir,
        include_paths=include_paths,
        repo_path=repo_path,
    )
    for path in paths_to_delete:
        if path.is_file():
            path.unlink()
        else:
            shutil.rmtree(path)


def _transfer_project_paths(
    local_template_dir: Path,
    remote_template_dir: Path,
    include_paths: Optional[Iterable[Path]] = None,
    project_dir: Path = Path("."),
    source_path=None,
):
    if source_path is None:
        source_path = remote_template_dir
    paths_to_copy, _ = _keep_and_ignore_paths(
        remote_template_dir,
        start_path=source_path,
        repo_path=source_path,
        include_paths=include_paths,
    )
    # Then we create a new tree with each file in the template that also exist
    # locally.
    for path in paths_to_copy:
        relative_path = path.relative_to(source_path)
        local_path = project_dir / relative_path
        destination = local_template_dir / relative_path
        if local_path.exists():
            if path.is_file():
                shutil.copy(str(local_path), str(destination))
            else:
                destination.mkdir(parents=True, exist_ok=True)
                destination.chmod(local_path.stat().st_mode)
