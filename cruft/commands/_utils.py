import json
import os
import stat
import time
from functools import partial
from pathlib import Path
from shutil import rmtree
from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional

from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_context
from cookiecutter.prompt import prompt_for_config
from git import Repo

from cruft.exceptions import (
    CruftAlreadyPresent,
    InvalidCookiecutterRepository,
    NoCruftFound,
    UnableToFindCookiecutterTemplate,
)

#################################
# Cookiecutter helper functions #
#################################


def get_cookiecutter_repo(
    template_git_url: str, cookiecutter_template_dir: Path, checkout: Optional[str] = None
):
    try:
        repo = Repo.clone_from(template_git_url, cookiecutter_template_dir)
        if checkout is not None:
            repo.git.checkout(checkout)
    except Exception as e:  # pragma: no cover
        raise InvalidCookiecutterRepository(e)
    else:
        return repo


def _validate_cookiecutter(cookiecutter_template_dir: Path):
    main_cookiecutter_directory: Optional[Path] = None

    for dir_item in cookiecutter_template_dir.glob("*cookiecutter.*"):
        if dir_item.is_dir() and "{{" in dir_item.name and "}}" in dir_item.name:
            main_cookiecutter_directory = dir_item
            break

    if not main_cookiecutter_directory:  # pragma: no cover
        raise UnableToFindCookiecutterTemplate(cookiecutter_template_dir)


def generate_cookiecutter_context(
    template_git_url: str,
    cookiecutter_template_dir: Path,
    config_file: str = None,
    default_config: bool = False,
    extra_context: Dict[str, Any] = None,
    no_input: bool = False,
):
    _validate_cookiecutter(cookiecutter_template_dir)

    context_file = cookiecutter_template_dir / "cookiecutter.json"

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

    return context


#######################
# Cruft related utils #
#######################


def get_cruft_file(project_dir_path: Path, exists: bool = True):
    cruft_file = project_dir_path / ".cruft.json"
    if not exists and cruft_file.is_file():
        raise CruftAlreadyPresent(cruft_file)
    if exists and not cruft_file.is_file():
        raise NoCruftFound(project_dir_path.resolve())
    return cruft_file


class RobustTemporaryDirectory(TemporaryDirectory):
    """Retries deletion on __exit__
    This is caused by Windows behavior that you cannot delete a directory
    if it contains any read-only files.
    cf. https://bugs.python.org/issue19643
    """

    DELETE_MAX_RETRY_COUNT = 10
    DELETE_RETRY_TIME = 0.1

    def cleanup(self):
        if self._finalizer.detach():

            def readonly_handler(rm_func, path, exc_info):
                if issubclass(exc_info[0], PermissionError):
                    os.chmod(path, stat.S_IWRITE)
                    return rm_func(path)

            err_count = 0
            while True:
                try:
                    rmtree(self.name, onerror=readonly_handler)
                    break
                except (OSError, WindowsError):
                    err_count += 1
                    if err_count > self.DELETE_MAX_RETRY_COUNT:
                        # This serves as a workaround to be able to use this tool under Windows.
                        # Deleting temporary folders fails because Python cannot delete them.
                        if os.name != "nt":
                            raise
                        else:
                            break
                    time.sleep(self.DELETE_RETRY_TIME)


json_dumps = partial(json.dumps, ensure_ascii=False, indent=4, separators=(",", ": "))
