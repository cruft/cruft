import json
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError, run  # nosec
from typing import Any, Dict, Optional, Set

import click
import typer

from . import utils
from .utils import example
from .utils.iohelper import AltTemporaryDirectory


@example(skip_apply_ask=False)
@example()
def update(
    project_dir: Path = Path("."),
    cookiecutter_input: bool = False,
    refresh_private_variables: bool = False,
    skip_apply_ask: bool = True,
    skip_update: bool = False,
    checkout: Optional[str] = None,
    strict: bool = True,
    allow_untracked_files: bool = False,
    extra_context: Optional[Dict[str, Any]] = None,
    extra_context_file: Optional[Path] = None,
) -> bool:
    """Update specified project's cruft to the latest and greatest release."""
    cruft_file = utils.cruft.get_cruft_file(project_dir)

    if extra_context_file:
        if extra_context_file.samefile(cruft_file):
            typer.secho(
                f"The file path given to --variables-to-update-file cannot be the same as the"
                f" project's cruft file ({cruft_file}), as the update process needs"
                f" to know the old/original values of variables as well. Please specify a"
                f" different path, and the project's cruft file will be updated as"
                f" part of the process.",
                fg=typer.colors.RED,
            )
            return False

        extra_context_from_cli = extra_context
        with open(extra_context_file, "r") as extra_context_fp:
            extra_context = json.load(extra_context_fp) or {}
        extra_context = extra_context.get("context") or {}
        extra_context = extra_context.get("cookiecutter") or {}
        if extra_context_from_cli:
            extra_context.update(extra_context_from_cli)

    # If the project dir is a git repository, we ensure
    # that the user has a clean working directory before proceeding.
    if not _is_project_repo_clean(project_dir, allow_untracked_files):
        typer.secho(
            "Cruft cannot apply updates on an unclean git project."
            " Please make sure your git working tree is clean before proceeding.",
            fg=typer.colors.RED,
        )
        return False

    cruft_state = json.loads(cruft_file.read_text())

    directory = cruft_state.get("directory", "")
    if directory:
        directory = str(Path("repo") / directory)
    else:
        directory = "repo"

    with AltTemporaryDirectory(directory) as tmpdir_:
        # Initial setup
        tmpdir = Path(tmpdir_)
        repo_dir = tmpdir / "repo"
        current_template_dir = tmpdir / "current_template"
        new_template_dir = tmpdir / "new_template"
        deleted_paths: Set[Path] = set()
        # Clone the template
        with utils.cookiecutter.get_cookiecutter_repo(
            cruft_state["template"], repo_dir, checkout
        ) as repo:
            last_commit = repo.head.object.hexsha

            # Bail early if the repo is already up to date and no inputs are asked
            if not (
                extra_context or cookiecutter_input or refresh_private_variables
            ) and utils.cruft.is_project_updated(repo, cruft_state["commit"], last_commit, strict):
                typer.secho(
                    "Nothing to do, project's cruft is already up to date!", fg=typer.colors.GREEN
                )
                return True

            # Generate clean outputs via the cookiecutter
            # from the current cruft state commit of the cookiecutter and the updated
            # cookiecutter.
            # For the current cruft state, we do not try to update the cookiecutter_input
            # because we want to keep the current context input intact.
            _ = utils.generate.cookiecutter_template(
                output_dir=current_template_dir,
                repo=repo,
                cruft_state=cruft_state,
                project_dir=project_dir,
                checkout=cruft_state["commit"],
                deleted_paths=deleted_paths,
                update_deleted_paths=True,
            )
            # Remove private variables from cruft_state to refresh their values
            # from the cookiecutter template config
            if refresh_private_variables:
                _clean_cookiecutter_private_variables(cruft_state)

            # Add new input data from command line to cookiecutter context
            if extra_context:
                extra = cruft_state["context"]["cookiecutter"]
                for k, v in extra_context.items():
                    extra[k] = v

            new_context = utils.generate.cookiecutter_template(
                output_dir=new_template_dir,
                repo=repo,
                cruft_state=cruft_state,
                project_dir=project_dir,
                cookiecutter_input=cookiecutter_input,
                checkout=last_commit,
                deleted_paths=deleted_paths,
            )

        # Given the two versions of the cookiecutter outputs based
        # on the current project's context we calculate the diff and
        # apply the updates to the current project.
        if _apply_project_updates(
            current_template_dir,
            new_template_dir,
            project_dir,
            skip_update,
            skip_apply_ask,
            allow_untracked_files,
        ):
            # Update the cruft state and dump the new state
            # to the cruft file
            cruft_state["commit"] = last_commit
            cruft_state["checkout"] = checkout
            cruft_state["context"] = new_context
            cruft_file.write_text(utils.cruft.json_dumps(cruft_state))
            typer.secho(
                "Good work! Project's cruft has been updated and is as clean as possible!",
                fg=typer.colors.GREEN,
            )
        return True


