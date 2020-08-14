import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import typer

from .utils import example, get_cookiecutter_repo, get_cruft_file, is_project_updated


@example()
def check(
    project_dir: Path = Path("."), checkout: Optional[str] = None, strict: bool = True
) -> bool:
    """Checks to see if there have been any updates to the Cookiecutter template
    used to generate this project."""
    cruft_file = get_cruft_file(project_dir)
    cruft_state = json.loads(cruft_file.read_text())
    with TemporaryDirectory() as cookiecutter_template_dir:
        repo = get_cookiecutter_repo(
            cruft_state["template"], Path(cookiecutter_template_dir), checkout
        )
        last_commit = repo.head.object.hexsha
        if is_project_updated(repo, cruft_state["commit"], last_commit, strict):
            typer.secho(
                "SUCCESS: Good work! Project's cruft is up to date and as clean as possible :).",
                fg=typer.colors.GREEN,
            )
            return True

        typer.secho(
            "FAILURE: Project's cruft is out of date! Run `cruft update` to clean this mess up.",
            fg=typer.colors.RED,
        )
        return False
