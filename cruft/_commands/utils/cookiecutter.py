import json
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_context
from cookiecutter.prompt import prompt_for_config
from git import GitCommandError, Repo

from cruft.exceptions import InvalidCookiecutterRepository

from .nested import is_nested_template

CookiecutterContext = Dict[str, Any]


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
        file_path = (Path(parsed_url.netloc) / Path(parsed_url.path)).absolute()
        # Below is to handle cases like "git@github.com"
        # which passes through to this block, but will obviously not
        # exist in the file system.
        # In this case we simply return the URL. If the user did
        # pass in a valid file path that does not exist, we do not need to
        # worry as we will never to be able use it in check/update etc. anyway
        if file_path.exists():
            return str(file_path)
    return url


def get_cookiecutter_repo(
    template_git_url: str,
    cookiecutter_template_dir: Path,
    checkout: Optional[str] = None,
    **clone_kwargs,
) -> Repo:
    try:
        repo = Repo.clone_from(template_git_url, cookiecutter_template_dir, **clone_kwargs)
    except GitCommandError as error:
        raise InvalidCookiecutterRepository(
            template_git_url, f"Failed to clone the repo. {error.stderr.strip()}"
        )
    if checkout is not None:
        try:
            repo.git.checkout(checkout)
        except GitCommandError as error:
            raise InvalidCookiecutterRepository(
                template_git_url,
                f"Failed to check out the reference {checkout}. {error.stderr.strip()}",
            )
    return repo


def generate_cookiecutter_context(
    template_git_url: str,
    cookiecutter_template_dir: Path,
    config_file: Optional[Path] = None,
    default_config: bool = False,
    extra_context: Optional[Dict[str, Any]] = None,
    no_input: bool = False,
) -> CookiecutterContext:

    context_file = cookiecutter_template_dir / "cookiecutter.json"
    config_dict = get_user_config(
        config_file=str(config_file) if config_file else None, default_config=default_config
    )

    context = generate_context(
        context_file=context_file,
        default_context=config_dict["default_context"],
        extra_context=extra_context,
    )

    if is_nested_template(context):
        return context

    # prompt the user to manually configure at the command line.
    # except when 'no-input' flag is set
    context["cookiecutter"] = prompt_for_config(context, no_input)
    context["cookiecutter"]["_template"] = template_git_url

    return context


def get_extra_context_from_file(extra_context_file: Path) -> Dict[str, Any]:
    extra_context = {}
    if extra_context_file.exists():
        with open(extra_context_file, "r") as f:
            extra_context = json.load(f)
    return extra_context
