from pathlib import Path
from typing import Any, Dict, Optional

import typer

from . import utils
from .utils import example
from .utils.iohelper import AltTemporaryDirectory


@example("https://github.com/timothycrosley/cookiecutter-python/")
def link(
    template_git_url: str,
    project_dir: Path = Path("."),
    checkout: Optional[str] = None,
    no_input: bool = True,
    config_file: Optional[Path] = None,
    default_config: bool = False,
    extra_context: Optional[Dict[str, Any]] = None,
    directory: Optional[str] = None,
) -> bool:
    """Links an existing project created from a template, to the template it was created from."""
    cruft_file = utils.cruft.get_cruft_file(project_dir, exists=False)
    template_git_url = utils.cookiecutter.resolve_template_url(template_git_url)
    with AltTemporaryDirectory(directory) as cookiecutter_template_dir_str:
        cookiecutter_template_dir = Path(cookiecutter_template_dir_str)
        with utils.cookiecutter.get_cookiecutter_repo(
            template_git_url, cookiecutter_template_dir, checkout
        ) as repo:
            last_commit = repo.head.object.hexsha

        if directory:
            cookiecutter_template_dir = cookiecutter_template_dir / directory

        context = utils.cookiecutter.generate_cookiecutter_context(
            template_git_url,
            cookiecutter_template_dir,
            config_file,
            default_config,
            extra_context,
            no_input,
        )
        if no_input:
            use_commit = last_commit
        else:
            typer.echo(
                f"Linking against the commit: {last_commit}"
                f" which corresponds with the git reference: {checkout}"
            )
            typer.echo("Press enter to link against this commit or provide an alternative commit.")
            use_commit = typer.prompt("Link to template at commit", default=last_commit)

        cruft_file.write_text(
            utils.cruft.json_dumps(
                {
                    "template": template_git_url,
                    "commit": use_commit,
                    "checkout": checkout,
                    "context": context,
                    "directory": directory,
                }
            )
        )
        return True