def _clean_cookiecutter_private_variables(cruft_state: dict):
    for key in list(cruft_state["context"]["cookiecutter"].keys()):
        if key != "_template" and key.startswith("_"):
            del cruft_state["context"]["cookiecutter"][key]


#################################################
# Calculating project diff and applying updates #
#################################################


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


def _has_untracked_file(status_line: str):
    return status_line.strip().startswith("??")


def _is_project_repo_clean(directory: Path, allow_untracked_files: bool):
    if not _is_git_repo(directory):
        return True
    git_status = run(["git", "status", "--porcelain"], stdout=PIPE, stderr=DEVNULL, cwd=directory)
    status_lines = git_status.stdout.decode("utf-8").split("\n")
    # remove empty string from trailing newline
    status_lines = [line for line in status_lines if line]
    if allow_untracked_files:
        status_lines = [line for line in status_lines if not _has_untracked_file(line)]
    if status_lines:
        return False
    return True


def _apply_patch_with_rejections(diff: str, expanded_dir_path: Path):
    offset = _get_offset(expanded_dir_path)

    git_apply = ["git", "apply", "--reject"]
    if offset:
        git_apply.extend(["--directory", offset])

    try:
        run(
            git_apply,
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


def _apply_three_way_patch(diff: str, expanded_dir_path: Path, allow_untracked_files: bool):
    offset = _get_offset(expanded_dir_path)

    git_apply = ["git", "apply", "-3"]
    if offset:
        git_apply.extend(["--directory", offset])

    try:
        run(
            git_apply,
            input=diff.encode(),
            stderr=PIPE,
            stdout=PIPE,
            check=True,
            cwd=expanded_dir_path,
        )
    except CalledProcessError as error:
        typer.secho(error.stderr.decode(), err=True)
        if _is_project_repo_clean(expanded_dir_path, allow_untracked_files):
            typer.secho(
                "Failed to apply the update. Retrying again with a different update strategy.",
                fg=typer.colors.YELLOW,
            )
            _apply_patch_with_rejections(diff, expanded_dir_path)


def _get_offset(expanded_dir_path: Path):
    try:
        offset = (
            run(
                ["git", "rev-parse", "--show-prefix"],
                stderr=PIPE,
                stdout=PIPE,
                check=True,
                cwd=expanded_dir_path,
            )
            .stdout.decode()
            .strip()
        )
        return offset
    except CalledProcessError as error:
        if "not a git repository" in error.stderr.decode():
            return ""
        else:
            raise error


def _apply_patch(diff: str, expanded_dir_path: Path, allow_untracked_files: bool):
    # Git 3 way merge is the our best bet
    # at applying patches. But it only works
    # with git repos. If the repo is not a git dir
    # we fall back to git apply --reject which applies
    # diffs cleanly where applicable otherwise creates
    # *.rej files where there are conflicts
    if _is_git_repo(expanded_dir_path):
        _apply_three_way_patch(diff, expanded_dir_path, allow_untracked_files)
    else:
        _apply_patch_with_rejections(diff, expanded_dir_path)


def _apply_project_updates(
    old_main_directory: Path,
    new_main_directory: Path,
    project_dir: Path,
    skip_update: bool,
    skip_apply_ask: bool,
    allow_untracked_files: bool,
) -> bool:
    diff = utils.diff.get_diff(old_main_directory, new_main_directory)

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
                    utils.diff.display_diff(old_main_directory, new_main_directory)
                else:
                    click.secho("There are no changes.", fg=typer.colors.YELLOW)
        if input_str == "n":
            typer.echo("User cancelled Cookiecutter template update.")
            return False
        elif input_str == "s":
            skip_update = True

    if not skip_update and diff.strip():
        _apply_patch(diff, project_dir, allow_untracked_files)
    return True
