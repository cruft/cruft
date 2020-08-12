from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional

import typer

from .utils import (
    example,
    generate_cookiecutter_context,
    get_cookiecutter_repo,
    get_cruft_file,
    json_dumps,
    resolve_template_url,
)


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
    cruft_file = get_cruft_file(project_dir, exists=False)
    template_git_url = resolve_template_url(template_git_url)
    with TemporaryDirectory() as cookiecutter_template_dir_str:
        cookiecutter_template_dir = Path(cookiecutter_template_dir_str)
        repo = get_cookiecutter_repo(template_git_url, cookiecutter_template_dir, checkout)
        last_commit = repo.head.object.hexsha

        if directory:
            cookiecutter_template_dir = cookiecutter_template_dir / directory

        context = generate_cookiecutter_context(
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
            json_dumps(
                {
                    "template": template_git_url,
                    "commit": use_commit,
                    "context": context,
                    "directory": directory,
                }
            )
        )
        return True
