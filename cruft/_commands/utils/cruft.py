import json
from pathlib import Path
from typing import Any, Dict

from git import Repo

from cruft.exceptions import CruftAlreadyPresent, NoCruftFound

CruftState = Dict[str, Any]


#######################
# Cruft related utils #
#######################


def get_cruft_file(project_dir_path: Path, exists: bool = True) -> Path:
    cruft_file = project_dir_path / ".cruft.json"
    if not exists and cruft_file.is_file():
        raise CruftAlreadyPresent(cruft_file)
    if exists and not cruft_file.is_file():
        raise NoCruftFound(project_dir_path.resolve())
    return cruft_file


def is_project_updated(repo: Repo, current_commit: str, latest_commit: str, strict: bool) -> bool:
    return (
        # If the latest commit exactly matches the current commit
        latest_commit == current_commit
        # Or if there have been no changes to the cookiecutter
        or not repo.index.diff(current_commit)
        # or if the strict flag is off, we allow for newer commits to count as up to date
        or (
            repo.is_ancestor(repo.commit(latest_commit), repo.commit(current_commit)) and not strict
        )
    )


def json_dumps(cruft_state: Dict[str, Any]) -> str:
    text = json.dumps(cruft_state, ensure_ascii=False, indent=2, separators=(",", ": "))
    return text + "\n"
