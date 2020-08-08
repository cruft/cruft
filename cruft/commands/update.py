import json
import sys
from pathlib import Path
from shutil import rmtree
from subprocess import PIPE, CalledProcessError, run  # nosec
from typing import Any, Dict

from cookiecutter.generate import generate_files
from examples import example
from git import Repo

from cruft.commands._utils import (
    RobustTemporaryDirectory,
    generate_cookiecutter_context,
    get_cookiecutter_repo,
    get_cruft_file,
    json_dumps,
)

try:
    import toml  # type: ignore
except ImportError:  # pragma: no cover
    toml = None  # type: ignore

CruftState = Dict[str, Any]


@example()
@example(skip_apply_ask=True)
def update(
    expanded_dir: str = ".",
    cookiecutter_input: bool = False,
    skip_apply_ask: bool = False,
    skip_update: bool = False,
    checkout: str = None,
) -> bool:
    """Update specified project's cruft to the latest and greatest release."""
    expanded_dir_path = Path(expanded_dir)
    pyproject_file = expanded_dir_path / "pyproject.toml"
    cruft_file = get_cruft_file(expanded_dir_path)

    cruft_state = json.loads(cruft_file.read_text())

    with RobustTemporaryDirectory() as compare_directory_str:
        # Initial setup
        compare_directory = Path(compare_directory_str)
        template_dir = compare_directory / "template"
        repo = get_cookiecutter_repo(cruft_state["template"], template_dir, checkout)
        directory = cruft_state.get("directory", "")
        if directory:
            template_dir = template_dir / directory
        last_commit = repo.head.object.hexsha

        # Bail early if the repo is already up to date
        if last_commit == cruft_state["commit"] or not repo.index.diff(cruft_state["commit"]):
            return False

        # Generate clean outputs via the cookiecutter
        # from the current cruft state commit of the cookiectter and the updated
        # cookiecutter.
        old_main_directory, new_main_directory, new_context = _generate_project_updates(
            compare_directory, cruft_state, template_dir, cookiecutter_input, repo
        )

        # Remove any files from the generated versions that we are supposed
        # to skip before generating the diff and applying updates
        _remove_skip_files(cruft_state, pyproject_file, old_main_directory, new_main_directory)

        # Given the two versions of the cookiecutter outputs based
        # on the current project's context we calculate the diff and
        # apply the updates to the current project.
        _apply_project_updates(
            old_main_directory, new_main_directory, expanded_dir_path, skip_update, skip_apply_ask
        )

        # Update the cruft state and dump the new state
        # to the cruft file
        cruft_state["commit"] = last_commit
        cruft_state["context"] = new_context
        cruft_state["directory"] = directory
        cruft_file.write_text(json_dumps(cruft_state))

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
    _, old_main_directory = _generate_output(
        cruft_state, template_dir, cookiecutter_input, old_output_dir
    )
    return old_main_directory, new_main_directory, new_context


##############################
# Removing unnecessary files #
##############################


def _remove_skip_files(
    cruft_state: CruftState,
    pyproject_file: Path,
    old_main_directory: Path,
    new_main_directory: Path,
):
    skip_cruft = cruft_state.get("skip", [])
    if toml and pyproject_file.is_file():
        pyproject_cruft = toml.loads(pyproject_file.read_text()).get("tool", {}).get("cruft", {})
        skip_cruft.extend(pyproject_cruft.get("skip", []))

    for skip_file in skip_cruft:
        file_path_old = old_main_directory / skip_file
        file_path_new = new_main_directory / skip_file
        for file_path in (file_path_old, file_path_new):
            if file_path.is_dir():
                rmtree(file_path)
            elif file_path.is_file():
                file_path.unlink()


#################################################
# Calculating project diff and applying updates #
#################################################


def _get_diff(old_main_directory: Path, new_main_directory: Path):
    diff = run(
        ["git", "diff", "--no-index", str(old_main_directory), str(new_main_directory)],
        stdout=PIPE,
        stderr=PIPE,
    ).stdout.decode("utf8")
    diff = (
        diff.replace("\\\\", "\\")
        .replace(str(old_main_directory), "")
        .replace(str(new_main_directory), "")
    )

    print("The following diff would be applied:\n")
    print(diff)
    print("")
    return diff


def _apply_patch(diff: str, expanded_dir_path: Path):
    try:
        run(
            ["patch", "-p1", "--merge"],
            input=diff.encode("utf8"),
            stderr=PIPE,
            check=True,
            cwd=expanded_dir_path,
        )
    except CalledProcessError as error:
        if b"unrecognized option `--merge'" in error.stderr:
            print(
                "Running patch with --no-backup-if-mismatch, this could silently fail"
                " to apply changes, verify changes with above diff."
            )
            run(
                ["patch", "-p1", "--no-backup-if-mismatch"],
                input=diff.encode("utf8"),
                cwd=expanded_dir_path,
            )
        else:
            print(error.stderr, file=sys.stderr)


def _apply_project_updates(
    old_main_directory: Path,
    new_main_directory: Path,
    project_dir: Path,
    skip_update: bool,
    skip_apply_ask: bool,
):

    diff = _get_diff(old_main_directory, new_main_directory)

    if not skip_apply_ask and not skip_update:  # pragma: no cover
        update_str: str = ""
        while update_str not in ("y", "n", "s"):
            print(
                'Respond with "s" to intentionally skip the update while marking '
                "your project as up-to-date."
            )
            update_str = input("Apply diff and update [y/n/s]? ").lower()  # nosec

        if update_str == "n":
            sys.exit("User cancelled Cookiecutter template update.")
        elif update_str == "s":
            skip_update = True

    if not skip_update:
        _apply_patch(diff, project_dir)
