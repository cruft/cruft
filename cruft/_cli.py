"""This module defines CLI interactions when using `cruft`."""
import json
from pathlib import Path
from typing import List, Optional

import typer

from cruft import _commands, _logo

app = typer.Typer(help=_logo.ascii_art, no_args_is_help=True, add_completion=False)


def _get_help_string(function):
    return function.__doc__.split("\n\n")[0]


@app.command(
    short_help="Check if the linked Cookiecutter template has been updated",
    help=_get_help_string(_commands.check),
)
def check(
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-p", help="Path to the project directory.", show_default=False
    ),
    checkout: Optional[str] = typer.Option(
        None,
        "--checkout",
        "-c",
        help="The git reference to check against. Supports branches, tags and commit hashes.",
    ),
    strict: bool = typer.Option(
        True,
        "--strict/--not-strict",
        help=(
            "If enabled, ensures that the project commit is exactly"
            " the same as the checked out cookiecutter template."
            "If disabled, the check passes if the checked out cookiecutter template"
            " commit is an ancestor of the project commit."
        ),
    ),
) -> None:
    if not _commands.check(project_dir=project_dir, checkout=checkout, strict=strict):
        raise typer.Exit(1)


@app.command(
    short_help="Create a new project from a Cookiecutter template",
    help=_get_help_string(_commands.create),
)
def create(
    template_git_url: str = typer.Argument(
        ..., metavar="TEMPLATE", help="The Cookiecutter template URI."
    ),
    output_dir: Path = typer.Option(
        Path("."),
        dir_okay=True,
        file_okay=False,
        help="Where to output the generated project dir into",
    ),
    config_file: Optional[Path] = typer.Option(
        None, help="Path to the Cookiecutter user config file", exists=True
    ),
    default_config: bool = typer.Option(
        False,
        "--default-config",
        "-d",
        help="Do not load a config file. Use the defaults instead",
        show_default=False,
    ),
    extra_context: str = typer.Option(
        "{}",
        help="A JSON string describing any extra context to pass to cookiecutter.",
        show_default=False,
    ),
    no_input: bool = typer.Option(
        False,
        "--no-input",
        "-y",
        help="Do not prompt for parameters and only use cookiecutter.json file content",
        show_default=False,
    ),
    directory: Optional[str] = typer.Option(
        None,
        help=(
            "Directory within repo that holds"
            " cookiecutter.json file for advanced repositories"
            " with multi templates in it"
        ),
    ),
    checkout: Optional[str] = typer.Option(
        None,
        "--checkout",
        "-c",
        help=("The git reference to check against. Supports branches, tags and commit hashes."),
    ),
    overwrite_if_exists: bool = typer.Option(
        False,
        "--overwrite-if-exists",
        "-f",
        show_default=False,
        help="Overwrite the contents of the output directory if it already exists",
    ),
    skip: Optional[List[str]] = typer.Option(
        None, "--skip", show_default=False, help="Default files/pattern to skip on update"
    ),
) -> None:
    _commands.create(
        template_git_url,
        output_dir=output_dir,
        config_file=config_file,
        default_config=default_config,
        extra_context=json.loads(extra_context),
        no_input=no_input,
        directory=directory,
        checkout=checkout,
        overwrite_if_exists=overwrite_if_exists,
        skip=skip,
    )


@app.command(
    short_help="Link an existing project to a Cookiecutter template",
    help=_get_help_string(_commands.link),
)
def link(
    template_git_url: str = typer.Argument(
        ..., metavar="TEMPLATE", help="The Cookiecutter template URI."
    ),
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-p", help="Path to the project directory.", show_default=False
    ),
    checkout: Optional[str] = typer.Option(
        None,
        "--checkout",
        "-c",
        help=("The git reference to check against. Supports branches, tags and commit hashes."),
    ),
    no_input: bool = typer.Option(
        False,
        "--no-input",
        "-y",
        help="Do not prompt for parameters and only use cookiecutter.json file content",
        show_default=False,
    ),
    config_file: Optional[Path] = typer.Option(
        None, help="Path to the Cookiecutter user config file", exists=True
    ),
    default_config: bool = typer.Option(
        False,
        "--default-config",
        "-d",
        help="Do not load a config file. Use the defaults instead",
        show_default=False,
    ),
    extra_context: str = typer.Option(
        "{}",
        help="A JSON string describing any extra context to pass to cookiecutter.",
        show_default=False,
    ),
    directory: Optional[str] = typer.Option(
        None,
        help=(
            "Directory within repo that holds"
            " cookiecutter.json file for advanced repositories"
            " with multi templates in it"
        ),
    ),
) -> None:
    _commands.link(
        template_git_url,
        project_dir=project_dir,
        checkout=checkout,
        config_file=config_file,
        default_config=default_config,
        extra_context=json.loads(extra_context),
        no_input=no_input,
        directory=directory,
    )


@app.command(
    short_help="Update the project to the latest version of the linked Cookiecutter template",
    help=_get_help_string(_commands.update),
)
def update(
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-p", help="Path to the project directory.", show_default=False
    ),
    cookiecutter_input: bool = typer.Option(
        False,
        "--cookiecutter-input",
        "-i",
        help="Prompt for cookiecutter parameters for the latest template version",
        show_default=False,
    ),
    skip_apply_ask: bool = typer.Option(
        False,
        "--skip-apply-ask",
        "-y",
        help="Skip any prompts and directly apply updates",
        show_default=False,
    ),
    skip_update: bool = typer.Option(
        False,
        "--skip-update",
        "-s",
        help="Skip the template updates but update the cruft state",
        show_default=False,
    ),
    checkout: Optional[str] = typer.Option(
        None,
        "--checkout",
        "-c",
        help=("The git reference to check against. Supports branches, tags and commit hashes."),
    ),
    strict: bool = typer.Option(
        True,
        "--strict/--not-strict",
        help=(
            "If enabled, ensures that the project is updated to be"
            " the same as the checked out cookiecutter template. This means that"
            " if the cookiecutter template is an older commit, the current project changes will"
            " be rolled back to the previous version."
            " If disabled, the update is skipped if the checked out cookiecutter template"
            " commit is an ancestor of the project commit."
        ),
    ),
    allow_untracked_files: bool = typer.Option(
        False,
        "--allow-untracked-files",
        help=(
            "Allow the project's cruft to be updated if there are untracked files in the git"
            " repository (but no other changes)"
        ),
    ),
) -> None:
    if not _commands.update(
        project_dir=project_dir,
        cookiecutter_input=cookiecutter_input,
        skip_apply_ask=skip_apply_ask,
        skip_update=skip_update,
        checkout=checkout,
        strict=strict,
        allow_untracked_files=allow_untracked_files,
    ):
        raise typer.Exit(1)


@app.command(
    short_help="Show the diff between the project and the current cruft template.",
    help=_get_help_string(_commands.diff),
)
def diff(
    project_dir: Path = typer.Option(
        Path("."), "--project-dir", "-p", help="Path to the project directory.", show_default=False
    ),
    exit_code: bool = typer.Option(
        False, "--exit-code", "-e", help="Exit with status 1 on non-empty diff.", show_default=False
    ),
    checkout: Optional[str] = typer.Option(
        None,
        "--checkout",
        "-c",
        help=("The git reference to check against. Supports branches, tags and commit hashes."),
    ),
) -> None:
    if not _commands.diff(project_dir=project_dir, exit_code=exit_code, checkout=checkout):
        raise typer.Exit(1)
