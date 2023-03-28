import json
import shutil
import sys
from pathlib import Path
from typing import Optional

import typer

from . import utils
from .utils.iohelper import AltTemporaryDirectory


def diff(
    project_dir: Path = Path("."), exit_code: bool = False, checkout: Optional[str] = None
) -> bool:
    """Show the diff between the project and the linked Cookiecutter template"""
    cruft_file = utils.cruft.get_cruft_file(project_dir)
    cruft_state = json.loads(cruft_file.read_text())
    checkout = checkout or cruft_state.get("commit")

    has_diff = False
    with AltTemporaryDirectory(cruft_state.get("directory")) as tmpdir_:
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

        # Then we create a new tree with each file in the template that also exist
        # locally.
        for path in sorted(remote_template_dir.glob("**/*")):
            relative_path = path.relative_to(remote_template_dir)
            local_path = project_dir / relative_path
            destination = local_template_dir / relative_path
            if path.is_file():
                shutil.copy(str(local_path), str(destination))
            else:
                destination.mkdir(parents=True, exist_ok=True)
                destination.chmod(local_path.stat().st_mode)

        # Finally we can compute and print the diff.
        diff = utils.diff.get_diff(local_template_dir, remote_template_dir)

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
                utils.diff.display_diff(local_template_dir, remote_template_dir)

    return not (has_diff and exit_code)
