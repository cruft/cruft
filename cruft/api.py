import json
import os
import stat
import sys
import time
from functools import partial
from pathlib import Path
from shutil import move, rmtree
from subprocess import PIPE, run  # nosec
from tempfile import TemporaryDirectory
from typing import Optional

from cookiecutter.config import get_user_config
from cookiecutter.generate import generate_context, generate_files
from cookiecutter.prompt import prompt_for_config
from examples import example
from git import Repo

from cruft.exceptions import (
    CruftAlreadyPresent,
    InvalidCookiecutterRepository,
    NoCruftFound,
    UnableToFindCookiecutterTemplate,
)

try:
    import toml  # type: ignore
except ImportError:  # pragma: no cover
    toml = None  # type: ignore

json_dumps = partial(json.dumps, ensure_ascii=False, indent=4, separators=(",", ": "))


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


@example("https://github.com/timothycrosley/cookiecutter-python/", no_input=True)
def create(
    template_git_url: str,
    output_dir: str = ".",
    config_file: Optional[str] = None,
    default_config: bool = False,
    extra_context: Optional[dict] = None,
    no_input: bool = False,
    directory: str = "",
    overwrite_if_exists: bool = False,
) -> str:
    """Expand a Git based Cookiecutter template into a new project on disk."""
    with RobustTemporaryDirectory() as cookiecutter_template_dir_str:
        cookiecutter_template_dir = Path(cookiecutter_template_dir_str)
        try:
            repo = Repo.clone_from(template_git_url, cookiecutter_template_dir)
            last_commit = repo.head.object.hexsha
        except Exception as e:
            raise InvalidCookiecutterRepository(e)

        main_cookiecutter_directory: Optional[Path] = None
        if directory:
            cookiecutter_template_dir = cookiecutter_template_dir / directory

        for dir_item in cookiecutter_template_dir.glob("*cookiecutter.*"):
            if dir_item.is_dir() and "{{" in dir_item.name and "}}" in dir_item.name:
                main_cookiecutter_directory = dir_item
                break

        if not main_cookiecutter_directory:  # pragma: no cover
            raise UnableToFindCookiecutterTemplate(cookiecutter_template_dir)

        context_file = cookiecutter_template_dir / "cookiecutter.json"

        config_dict = get_user_config(config_file=config_file, default_config=default_config)

        context = generate_context(
            context_file=str(context_file),
            default_context=config_dict["default_context"],
            extra_context=extra_context,
        )

        # prompt the user to manually configure at the command line.
        # except when 'no-input' flag is set
        context["cookiecutter"] = prompt_for_config(context, no_input)
        context["cookiecutter"]["_template"] = template_git_url

        (main_cookiecutter_directory / ".cruft.json").write_text(
            json_dumps(
                {
                    "template": template_git_url,
                    "commit": last_commit,
                    "context": context,
                    "directory": directory,
                }
            )
        )

        return generate_files(
            repo_dir=cookiecutter_template_dir,
            context=context,
            overwrite_if_exists=overwrite_if_exists,
            output_dir=output_dir,
        )


@example()
def check(expanded_dir: str = ".") -> bool:
    """Checks to see if there have been any updates to the Cookiecutter template used
    to generate this project.
    """
    expanded_dir_path = Path(expanded_dir)
    cruft_file = expanded_dir_path / ".cruft.json"
    if not cruft_file.is_file():
        raise NoCruftFound(expanded_dir_path.resolve())

    cruft_state = json.loads(cruft_file.read_text())
    with RobustTemporaryDirectory() as cookiecutter_template_dir:
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


