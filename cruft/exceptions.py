"""Contains all custom exceptions raised by cruft."""
from pathlib import Path
from typing import Union

from click import ClickException


class CruftError(ClickException):
    """The base exception for any error originating from the cruft project."""


class UnableToFindCookiecutterTemplate(CruftError):
    """Raised when Cruft is unable to find a cookiecutter template."""

    def __init__(self, directory: Union[str, Path]):
        if not isinstance(directory, str):
            directory = str(directory)
        super().__init__(f"Was unable to locate a Cookiecutter template in `{directory}` !")
        self.directory = directory


class NoCruftFound(CruftError):
    """Raised when no .cruft.json state is found in the current directory."""

    def __init__(self, directory: Union[str, Path]):
        if not isinstance(directory, str):
            directory = str(directory)
        super().__init__(f"Was unable to locate a `.cruft.json` state file in `{directory}` !")
        self.directory = directory


class CruftAlreadyPresent(CruftError):
    """Raised when there is an attempt to create a new .cruft.json file but one already exists."""

    def __init__(self, file_location: Union[str, Path]):
        if not isinstance(file_location, str):
            file_location = str(file_location)
        super().__init__(f"`.cruft.json` is already defined at `{file_location}` !")
        self.file_location = file_location


class InvalidCookiecutterRepository(CruftError):
    """Raised when an invalid cookiecutter repository is provided."""

    def __init__(self, cookiecutter_repo: str, details: str = ""):
        self.cookiecutter_repo = cookiecutter_repo
        super().__init__(
            f"Unable to initialize the cookiecutter using {cookiecutter_repo}! {details.strip()}"
        )


class ChangesetUnicodeError(CruftError):
    """Raised when `cruft update` is unable to generate the change"""

    def __init__(self):
        super().__init__(
            (
                "Unable to interpret changes between current project and cookiecutter template as "
                "unicode. Typically a result of hidden binary files in project folder."
            )
        )
