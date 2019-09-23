import json
import os
import sys
from functools import partial
from pathlib import Path
from shutil import move
from subprocess import run  # nosec
from tempfile import TemporaryDirectory
from typing import Optional

from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_context, generate_files
from cookiecutter.prompt import prompt_for_config
from examples import example
from git import Repo

from cruft.exceptions import NoCruftFound, UnableToFindCookiecutterTemplate

json_dump = partial(json.dump, ensure_ascii=False, indent=4, separators=(",", ": "))


@example("https://github.com/timothycrosley/cookiecutter-python/", no_input=True)
def create(
    template_git_url: str,
    output_dir: str = ".",
    config_file: Optional[str] = None,
    default_config: bool = False,
    extra_context: Optional[dict] = None,
    no_input: bool = False,
    overwrite_if_exists: bool = False,
) -> str:
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
            json_dump(
                {"template": template_git_url, "commit": last_commit, "context": context},
                cruft_file,
            )

        return generate_files(
            repo_dir=cookiecutter_template_dir,
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            output_dir=output_dir,
        )


def check(expanded_dir: str = ".") -> bool:
    """Checks to see if there have been any updates to the Cookiecutter template used
    to generate this project.
    """
    cruft_file = os.path.join(expanded_dir, ".cruft.json")
    if not os.path.isfile(cruft_file):
        raise NoCruftFound(os.path.abspath(expanded_dir))

    with open(cruft_file) as cruft_open_file:
        cruft_state = json.load(cruft_open_file)
        with TemporaryDirectory() as cookiecutter_template_dir:
            repo = Repo.clone_from(cruft_state["template"], cookiecutter_template_dir)
            last_commit = repo.head.object.hexsha
            if last_commit == cruft_state["commit"] or not repo.index.diff(cruft_state["commit"]):
                return True

    return False


def _generate_output(
    context_file: str,
    cruft_state: dict,
    cookiecutter_input: bool,
    template_dir: str,
    output_dir: str,
) -> dict:
    context = generate_context(
        context_file=context_file, extra_context=cruft_state["context"]["cookiecutter"]
    )
    context["cookiecutter"] = prompt_for_config(context, not cookiecutter_input)
    context["cookiecutter"]["_template"] = cruft_state["template"]

    generate_files(
        repo_dir=template_dir, context=context, overwrite_if_exists=True, output_dir=output_dir
    )
    return context


def update(
    expanded_dir: str = ".", cookiecutter_input: bool = False, skip_apply_ask: bool = False
) -> bool:
    """Update specified project's cruft to the latest and greatest release."""
    cruft_file = os.path.join(expanded_dir, ".cruft.json")
    if not os.path.isfile(cruft_file):
        raise NoCruftFound(os.path.abspath(expanded_dir))

    with open(cruft_file) as cruft_open_file:
        cruft_state = json.load(cruft_open_file)
        with TemporaryDirectory() as compare_directory:
            template_dir = os.path.join(compare_directory, "template")

            repo = Repo.clone_from(cruft_state["template"], template_dir)
            last_commit = repo.head.object.hexsha
            if last_commit == cruft_state["commit"] or not repo.index.diff(cruft_state["commit"]):
                return False

            context_file = os.path.join(template_dir, "cookiecutter.json")

            new_output_dir = os.path.join(compare_directory, "new_output")

            new_context = _generate_output(
                context_file=context_file,
                cruft_state=cruft_state,
                cookiecutter_input=cookiecutter_input,
                template_dir=template_dir,
                output_dir=new_output_dir,
            )

            old_output_dir = os.path.join(compare_directory, "old_output")
            repo.head.reset(commit=cruft_state["commit"], working_tree=True)
            _generate_output(
                context_file=context_file,
                cruft_state=cruft_state,
                cookiecutter_input=cookiecutter_input,
                template_dir=template_dir,
                output_dir=old_output_dir,
            )

            main_directory: str = ""
            for file_name in os.listdir(old_output_dir):
                file_path = os.path.join(old_output_dir, file_name)
                if os.path.isdir(file_path):
                    main_directory = file_name

            new_main_directory = os.path.join(new_output_dir, main_directory)
            old_main_directory = os.path.join(old_output_dir, main_directory)

            diff = run(
                ["git", "diff", old_main_directory, new_main_directory], capture_output=True
            ).stdout.decode("utf8")
            diff = diff.replace(old_main_directory, "").replace(new_main_directory, "")

            print("The following diff would be applied:\n")
            print(diff)
            print("")

            if not skip_apply_ask:
                update = ""
                while update.lower() not in ("y", "n"):
                    update = input("Apply diff and update [y/n]? ")  # nosec

                if update.lower() == "n":
                    sys.exit("User cancelled Cookiecutter template update.")

            current_directory = os.getcwd()
            try:
                os.chdir(expanded_dir)
                run(["git", "apply"], input=diff.encode("utf8"))

                cruft_state["commit"] = last_commit
                cruft_state["context"] = new_context
                with open(cruft_file, "w") as cruft_output:
                    json_dump(cruft_state, cruft_output)
            finally:
                os.chdir(current_directory)

            return True
