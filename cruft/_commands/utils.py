import json
from functools import partial, wraps
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

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

try:
    from examples import example
except ImportError:  # pragma: no cover
    # In case examples is not available,
    # we introduce a no-op decorator.
    def example(*_args, **_kwargs):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)

            return wrapper

        return decorator


#################################
# Cookiecutter helper functions #
#################################


def resolve_template_url(url: str) -> str:
    parsed_url = urlparse(url)
    # If we are given a file URI, we should convert
    # relative paths to absolute paths. This is to
    # make sure that further operations like check/update
    # work properly in case the generated project directory
    # does not reside in the same relative path.
    if not parsed_url.scheme or parsed_url.scheme == "file":
        return str((Path(parsed_url.netloc) / Path(parsed_url.path)).absolute())
    return url


def get_cookiecutter_repo(
    template_git_url: str, cookiecutter_template_dir: Path, checkout: Optional[str] = None
):
    try:
        repo = Repo.clone_from(template_git_url, cookiecutter_template_dir)
        if checkout is not None:
            repo.git.checkout(checkout)
    except Exception:
        raise InvalidCookiecutterRepository(template_git_url)
    else:
        return repo


def _validate_cookiecutter(cookiecutter_template_dir: Path):
    main_cookiecutter_directory: Optional[Path] = None

    for dir_item in cookiecutter_template_dir.glob("*cookiecutter.*"):
        if dir_item.is_dir() and "{{" in dir_item.name and "}}" in dir_item.name:
            main_cookiecutter_directory = dir_item
            break

    if not main_cookiecutter_directory:
        raise UnableToFindCookiecutterTemplate(cookiecutter_template_dir)


def generate_cookiecutter_context(
    template_git_url: str,
    cookiecutter_template_dir: Path,
    config_file: Optional[Path] = None,
    default_config: bool = False,
    extra_context: Optional[Dict[str, Any]] = None,
    no_input: bool = False,
):
    _validate_cookiecutter(cookiecutter_template_dir)

    context_file = cookiecutter_template_dir / "cookiecutter.json"
    config_dict = get_user_config(
        config_file=str(config_file) if config_file else None, default_config=default_config
    )

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


def is_project_updated(repo: Repo, current_commit: str, latest_commit: str, strict: bool):
    return (
        # If the latest commit exactly matches the current commit
        latest_commit == current_commit
        # Or if there have been no changes to the cookiecutter
        or not repo.index.diff(current_commit)
        # or if the strict flag is off, we allow for newer commits to count as up to date
        or (repo.is_ancestor(latest_commit, current_commit) and not strict)
    )


json_dumps = partial(json.dumps, ensure_ascii=False, indent=4, separators=(",", ": "))