@example()
@example(skip_apply_ask=True)
def update(
    expanded_dir: str = ".",
    cookiecutter_input: bool = False,
    skip_apply_ask: bool = False,
    skip_update: bool = False,
) -> bool:
    """Update specified project's cruft to the latest and greatest release."""
    expanded_dir_path = Path(expanded_dir)
    pyproject_file = expanded_dir_path / "pyproject.toml"
    cruft_file = expanded_dir_path / ".cruft.json"
    if not cruft_file.is_file():
        raise NoCruftFound(cruft_file)

    cruft_state = json.loads(cruft_file.read_text())

    skip_cruft = cruft_state.get("skip", [])
    if toml and pyproject_file.is_file():
        pyproject_cruft = toml.loads(pyproject_file.read_text()).get("tool", {}).get("cruft", {})
        skip_cruft.extend(pyproject_cruft.get("skip", []))

    with RobustTemporaryDirectory() as compare_directory_str:
        compare_directory = Path(compare_directory_str)
        template_dir = compare_directory / "template"

        try:
            repo = Repo.clone_from(cruft_state["template"], template_dir)
            last_commit = repo.head.object.hexsha
        except Exception as e:  # pragma: no cover
            raise InvalidCookiecutterRepository(e)

        if last_commit == cruft_state["commit"] or not repo.index.diff(cruft_state["commit"]):
            return False

        directory = cruft_state.get("directory", "")

        template_dir = template_dir / directory

        context_file = template_dir / "cookiecutter.json"

        new_output_dir = compare_directory / "new_output"

        new_context = _generate_output(
            context_file=str(context_file),
            cruft_state=cruft_state,
            cookiecutter_input=cookiecutter_input,
            template_dir=str(template_dir),
            output_dir=str(new_output_dir),
        )

        old_output_dir = compare_directory / "old_output"
        repo.head.reset(commit=cruft_state["commit"], working_tree=True)
        _generate_output(
            context_file=str(context_file),
            cruft_state=cruft_state,
            cookiecutter_input=cookiecutter_input,
            template_dir=str(template_dir),
            output_dir=str(old_output_dir),
        )

        for dir_item in old_output_dir.glob("*"):
            if dir_item.is_dir():
                old_main_directory = dir_item

        new_main_directory = new_output_dir / old_main_directory.name

        for skip_file in skip_cruft:
            file_path_old = old_main_directory / skip_file
            file_path_new = new_main_directory / skip_file
            for file_path in (file_path_old, file_path_new):
                if file_path.is_dir():
                    rmtree(file_path)
                elif file_path.is_file():
                    file_path.unlink()

        diff = run(
            ["git", "diff", "--no-index", str(old_main_directory), str(new_main_directory)],
            stdout=PIPE,
            stderr=PIPE,
        ).stdout.decode("utf8")
        diff = (
            diff.replace("\\\\", "\\")
            .replace(str(old_main_directory), "")
            .replace(str(new_main_directory), "")
        )

        print("The following diff would be applied:\n")
        print(diff)
        print("")

        if not skip_apply_ask and not skip_update:  # pragma: no cover
            update_str: str = ""
            while update_str not in ("y", "n", "s"):
                print(
                    'Respond with "s" to intentionally skip the update while marking '
                    "your project as up-to-date."
                )
                update_str = input("Apply diff and update [y/n/s]? ").lower()  # nosec

            if update_str == "n":
                sys.exit("User cancelled Cookiecutter template update.")
            elif update_str == "s":
                skip_update = True

        current_directory = Path.cwd()
        try:
            os.chdir(expanded_dir_path)
            if not skip_update:
                run(["patch", "-p1", "--merge"], input=diff.encode("utf8"))

            cruft_state["commit"] = last_commit
            cruft_state["context"] = new_context
            cruft_state["directory"] = directory
            cruft_file.write_text(json_dumps(cruft_state))
        finally:
            os.chdir(current_directory)

        return True


@example("https://github.com/timothycrosley/cookiecutter-python/", no_input=True, use_latest=True)
def link(
    template_git_url: str,
    project_dir: str = ".",
    use_latest: bool = False,
    no_input: bool = False,
    config_file: Optional[str] = None,
    default_config: bool = False,
    extra_context: Optional[dict] = None,
    directory: str = "",
) -> bool:
    """Links an existing project created from a template, to the template it was created from."""
    project_dir_path = Path(project_dir)
    cruft_file = project_dir_path / ".cruft.json"
    if cruft_file.is_file():
        raise CruftAlreadyPresent(cruft_file)

    with RobustTemporaryDirectory() as cookiecutter_template_dir_str:
        cookiecutter_template_dir = Path(cookiecutter_template_dir_str)
        try:
            repo = Repo.clone_from(template_git_url, cookiecutter_template_dir)
            last_commit = repo.head.object.hexsha
        except Exception as e:  # pragma: no cover
            raise InvalidCookiecutterRepository(e)

        main_cookiecutter_directory: Optional[Path] = None
        if directory:
            cookiecutter_template_dir = cookiecutter_template_dir / directory

        for dir_item in cookiecutter_template_dir.glob("*cookiecutter.*"):
            if dir_item.is_dir() and "{{" in dir_item.name and "}}" in dir_item.name:
                main_cookiecutter_directory = dir_item
                break

        if not main_cookiecutter_directory:  # pragma: no cover
            raise UnableToFindCookiecutterTemplate(cookiecutter_template_dir)

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

        if use_latest or no_input:
            use_commit = last_commit
        else:  # pragma: no cover
            print("")
            print(f"The latest commit to the template is {last_commit}")
            print("Press enter to link against this commit or provide an alternative commit.")
            print("")
            use_commit = input(f"Link to template at commit [{last_commit}]: ")  # nosec
            use_commit = use_commit if use_commit.strip() else last_commit

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
