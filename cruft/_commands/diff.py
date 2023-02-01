import json
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import typer
from git import InvalidGitRepositoryError, Repo

from . import utils
from .utils.iohelper import AltTemporaryDirectory


def diff(
    project_dir: Path = Path("."),
    include_paths: Optional[Iterable[Path]] = None,
    exit_code: bool = False,
    checkout: Optional[str] = None,
    reverse: Optional[bool] = None,
    respect_gitignore: Optional[bool] = None,
):
    """Show the diff between the project and the linked Cookiecutter template"""
    # By default, if it's a reverse diff we respect the project dir's .gitignore when
    # determining which paths to compare, but this is not necessary for regular diffs
    # as we only compare files which are present in the template.
    # We also don't bother with the .gitignore check if explicit paths are passed.
    if respect_gitignore is None:
        respect_gitignore = reverse and not include_paths

    cruft_file = utils.cruft.get_cruft_file(project_dir)
    cruft_state = json.loads(cruft_file.read_text())
    checkout = checkout or cruft_state.get("commit")

    has_diff = False
    with AltTemporaryDirectory() as tmpdir_:
        tmpdir = Path(tmpdir_)
        repo_dir = tmpdir / "repo"
        remote_template_dir = tmpdir / "remote"
        local_template_dir = tmpdir / "local"

        # Create all the directories
        remote_template_dir.mkdir(parents=True, exist_ok=True)
        local_template_dir.mkdir(parents=True, exist_ok=True)

        # Let's clone the template
        with utils.cookiecutter.get_cookiecutter_repo(
            cruft_state["template"], repo_dir, checkout=checkout
        ) as repo:
            # We generate the template for the revision expected by the project
            utils.generate.cookiecutter_template(
                output_dir=remote_template_dir,
                repo=repo,
                cruft_state=cruft_state,
                project_dir=project_dir,
                checkout=checkout,
                update_deleted_paths=True,
            )
            # We delete files from this generated directory that would be ignored by the
            # project, if respect_gitignore is True and the project directory (not the
            # template) is a repo.
            repo_path = project_dir if respect_gitignore else None
            _, paths_to_delete = _keep_and_ignore_paths(
                remote_template_dir,
                include_paths=include_paths,
                repo_path=repo_path,
            )
            for path in paths_to_delete:
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(path)

        # For a regular diff, files that are present in the template.
        # For a reverse diff, all project files.
        # The .gitignore of the project dir is respected if respect_gitignore is True
        # and the project directory is a repo.
        prefixes = {
            "diff_src_prefix": utils.diff.DIFF_SRC_PREFIX,
            "diff_dst_prefix": utils.diff.DIFF_DST_PREFIX,
        }
        if reverse:
            prefixes = {
                "diff_src_prefix": utils.diff.DIFF_PRJ_PREFIX,
                "diff_dst_prefix": utils.diff.DIFF_DST_PREFIX,
            }

        paths_to_copy, _ = _keep_and_ignore_paths(remote_template_dir, include_paths=include_paths)

        # Then we create a new tree with each file in the template that also exist
        # locally.
        for path in paths_to_copy:
            relative_path = path.relative_to(remote_template_dir)
            local_path = project_dir / relative_path
            destination = local_template_dir / relative_path
            if path.is_file():
                shutil.copy(str(local_path), str(destination))
            else:
                destination.mkdir(parents=True, exist_ok=True)
                destination.chmod(local_path.stat().st_mode)

        # Finally we can compute and print the diff.
        diff_direction = [local_template_dir, remote_template_dir]
        # Either but not both because that means diff_direction.reverse().reverse()
        # len({in_project, reverse} & {True, False}) == 2
        if reverse:
            diff_direction.reverse()

        diff = utils.diff.get_diff(*diff_direction, **prefixes)  # type: ignore

        if diff.strip():
            has_diff = True

            if exit_code or not sys.stdout.isatty():
                # The current shell doesn't run on a TTY or the "--exit-code" flag
                # is set. This means we're probably not displaying the diff to an
                # end-user. Let's just output the sanitized version of the diff.
                #
                # Note that we can't delegate this check to "git diff" command
                # because it would show absolute paths to files as we're working in
                # temporary, non-gitted directories. Doing so would prevent the user
                # from applying the patch later on as the temporary directories wouldn't
                # exist anymore.
                typer.echo(diff, nl=False)
            else:
                # We're outputing the diff to a real user. We can delegate the job
                # to git diff so that they can benefit from coloration and paging.
                # Ouputing absolute paths is less of a concern although it would be
                # better to find a way to make git shrink those paths.
                utils.diff.display_diff(*diff_direction, **prefixes)  # type: ignore

    return not (has_diff and exit_code)


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
    include_paths = tuple((root / path) for path in include_paths) if include_paths else ()

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
            relative_path = path.relative_to(root)
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
