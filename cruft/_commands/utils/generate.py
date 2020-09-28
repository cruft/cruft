import os
from pathlib import Path
from shutil import move, rmtree
from tempfile import TemporaryDirectory
from typing import Optional, Set

from cookiecutter.generate import generate_files
from git import Repo

from .cookiecutter import CookiecutterContext, generate_cookiecutter_context
from .cruft import CruftState

try:
    import toml  # type: ignore
except ImportError:  # pragma: no cover
    toml = None  # type: ignore


def cookiecutter_template(
    output_dir: Path,
    repo: Repo,
    cruft_state: CruftState,
    project_dir: Path = Path("."),
    cookiecutter_input: bool = False,
    checkout: Optional[str] = None,
) -> CookiecutterContext:
    """Generate a clean cookiecutter template in output_dir."""
    pyproject_file = project_dir / "pyproject.toml"
    commit = checkout or repo.remotes.origin.refs["HEAD"]

    repo.head.reset(commit=commit, working_tree=True)

    context = _generate_output(cruft_state, Path(repo.working_dir), cookiecutter_input, output_dir)

    # Get all paths that we are supposed to skip before generating the diff and applying updates
    skip_paths = _get_skip_paths(cruft_state, pyproject_file)
    # We also get the list of paths that were deleted from the project
    # directory but were present in the template that the project is linked against
    # This is to avoid introducing changes that won't apply cleanly to the current project.
    deleted_paths = _get_deleted_files(output_dir, project_dir)
    # We now remove skipped and deleted paths from the project
    _remove_paths(output_dir, skip_paths | deleted_paths)

    return context


#####################################
# Generating clean outputs for diff #
#####################################


def _generate_output(
    cruft_state: CruftState, project_dir: Path, cookiecutter_input: bool, output_dir: Path
) -> CookiecutterContext:
    inner_dir = project_dir / (cruft_state.get("directory") or "")

    new_context = generate_cookiecutter_context(
        cruft_state["template"],
        inner_dir,
        extra_context=cruft_state["context"]["cookiecutter"],
        no_input=not cookiecutter_input,
    )

    # This generates the cookiecutter template.
    # Unfortunately, cookiecutter doesn't let us output the template in an
    # arbitrary directory. It insists on creating the initial project directory.
    # Therefore we have to move the directory content to the expected output_dir.
    # See https://github.com/cookiecutter/cookiecutter/pull/907
    output_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as tmpdir_:
        tmpdir = Path(tmpdir_)

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
    if toml and pyproject_file.is_file():
        pyproject_cruft = toml.loads(pyproject_file.read_text()).get("tool", {}).get("cruft", {})
        skip_cruft.extend(pyproject_cruft.get("skip", []))
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


def _remove_paths(root: Path, paths_to_remove: Set[Path]):
    for path_to_remove in paths_to_remove:
        path = root / path_to_remove
        if path.is_dir():
            rmtree(path)
        elif path.is_file():
            path.unlink()
