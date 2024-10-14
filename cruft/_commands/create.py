from pathlib import Path
from typing import Any, Dict, List, Optional

from cookiecutter.generate import generate_files
from cookiecutter.prompt import choose_nested_template

from . import utils
from .utils import example
from .utils.iohelper import AltTemporaryDirectory
from .utils.nested import get_relative_path, is_nested_template
from .utils.validate import validate_cookiecutter


@example("https://github.com/timothycrosley/cookiecutter-python/")
def create(
    template_git_url: str,
    output_dir: Path = Path("."),
    config_file: Optional[Path] = None,
    default_config: bool = False,
    extra_context: Optional[Dict[str, Any]] = None,
    extra_context_file: Optional[Path] = None,
    no_input: bool = True,
    directory: Optional[str] = None,
    checkout: Optional[str] = None,
    overwrite_if_exists: bool = False,
    skip: Optional[List[str]] = None,
) -> Path:
    """Expand a Git based Cookiecutter template into a new project on disk."""
    template_git_url = utils.cookiecutter.resolve_template_url(template_git_url)
    with AltTemporaryDirectory(directory) as cookiecutter_template_dir_str:
        cookiecutter_template_dir = Path(cookiecutter_template_dir_str)
        with utils.cookiecutter.get_cookiecutter_repo(
            template_git_url, cookiecutter_template_dir, checkout
        ) as repo:
            last_commit = repo.head.object.hexsha

            if directory:
                cookiecutter_template_dir = cookiecutter_template_dir / directory

            if extra_context_file:
                extra_context = utils.cookiecutter.get_extra_context_from_file(extra_context_file)
            context = utils.cookiecutter.generate_cookiecutter_context(
                template_git_url,
                cookiecutter_template_dir,
                config_file,
                default_config,
                extra_context,
                no_input,
            )

        if is_nested_template(context):
            nested_template = choose_nested_template(
                context, cookiecutter_template_dir_str, no_input
            )
            return create(
                template_git_url=template_git_url,
                output_dir=output_dir,
                config_file=config_file,
                default_config=default_config,
                extra_context=extra_context,
                extra_context_file=extra_context_file,
                no_input=no_input,
                directory=get_relative_path(nested_template, cookiecutter_template_dir_str),
                checkout=checkout,
                skip=skip,
            )

        validate_cookiecutter(cookiecutter_template_dir)

        project_dir = Path(
            generate_files(
                repo_dir=cookiecutter_template_dir,
                context=context,
                overwrite_if_exists=overwrite_if_exists,
                output_dir=str(output_dir),
            )
        )

        cruft_content = {
            "template": template_git_url,
            "commit": last_commit,
            "checkout": checkout,
            "context": context,
            "directory": directory,
        }

        if skip:
            cruft_content["skip"] = skip

        # After generating the project - save the cruft state
        # into the cruft file.
        (project_dir / ".cruft.json").write_text(utils.cruft.json_dumps(cruft_content))

        return project_dir
