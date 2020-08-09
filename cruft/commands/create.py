from pathlib import Path

from cookiecutter.generate import generate_files
from examples import example

from cruft.commands._utils import (
    RobustTemporaryDirectory,
    generate_cookiecutter_context,
    get_cookiecutter_repo,
    json_dumps,
)


@example("https://github.com/timothycrosley/cookiecutter-python/", no_input=True)
def create(
    template_git_url: str,
    output_dir: str = ".",
    config_file: str = None,
    default_config: bool = False,
    extra_context: dict = None,
    no_input: bool = False,
    directory: str = "",
    checkout: str = None,
    overwrite_if_exists: bool = False,
) -> str:
    """Expand a Git based Cookiecutter template into a new project on disk."""
    with RobustTemporaryDirectory() as cookiecutter_template_dir_str:
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

        project_dir = generate_files(
            repo_dir=cookiecutter_template_dir,
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            output_dir=output_dir,
        )

        # After generating the project - save the cruft state
        # into the cruft file.
        (Path(project_dir) / ".cruft.json").write_text(
            json_dumps(
                {
                    "template": template_git_url,
                    "commit": last_commit,
                    "context": context,
                    "directory": directory,
                }
            )
        )

        return project_dir
