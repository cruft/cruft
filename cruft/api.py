import json
import os
from tempfile import TemporaryDirectory
from typing import Optional

from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_context, generate_files
from cookiecutter.prompt import prompt_for_config
from git import Repo

from cruft.exceptions import UnableToFindCookiecutterTemplate


def create(
    template_git_url: str,
    output_dir: str = ".",
    config_file: Optional[str] = None,
    default_config: bool = False,
    extra_context: Optional[dict] = None,
    no_input: bool = False,
    overwrite_if_exists: bool = False,
):
    """Expand a Git based Cookiecutter template into a new project on disk."""
    with TemporaryDirectory() as cookiecutter_template_dir:
        repo = Repo.clone_from(template_git_url, cookiecutter_template_dir)
        last_commit = repo.head.object.hexsha

        main_cookiecutter_directory: str = ""
        for file_name in os.listdir(cookiecutter_template_dir):
            file_path = os.path.join(cookiecutter_template_dir, file_name)
            if (
                os.path.isdir(file_path)
                and "{{" in file_name
                and "}}" in file_name
                and "cookiecutter." in file_name
            ):
                main_cookiecutter_directory = file_path
                break

        if not main_cookiecutter_directory:
            raise UnableToFindCookiecutterTemplate(cookiecutter_template_dir)

        context_file = os.path.join(cookiecutter_template_dir, "cookiecutter.json")

        config_dict = get_user_config(config_file=config_file, default_config=default_config)

        context = generate_context(
            context_file=context_file,
            default_context=config_dict["default_context"],
            extra_context=extra_context,
        )

        # prompt the user to manually configure at the command line.
        # except when 'no-input' flag is set
        context["cookiecutter"] = prompt_for_config(context, no_input)
        context["cookiecutter"]["_template"] = template_git_url

        with open(os.path.join(main_cookiecutter_directory, ".cruft.json"), "w") as cruft_file:
            json.dump(
                {"template": "template_git_url", "commit": last_commit, "context": context},
                cruft_file,
                ensure_ascii=False,
            )

        result = generate_files(
            repo_dir=cookiecutter_template_dir,
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            output_dir=output_dir,
        )
