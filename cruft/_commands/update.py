import json
import os
from pathlib import Path
from shutil import rmtree
from subprocess import DEVNULL, PIPE, CalledProcessError, run  # nosec
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional, Set

import click
import typer
from cookiecutter.generate import generate_files
from git import Repo

from .utils import (
    example,
    generate_cookiecutter_context,
    get_cookiecutter_repo,
    get_cruft_file,
    is_project_updated,
    json_dumps,
)

try:
    import toml  # type: ignore
except ImportError:  # pragma: no cover
    toml = None  # type: ignore

CruftState = Dict[str, Any]


@example(skip_apply_ask=False)
@example()
def update(
    project_dir: Path = Path("."),
    cookiecutter_input: bool = False,
    skip_apply_ask: bool = True,
    skip_update: bool = False,
    checkout: Optional[str] = None,
    strict: bool = True,
) -> bool:
    """Update specified project's cruft to the latest and greatest release."""
    pyproject_file = project_dir / "pyproject.toml"
    cruft_file = get_cruft_file(project_dir)

    # If the project dir is a git repository, we ensure
    # that the user has a clean working directory before proceeding.
    if not _is_project_repo_clean(project_dir):
        typer.secho(
            "Cruft cannot apply updates on an unclean git project."
            " Please make sure your git working tree is clean before proceeding.",
            fg=typer.colors.RED,
        )
        return False

    cruft_state = json.loads(cruft_file.read_text())

    with TemporaryDirectory() as compare_directory_str:
        # Initial setup
        compare_directory = Path(compare_directory_str)
        template_dir = compare_directory / "template"
        repo = get_cookiecutter_repo(cruft_state["template"], template_dir, checkout)
        directory = cruft_state.get("directory", None)
        if directory:
            template_dir = template_dir / directory
        last_commit = repo.head.object.hexsha

        # Bail early if the repo is already up to date
        if is_project_updated(repo, cruft_state["commit"], last_commit, strict):
            typer.secho(
                "Nothing to do, project's cruft is already up to date!", fg=typer.colors.GREEN
            )
            return True

        # Generate clean outputs via the cookiecutter
        # from the current cruft state commit of the cookiectter and the updated
        # cookiecutter.
        old_main_directory, new_main_directory, new_context = _generate_project_updates(
            compare_directory, cruft_state, template_dir, cookiecutter_input, repo
        )

        # Get all paths that we are supposed to skip before generating the diff and applying updates
        skip_paths = _get_skip_paths(cruft_state, pyproject_file)
        # We also get the list of paths that were deleted from the project
        # directory but were present in the template that the project is linked against
        # This is to avoid introducing changes that won't apply cleanly to the current project.
        deleted_paths = _get_deleted_files(old_main_directory, project_dir)
        # We now remove both the skipped and deleted paths from the new and old project
        _remove_paths(old_main_directory, new_main_directory, skip_paths | deleted_paths)
        # Given the two versions of the cookiecutter outputs based
        # on the current project's context we calculate the diff and
        # apply the updates to the current project.
        if _apply_project_updates(
            old_main_directory, new_main_directory, project_dir, skip_update, skip_apply_ask
        ):

            # Update the cruft state and dump the new state
            # to the cruft file
            cruft_state["commit"] = last_commit
            cruft_state["context"] = new_context
            cruft_state["directory"] = directory
            cruft_file.write_text(json_dumps(cruft_state))
            typer.secho(
                "Good work! Project's cruft has been updated and is as clean as possible!",
                fg=typer.colors.GREEN,
            )
        return True


#####################################
# Generating clean outputs for diff #
#####################################


def _generate_output(
    cruft_state: CruftState, template_dir: Path, cookiecutter_input: bool, new_output_dir: Path
):
    new_context = generate_cookiecutter_context(
        cruft_state["template"],
        template_dir,
        extra_context=cruft_state["context"]["cookiecutter"],
        no_input=not cookiecutter_input,
    )

    project_dir = generate_files(
        repo_dir=template_dir,
        context=new_context,
        overwrite_if_exists=True,
        output_dir=new_output_dir,
    )
    return new_context, Path(project_dir)


def _generate_project_updates(
    compare_directory: Path,
    cruft_state: CruftState,
    template_dir: Path,
    cookiecutter_input: bool,
    repo: Repo,
):
    new_output_dir = compare_directory / "new_output"

    new_context, new_main_directory = _generate_output(
        cruft_state, template_dir, cookiecutter_input, new_output_dir
    )

    repo.head.reset(commit=cruft_state["commit"], working_tree=True)

    old_output_dir = compare_directory / "old_output"
    # We should not prompt for the cookiecutter input for the current
    # project state
    _, old_main_directory = _generate_output(cruft_state, template_dir, False, old_output_dir)
    return old_main_directory, new_main_directory, new_context


##############################
# Removing unnecessary files #
##############################


def _get_skip_paths(cruft_state: CruftState, pyproject_file: Path) -> Set[Path]:
    skip_cruft = cruft_state.get("skip", [])
    if toml and pyproject_file.is_file():
        pyproject_cruft = toml.loads(pyproject_file.read_text()).get("tool", {}).get("cruft", {})
        skip_cruft.extend(pyproject_cruft.get("skip", []))
    return set(map(Path, skip_cruft))


