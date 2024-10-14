from pathlib import Path
from typing import Optional

from cruft.exceptions import UnableToFindCookiecutterTemplate


def validate_cookiecutter(cookiecutter_template_dir: Path):
    main_cookiecutter_directory: Optional[Path] = None

    for dir_item in cookiecutter_template_dir.glob("*cookiecutter.*"):
        if dir_item.is_dir() and "{{" in dir_item.name and "}}" in dir_item.name:
            main_cookiecutter_directory = dir_item
            break

    if not main_cookiecutter_directory:
        raise UnableToFindCookiecutterTemplate(cookiecutter_template_dir)
