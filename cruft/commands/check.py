import json
from pathlib import Path

from examples import example

from cruft.commands._utils import RobustTemporaryDirectory, get_cookiecutter_repo, get_cruft_file


@example()
def check(expanded_dir: str = ".", checkout: str = None) -> bool:
    """Checks to see if there have been any updates to the Cookiecutter template used
    to generate this project.
    """
    expanded_dir_path = Path(expanded_dir)
    cruft_file = get_cruft_file(expanded_dir_path)
    cruft_state = json.loads(cruft_file.read_text())
    with RobustTemporaryDirectory() as cookiecutter_template_dir:
        repo = get_cookiecutter_repo(cruft_state["template"], cookiecutter_template_dir, checkout)
        last_commit = repo.head.object.hexsha
        if last_commit == cruft_state["commit"] or not repo.index.diff(cruft_state["commit"]):
            return True

    return False