def _get_deleted_files(template_dir: Path, project_dir: Path):
    cwd = Path.cwd()
    os.chdir(template_dir)
    template_paths = set(Path(".").glob("**/*"))
    os.chdir(cwd)
    os.chdir(project_dir)
    deleted_paths = set(filter(lambda path: not path.exists(), template_paths))
    os.chdir(cwd)
    return deleted_paths


def _remove_paths(old_main_directory: Path, new_main_directory: Path, paths_to_remove: Set[Path]):
    for path_to_remove in paths_to_remove:
        old_path = old_main_directory / path_to_remove
        new_path = new_main_directory / path_to_remove
        for path in (old_path, new_path):
            if path.is_dir():
                rmtree(path)
            elif path.is_file():
                path.unlink()


#################################################
# Calculating project diff and applying updates #
#################################################


def _get_diff(old_main_directory: Path, new_main_directory: Path):
    diff = run(
        [
            "git",
            "diff",
            "--no-index",
            "--no-ext-diff",
            "--no-color",
            str(old_main_directory),
            str(new_main_directory),
        ],
        stdout=PIPE,
        stderr=PIPE,
    ).stdout.decode()
    diff = diff.replace(str(old_main_directory), "").replace(str(new_main_directory), "")
    return diff


def _view_diff(old_main_directory: Path, new_main_directory: Path):
    run(["git", "diff", "--no-index", str(old_main_directory), str(new_main_directory)])


def _is_git_repo(directory: Path):
    # Taken from https://stackoverflow.com/a/16925062
    # This works even if we are in a sub folder in a git
    # repo
    output = run(
        ["git", "rev-parse", "--is-inside-work-tree"], stdout=PIPE, stderr=DEVNULL, cwd=directory
    )
    if b"true" in output.stdout:
        return True
    return False


def _is_project_repo_clean(directory: Path):
    if not _is_git_repo(directory):
        return True
    output = run(["git", "status", "--porcelain"], stdout=PIPE, stderr=DEVNULL, cwd=directory)
    if output.stdout.strip():
        return False
    return True


def _apply_patch_with_rejections(diff: str, expanded_dir_path: Path):
    try:
        run(
            ["git", "apply", "--reject"],
            input=diff.encode(),
            stderr=PIPE,
            stdout=PIPE,
            check=True,
            cwd=expanded_dir_path,
        )
    except CalledProcessError as error:
        typer.secho(error.stderr.decode(), err=True)
        typer.secho(
            (
                "Project directory may have *.rej files reflecting merge conflicts with the update."
                " Please resolve those conflicts manually."
            ),
            fg=typer.colors.YELLOW,
        )


def _apply_three_way_patch(diff: str, expanded_dir_path: Path):
    try:
        run(
            ["git", "apply", "-3"],
            input=diff.encode(),
            stderr=PIPE,
            stdout=PIPE,
            check=True,
            cwd=expanded_dir_path,
        )
    except CalledProcessError as error:
        typer.secho(error.stderr.decode(), err=True)
        if _is_project_repo_clean(expanded_dir_path):
            typer.secho(
                "Failed to apply the update. Retrying again with a different update stratergy.",
                fg=typer.colors.YELLOW,
            )
            _apply_patch_with_rejections(diff, expanded_dir_path)


def _apply_patch(diff: str, expanded_dir_path: Path):
    # Git 3 way merge is the our best bet
    # at applying patches. But it only works
    # with git repos. If the repo is not a git dir
    # we fall back to git apply --reject which applies
    # diffs cleanly where applicable otherwise creates
    # *.rej files where there are conflicts
    if _is_git_repo(expanded_dir_path):
        _apply_three_way_patch(diff, expanded_dir_path)
    else:
        _apply_patch_with_rejections(diff, expanded_dir_path)


def _apply_project_updates(
    old_main_directory: Path,
    new_main_directory: Path,
    project_dir: Path,
    skip_update: bool,
    skip_apply_ask: bool,
) -> bool:
    diff = _get_diff(old_main_directory, new_main_directory)

    if not skip_apply_ask and not skip_update:
        input_str: str = "v"
        while input_str == "v":
            typer.echo(
                'Respond with "s" to intentionally skip the update while marking '
                "your project as up-to-date or "
                'respond with "v" to view the changes that will be applied.'
            )
            input_str = typer.prompt(
                "Apply diff and update?",
                type=click.Choice(("y", "n", "s", "v")),
                show_choices=True,
                default="y",
            )
            if input_str == "v":
                if diff.strip():
                    _view_diff(old_main_directory, new_main_directory)
                else:
                    click.secho("There are no changes.", fg=typer.colors.YELLOW)
        if input_str == "n":
            typer.echo("User cancelled Cookiecutter template update.")
            return False
        elif input_str == "s":
            skip_update = True

    if not skip_update and diff.strip():
        _apply_patch(diff, project_dir)
    return True
