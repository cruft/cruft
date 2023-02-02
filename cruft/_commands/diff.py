import json
import sys
from pathlib import Path
from typing import Iterable, Optional

import typer

from . import utils
from .utils.diff import _transfer_project_paths, _trim_ignored_paths
from .utils.iohelper import AltTemporaryDirectory


def diff(
    project_dir: Path = Path("."),
    include_paths: Optional[Iterable[Path]] = None,
    exit_code: bool = False,
    checkout: Optional[str] = None,
    reverse: Optional[bool] = None,
    respect_gitignore: bool = False,
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

            _trim_ignored_paths(
                include_paths=include_paths,
                project_dir=project_dir,
                target_dir=remote_template_dir,
                respect_gitignore=respect_gitignore,
            )

        # For a regular diff, files that are present in the template.
        # For a reverse diff, all project files.
        # The .gitignore of the project dir is respected if respect_gitignore is True
        # and the project directory is a repo.
        if reverse:
            source_path = project_dir
            prefixes = {
                "diff_src_prefix": utils.diff.DIFF_PRJ_PREFIX,
                "diff_dst_prefix": utils.diff.DIFF_SRC_PREFIX,
            }
        else:
            source_path = remote_template_dir
            prefixes = {
                "diff_src_prefix": utils.diff.DIFF_SRC_PREFIX,
                "diff_dst_prefix": utils.diff.DIFF_DST_PREFIX,
            }

        _transfer_project_paths(
            include_paths=include_paths,
            local_template_dir=local_template_dir,
            project_dir=project_dir,
            remote_template_dir=remote_template_dir,
            source_path=source_path,
        )

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
