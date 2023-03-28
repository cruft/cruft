import os
import stat
import sys
from pathlib import Path
from shutil import move, rmtree
from typing import Optional, Set, Union
from warnings import warn

from cookiecutter.generate import generate_files
from git import Repo

from .cookiecutter import CookiecutterContext, generate_cookiecutter_context
from .cruft import CruftState
from .iohelper import AltTemporaryDirectory

if not sys.version_info >= (3, 11):
    try:
        import toml as tomllib
    except ImportError:  # pragma: no cover
        tomllib = None  # type: ignore
else:
    import tomllib


def cookiecutter_template(
    output_dir: Path,
    repo: Repo,
    cruft_state: CruftState,
    project_dir: Path = Path("."),
    cookiecutter_input: bool = False,
    checkout: Optional[str] = None,
    deleted_paths: Optional[Set[Path]] = None,
    update_deleted_paths: bool = False,
) -> CookiecutterContext:
    """Generate a clean cookiecutter template in output_dir."""
    if deleted_paths is None:
        deleted_paths = set()
    pyproject_file = project_dir / "pyproject.toml"
    commit = checkout or repo.remotes.origin.refs["HEAD"]

    repo.head.reset(commit=commit, working_tree=True)

    assert repo.working_dir is not None  # nosec B101 (allow assert for type checking)
    context = _generate_output(cruft_state, Path(repo.working_dir), cookiecutter_input, output_dir)

    # Get all paths that we are supposed to skip before generating the diff and applying updates
    skip_paths = _get_skip_paths(cruft_state, pyproject_file)
    # We also get the list of paths that were deleted from the project
    # directory but were present in the template that the project is linked against
    # This is to avoid introducing changes that won't apply cleanly to the current project.
    if update_deleted_paths:
        deleted_paths.update(_get_deleted_files(output_dir, project_dir))
    # We now remove skipped and deleted paths from the project
    _remove_paths(output_dir, skip_paths | deleted_paths)  # type: ignore

    return context


#####################################
# Generating clean outputs for diff #
#####################################


def _generate_output(
    cruft_state: CruftState, project_dir: Path, cookiecutter_input: bool, output_dir: Path
) -> CookiecutterContext:
    inner_dir = project_dir / (cruft_state.get("directory") or "")

    # Don't pass entries prefixed by "_" = cookiecutter extensions, not direct user intent
    extra_context = {
        key: value
        for key, value in cruft_state["context"]["cookiecutter"].items()
        if not key.startswith("_")
    }
    new_context = generate_cookiecutter_context(
        cruft_state["template"],
        inner_dir,
        extra_context=extra_context,
        no_input=not cookiecutter_input,
    )

    # This generates the cookiecutter template.
    # Unfortunately, cookiecutter doesn't let us output the template in an
    # arbitrary directory. It insists on creating the initial project directory.
    # Therefore we have to move the directory content to the expected output_dir.
    # See https://github.com/cookiecutter/cookiecutter/pull/907
    output_dir.mkdir(parents=True, exist_ok=True)
    with AltTemporaryDirectory(cruft_state.get("directory")) as tmpdir:

        # Kindly ask cookiecutter to generate the template
        template_dir = generate_files(
            repo_dir=inner_dir, context=new_context, overwrite_if_exists=True, output_dir=tmpdir
        )
        template_dir = Path(template_dir)

        # Move the template content to the output directory
        for name in os.listdir(template_dir):
            move(str(template_dir / name), str(output_dir))

    return new_context


##############################
# Removing unnecessary files #
##############################


def _get_skip_paths(cruft_state: CruftState, pyproject_file: Path) -> Set[Path]:
    skip_cruft = cruft_state.get("skip", [])
    if tomllib and pyproject_file.is_file():
        pyproject_cruft = tomllib.loads(pyproject_file.read_text()).get("tool", {}).get("cruft", {})
        skip_cruft.extend(pyproject_cruft.get("skip", []))
    elif pyproject_file.is_file():
        warn(
            "pyproject.toml is present in repo, but python version is < 3.11 and "
            "`toml` package is not installed. Cruft configuration may be ignored."
        )
    return set(map(Path, skip_cruft))


def _get_deleted_files(template_dir: Path, project_dir: Path):
    cwd = Path.cwd()
    os.chdir(template_dir)
    template_paths = set(Path(".").glob("**/*"))
    os.chdir(cwd)
    os.chdir(project_dir)
    deleted_paths = set(filter(lambda path: not path.exists(), template_paths))
    os.chdir(cwd)
    return deleted_paths


def _remove_readonly(func, path, _):  # pragma: no cov_4_nix
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)  # WINDOWS
    func(path)


def _remove_single_path(path: Path):
    if path.is_dir():
        try:
            rmtree(path, ignore_errors=False, onerror=_remove_readonly)
        except Exception:  # pragma: no cover
            raise Exception("Failed to remove directory.")
        # rmtree(path)
    elif path.is_file():
        # path.unlink()
        try:
            path.unlink()
        except PermissionError:  # pragma: no cov_4_nix
            path.chmod(stat.S_IWRITE)
            path.unlink()
        except Exception as exc:  # pragma: no cover
            raise Exception("Failed to remove file.") from exc


def _remove_paths(root: Path, paths_to_remove: Set[Union[Path, str]]):
    # There is some redundancy here in chmoding dirs and/or files differently.
    abs_paths_to_remove = []
    for path_to_remove in paths_to_remove:
        if isinstance(path_to_remove, Path):
            abs_paths_to_remove.append(root / path_to_remove)
        elif isinstance(path_to_remove, str):  # assumes the string is a glob-pattern
            abs_paths_to_remove += list(root.glob(path_to_remove))
        else:
            warn(f"{path_to_remove} is not a Path object or a string glob-pattern")

    for path in abs_paths_to_remove:
        _remove_single_path(path)
