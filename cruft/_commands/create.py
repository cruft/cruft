from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional

from cookiecutter.generate import generate_files

from . import utils
from .utils import example


@example("https://github.com/timothycrosley/cookiecutter-python/")
def create(
    template_git_url: str,
    output_dir: Path = Path("."),
    config_file: Optional[Path] = None,
    default_config: bool = False,
    extra_context: Optional[Dict[str, Any]] = None,
    no_input: bool = True,
    directory: Optional[str] = None,
    checkout: Optional[str] = None,
    overwrite_if_exists: bool = False,
) -> Path:
    """Expand a Git based Cookiecutter template into a new project on disk."""
    template_git_url = utils.cookiecutter.resolve_template_url(template_git_url)
    with TemporaryDirectory() as cookiecutter_template_dir_str:
        cookiecutter_template_dir = Path(cookiecutter_template_dir_str)
        repo = utils.cookiecutter.get_cookiecutter_repo(
            template_git_url, cookiecutter_template_dir, checkout
        )
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

        project_dir = Path(
            generate_files(
                repo_dir=cookiecutter_template_dir,
                context=context,
                overwrite_if_exists=overwrite_if_exists,
                output_dir=str(output_dir),
            )
        )

        # After generating the project - save the cruft state
        # into the cruft file.
        (project_dir / ".cruft.json").write_text(
            utils.cruft.json_dumps(
                {
                    "template": template_git_url,
                    "commit": last_commit,
                    "context": context,
                    "directory": directory,
                }
            )
        )

        return project_dir
